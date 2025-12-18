import os
import sys

# --- 1. CORRECTIF CLOUD (Obligatoire) ---
try:
    __import__('pysqlite3')
    sys.modules['sqlite3'] = sys.modules.pop('pysqlite3')
except ImportError:
    pass

import streamlit as st
import google.generativeai as genai
import chromadb
import time

# --- 2. CONFIGURATION DE LA PAGE ---
st.set_page_config(page_title="Expert RH & Social", page_icon="⚖️", layout="wide")
st.title("Assistant Expert Paie & Droit Social ⚖️")
st.caption("Accès Réservé - Base Documentaire 2025")

# --- 3. SÉCURITÉ (Mot de passe) ---
if "password_correct" not in st.session_state:
    st.session_state.password_correct = False

if not st.session_state.password_correct:
    with st.form("login_form"):
        st.write("🔒 **Identification Requise**")
        password_input = st.text_input("Mot de passe", type="password")
        submit_btn = st.form_submit_button("Entrer")
        
        if submit_btn:
            if password_input == "socialpro2026":
                st.session_state.password_correct = True
                st.rerun()
            else:
                st.error("❌ Accès refusé.")
    st.stop()

# --- 4. CONNEXION API (Simplifiée sans Sidebar) ---
api_key = None

# Tentative de récupération depuis les secrets (cas idéal)
try:
    if "GOOGLE_API_KEY" in st.secrets:
        api_key = st.secrets["GOOGLE_API_KEY"]
        # On n'affiche rien si ça marche, c'est transparent pour l'utilisateur
except:
    pass

# Si la clé n'est pas trouvée (ex: quelqu'un fork le projet), on demande poliment
if not api_key:
    with st.expander("⚙️ Configuration Technique (Clé API manquante)", expanded=True):
        st.warning("Aucune clé API trouvée dans les secrets.")
        api_key = st.text_input("Entrez votre clé API Google", type="password")

if api_key:
    genai.configure(api_key=api_key)
else:
    st.error("⚠️ Clé API requise pour démarrer.")
    st.stop()

# --- 5. LE CERVEAU (RAG) ---
@st.cache_resource(show_spinner=False)
def charger_cerveau():
    client = chromadb.Client()
    # On change le nom pour forcer la mise à jour avec le nouveau modèle
    nom_collection = "expert_rh_pro_v2" 

    try:
        client.delete_collection(nom_collection)
    except:
        pass
    
    collection = client.create_collection(nom_collection)

    # Lecture de tous les fichiers .txt (Documentation interne + Taux)
    fichiers_txt = [f for f in os.listdir('.') if f.endswith('.txt') and f != 'requirements.txt']
    
    if not fichiers_txt:
        return None

    docs_textes = []
    docs_ids = []
    compteur = 0
    
    for fichier in fichiers_txt:
        with open(fichier, "r", encoding="utf-8") as f:
            contenu = f.read()
        
        taille_bloc = 1500 # Blocs plus gros pour l'expert (plus de contexte)
        chevauchement = 200
        
        for i in range(0, len(contenu), taille_bloc - chevauchement):
            morceau = contenu[i : i + taille_bloc]
            if len(morceau.strip()) > 10:
                docs_textes.append(f"Source Documentaire [{fichier}] :\n{morceau}")
                docs_ids.append(f"doc_{compteur}")
                compteur += 1

    if not docs_textes:
        return None

    # Embedding
    embeddings = []
    barre = st.progress(0, text="Analyse de la documentation interne...")
    
    modele_embedding = "models/text-embedding-004"

    for i, doc in enumerate(docs_textes):
        try:
            res = genai.embed_content(model=modele_embedding, content=doc, task_type="retrieval_document")
            embeddings.append(res['embedding'])
            time.sleep(0.05) # Rapide car compte payant
        except:
            pass
        barre.progress(min((i + 1) / len(docs_textes), 1.0))
    
    barre.empty()
    
    if embeddings:
        collection.add(documents=docs_textes, ids=docs_ids, embeddings=embeddings)
        return collection
    return None

# --- 6. INTERFACE CHAT ---
with st.spinner("Initialisation de l'Expertise..."):
    db = charger_cerveau()

if db:
    st.success("✅ Système expert opérationnel.")
else:
    st.error("❌ Documentation introuvable (.txt).")

if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "assistant", "content": "Bonjour. Je suis prêt à analyser vos problématiques paie et droit social sur la base des textes 2025."}
    ]

for msg in st.session_state.messages:
    icone = "👔" if msg["role"] == "assistant" else "👤"
    st.chat_message(msg["role"], avatar=icone).write(msg["content"])

if question := st.chat_input("Posez votre cas pratique ou question juridique..."):
    st.session_state.messages.append({"role": "user", "content": question})
    st.chat_message("user", avatar="👤").write(question)

    if db:
        try:
            # 1. Recherche
            q_vec = genai.embed_content(model="models/text-embedding-004", content=question, task_type="retrieval_query")
            res = db.query(query_embeddings=[q_vec['embedding']], n_results=7) # Plus de sources pour l'expert
            
            if res['documents'] and res['documents'][0]:
                contexte = "\n\n".join(res['documents'][0])
                
                # 2. Prompt "Expert Senior" avec Source Unique imposée
                prompt_final = f"""Tu es un Expert RH et Paie Senior (Consultant).
                Ta mission : Fournir une analyse juridique précise et sourcée pour des professionnels.
                
                CONSIGNES STRICTES DE RÉDACTION :
                1. Base-toi EXCLUSIVEMENT sur le CONTEXTE fourni ci-dessous.
                2. SOURCE UNIQUE : Quelle que soit la partie du texte utilisée, tu dois citer ta source comme étant : "Mémento Social Editions Francis Lefebvre".
                3. INTERDICTION FORMELLE de mentionner les noms de fichiers techniques (ex: .txt, accidents_travail, etc.).
                4. Si l'information n'est pas dans le contexte, indique : "Cette précision ne figure pas dans les extraits du Mémento Social disponibles."
                
                CONTEXTE DOCUMENTAIRE (Extraits du Mémento Social Francis Lefebvre) :
                {contexte}
                
                QUESTION DU CLIENT : {question}"""

                # --- LE MOTEUR PRO (Stable & Rapide) ---
                # On utilise Gemini 2.0 Flash pour encaisser la charge sans erreur
                model = genai.GenerativeModel('models/gemini-2.0-flash')
                
                reponse = model.generate_content(prompt_final)
                
                st.chat_message("assistant", avatar="👔").write(reponse.text)
                st.session_state.messages.append({"role": "assistant", "content": reponse.text})
            else:
                st.warning("⚠️ Information absente de la base documentaire actuelle.")

        except Exception as e:
            st.error(f"Erreur système : {e}")
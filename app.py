import os
import sys

# --- 1. CORRECTIF POUR LE CLOUD (Pour éviter les erreurs SQLite) ---
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
st.set_page_config(page_title="Expert RH", page_icon="🧠", layout="wide")
st.title("Assistant expert Paie, Social & RH")
st.caption("Accès personnel Sécurisé")

# --- 3. SÉCURITÉ (Mot de passe) ---
# Si le mot de passe n'est pas bon, on arrête tout ici.
if "password_correct" not in st.session_state:
    st.session_state.password_correct = False

if not st.session_state.password_correct:
    # On utilise un formulaire pour éviter que ça tourne dans le vide
    with st.form("login_form"):
        st.write("🔒 **Veuillez vous identifier**")
        password_input = st.text_input("Mot de passe", type="password")
        submit_btn = st.form_submit_button("Valider")
        
        if submit_btn:
            if password_input == "socialpro2026":
                st.session_state.password_correct = True
                st.rerun() # On recharge proprement la page
            else:
                st.error("❌ Mot de passe incorrect")
    st.stop() # Arrêt du script si pas connecté

# --- 4. CONNEXION API GOOGLE (Une fois connecté) ---
with st.sidebar:
    st.header("🤖 Configuration")
    api_key = None
    
    # Tentative de récupération depuis les secrets
    try:
        if "GOOGLE_API_KEY" in st.secrets:
            api_key = st.secrets["GOOGLE_API_KEY"]
            st.success("Clé API connectée")
    except:
        pass

    # Si pas de secret, champ manuel
    if not api_key:
        api_key = st.text_input("Entrez votre clé API Google", type="password")
    
    if api_key:
        genai.configure(api_key=api_key)

if not api_key:
    st.warning("⚠️ Veuillez configurer la clé API dans la barre latérale pour continuer.")
    st.stop()

# --- 5. LE CERVEAU (Fonction de chargement des documents) ---
@st.cache_resource(show_spinner=False)
def charger_cerveau():
    client = chromadb.Client()
    nom_collection = "expert_rh_db_v3" # On change le nom pour forcer la mise à jour si besoin

    try:
        client.delete_collection(nom_collection)
    except:
        pass
    
    collection = client.create_collection(nom_collection)

    # Récupération des fichiers .txt
    fichiers_txt = [f for f in os.listdir('.') if f.endswith('.txt') and f != 'requirements.txt']
    
    if not fichiers_txt:
        return None

    docs_textes = []
    docs_ids = []
    compteur = 0
    
    # Découpage des fichiers
    for fichier in fichiers_txt:
        with open(fichier, "r", encoding="utf-8") as f:
            contenu = f.read()
        
        taille_bloc = 1500
        chevauchement = 200
        
        for i in range(0, len(contenu), taille_bloc - chevauchement):
            morceau = contenu[i : i + taille_bloc]
            docs_textes.append(f"Source: {fichier}\n\n{morceau}")
            docs_ids.append(f"doc_{compteur}")
            compteur += 1

    if not docs_textes:
        return None

    # Création des Embeddings (vectorisation)
    embeddings = []
    barre = st.progress(0, text="Lecture des documents juridiques...")
    
    for i, doc in enumerate(docs_textes):
        try:
            # On utilise le modèle d'embedding de Google
            res = genai.embed_content(model="models/text-embedding-004", content=doc, task_type="retrieval_document")
            embeddings.append(res['embedding'])
            time.sleep(0.5) # Petite pause pour éviter de saturer l'API
        except:
            pass
        barre.progress((i + 1) / len(docs_textes))
    
    barre.empty()
    
    if embeddings:
        collection.add(documents=docs_textes, ids=docs_ids, embeddings=embeddings)
        return collection
    return None

# --- 6. INTERFACE DE CHAT ---
if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "assistant", "content": "Bonjour ! Je suis l'assistant expert Paie, Social & RH. Posez-moi votre question."}
    ]

# Affichage de l'historique
for msg in st.session_state.messages:
    st.chat_message(msg["role"]).write(msg["content"])

# Chargement silencieux de la base de données
db = charger_cerveau()

# Zone de saisie utilisateur
if question := st.chat_input("Votre question juridique ou paie..."):
    # 1. On affiche la question
    st.session_state.messages.append({"role": "user", "content": question})
    st.chat_message("user").write(question)

    if not db:
        st.error("Je n'ai pas trouvé de documents (.txt) à lire. Vérifiez vos fichiers.")
        st.stop()

    # 2. Recherche dans la base (RAG)
    try:
        q_vec = genai.embed_content(model="models/text-embedding-004", content=question, task_type="retrieval_query")
        res = db.query(query_embeddings=[q_vec['embedding']], n_results=5)
        contexte = "\n\n".join(res['documents'][0])
        
        # 3. Génération de la réponse
        prompt_final = f"""Tu es un Expert RH et Paie Senior. Réponds à la question en utilisant le contexte fourni.
        Si la réponse n'est pas dans le contexte, dis-le clairement.
        Cite l'article ou la source si possible.
        
        CONTEXTE JURIDIQUE :
        {contexte}
        
        QUESTION : {question}"""

        model = genai.GenerativeModel('gemini-2.0-flash')
        reponse = model.generate_content(prompt_final)
        
        # 4. Affichage de la réponse
        st.chat_message("assistant").write(reponse.text)
        st.session_state.messages.append({"role": "assistant", "content": reponse.text})

    except Exception as e:
        st.error(f"Une erreur est survenue : {e}")
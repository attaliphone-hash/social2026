__import__('pysqlite3')
import sys
sys.modules['sqlite3'] = sys.modules.pop('pysqlite3')

import streamlit as st
import google.generativeai as genai
import chromadb
import os
import time

# --- CONFIGURATION ---
st.set_page_config(page_title="Expert RH", page_icon="🧠")
st.title("Assistant Paie, social & RH")
st.caption("Accès Sécurisé")

# --- 0. LE SAS D'ENTRÉE (Mot de passe) ---
# C'est ici que l'on bloque les intrus
if "password_verified" not in st.session_state:
    st.session_state.password_verified = False

def verifier_pass():
    if st.session_state["input_pass"] == "socialpro2026":
        st.session_state.password_verified = True
    else:
        st.session_state.password_verified = False

if not st.session_state.password_verified:
    st.text_input("🔒 Mot de passe d'accès", type="password", key="input_pass", on_change=verifier_pass)
    st.warning("Veuillez entrer le code d'accès pour voir la démo.")
    st.stop() # On arrête tout ici si le mot de passe est faux

# --- 1. SÉCURITÉ API & CONNEXION ---
with st.sidebar:
    st.header("🔐 Connexion")
    
    # On regarde d'abord dans le coffre-fort (Secrets) pour le "Zéro Clic"
    if "GOOGLE_API_KEY" in st.secrets:
        api_key = st.secrets["GOOGLE_API_KEY"]
        st.success("✅ Mode Démo Opérationnel")
    else:
        # Sinon, on demande à l'utilisateur
        api_key = st.text_input("Clé API Google", type="password")
    
    if api_key:
        genai.configure(api_key=api_key)

if not api_key:
    st.warning("⬅️ Clé API manquante (Ajoutez-la dans les Secrets ou ici).")
    st.stop()

# --- 2. FONCTION D'INDEXATION (Moteur 2025) ---
@st.cache_resource(show_spinner=False)
def charger_cerveau():
    client = chromadb.Client()
    try:
        client.delete_collection("paie")
    except:
        pass
    collection = client.create_collection("paie")

    # Recherche Multi-Fichiers (.txt)
    tous_les_fichiers = [f for f in os.listdir('.') if f.endswith('.txt') and f != 'requirements.txt']
    
    if not tous_les_fichiers:
        st.error("❌ Aucun fichier '.txt' trouvé.")
        return None

    docs_globaux = []
    ids_globaux = []
    compteur = 0
    
    # Lecture et découpage
    for fichier in tous_les_fichiers:
        with open(fichier, "r", encoding="utf-8") as f:
            contenu = f.read()
        
        taille_bloc = 1000
        chevauchement = 100
        
        for i in range(0, len(contenu), taille_bloc - chevauchement):
            morceau = contenu[i : i + taille_bloc]
            if len(morceau.strip()) > 10:
                docs_globaux.append(f"Source [{fichier}] : {morceau}")
                ids_globaux.append(f"doc_{compteur}")
                compteur += 1

    if not docs_globaux:
        st.error("❌ Fichiers vides.")
        return None

    # Vectorisation (Modèle embedding-004)
    embeddings = []
    total = len(docs_globaux)
    barre = st.progress(0, text=f"Chargement sécurisé de {total} extraits...")
    
    modele_embedding = "models/text-embedding-004"

    try:
        genai.embed_content(model=modele_embedding, content="Test", task_type="retrieval_document")
    except Exception as e:
        barre.empty()
        st.error(f"⛔️ ERREUR API : {e}")
        return None

    for i, doc in enumerate(docs_globaux):
        try:
            res = genai.embed_content(model=modele_embedding, content=doc, task_type="retrieval_document")
            embeddings.append(res['embedding'])
            time.sleep(1.0) # Pause sécurité quota
        except Exception as e:
            break
        
        if total > 0:
            barre.progress(min((i + 1) / total, 1.0))
    
    barre.empty()
    
    if len(embeddings) > 0:
        taille = len(embeddings)
        collection.add(documents=docs_globaux[:taille], ids=ids_globaux[:taille], embeddings=embeddings[:taille])
        return collection
            
    return None

# --- 3. DÉMARRAGE ---
with st.spinner("Démarrage du système..."):
    db = charger_cerveau()

if db:
    st.success("✅ Système prêt !")

    # --- 4. CHAT (Moteur Gemini 2.5) ---
    if "messages" not in st.session_state:
        st.session_state.messages = [{"role": "assistant", "content": "Bonjour ! Je suis prêt, vous pouvez poser votre question."}]

    for msg in st.session_state.messages:
        st.chat_message(msg["role"]).write(msg["content"])

    if question := st.chat_input("Votre question..."):
        st.session_state.messages.append({"role": "user", "content": question})
        st.chat_message("user").write(question)

        try:
            q_vec = genai.embed_content(model="models/text-embedding-004", content=question, task_type="retrieval_query")
            res = db.query(query_embeddings=[q_vec['embedding']], n_results=5)
            
            if res['documents'] and res['documents'][0]:
                contexte = "\n\n".join(res['documents'][0])
                prompt = f"Expert RH. Réponds UNIQUEMENT via ce contexte.\nCONTEXTE: {contexte}\nQUESTION: {question}"
                
                # Le modèle Chat à jour (2.5)
                model = genai.GenerativeModel('gemini-2.5-flash') 
                reponse = model.generate_content(prompt)
                
                st.chat_message("assistant").write(reponse.text)
                st.session_state.messages.append({"role": "assistant", "content": reponse.text})
            else:
                st.warning("Je n'ai pas la réponse dans les documents.")
        except Exception as e:
            st.error(f"Erreur : {e}")

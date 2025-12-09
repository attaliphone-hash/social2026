__import__('pysqlite3')
import sys
sys.modules['sqlite3'] = sys.modules.pop('pysqlite3')

import streamlit as st
import google.generativeai as genai
import chromadb
import os

st.set_page_config(page_title="Payroll Bot", page_icon="⚖️")
st.title("Assistant Paie & RH 🧠")

# --- SECURITE ---
with st.sidebar:
    st.header("🔐 Connexion")
    api_key = st.text_input("Clé API Google", type="password")
    if api_key:
        genai.configure(api_key=api_key)

if not api_key:
    st.warning("⬅️ Veuillez entrer votre clé API.")
    st.stop()

# --- CERVEAU ---
@st.cache_resource(show_spinner=False)
def get_db():
    client = chromadb.Client()
    try:
        client.delete_collection("paie")
    except:
        pass
    collection = client.create_collection("paie")

    # Recherche du fichier (racine ou dossier documents)
    fichiers = ["accidents du travail.txt", "documents/accidents du travail.txt"]
    fichier_trouve = None
    for f in fichiers:
        if os.path.exists(f):
            fichier_trouve = f
            break
            
    if not fichier_trouve:
        st.error("Fichier introuvable.")
        return None

    with open(fichier_trouve, "r", encoding="utf-8") as f:
        contenu = f.read()

    # --- ASTUCE ANTI-COPIE ---
    # On utilise le code 91 pour le crochet [
    balise = chr(91) + "source:"
    parts = contenu.split(balise)
    # -----------------------

    docs = []
    ids = []
    
    barre = st.progress(0, text="Analyse du Mémento...")
    total = len(parts)

    for i, part in enumerate(parts):
        if "]" in part:
            try:
                morceaux = part.split("]", 1)
                source_id = morceaux[0]
                texte = morceaux[1].strip()
                if len(texte) > 10:
                    docs.append(f"Source {source_id}: {texte}")
                    ids.append(f"doc_{i}")
            except:
                pass
        if total > 0 and i % 10 == 0:
            barre.progress(min(i / total, 1.0))
    
    barre.empty()

    if docs:
        embeddings = []
        for doc in docs:
            try:
                res = genai.embed_content(model="models/embedding-001", content=doc, task_type="retrieval_document")
                embeddings.append(res['embedding'])
            except:
                pass
        
        if len(embeddings) > 0:
            collection.add(documents=docs, ids=ids, embeddings=embeddings)
            return collection
    return None

# --- INTERFACE ---
with st.spinner("Démarrage..."):
    db = get_db()

if db:
    st.success("✅ Système prêt !")

    if "messages" not in st.session_state:
        st.session_state.messages = [{"role": "assistant", "content": "Bonjour ! Je suis votre expert RH."}]

    for msg in st.session_state.messages:
        st.chat_message(msg["role"]).write(msg["content"])

    if question := st.chat_input("Votre question..."):
        st.session_state.messages.append({"role": "user", "content": question})
        st.chat_message("user").write(question)

        try:
            q_embed = genai.embed_content(model="models/embedding-001", content=question, task_type="retrieval_query")
            res = db.query(query_embeddings=[q_embed['embedding']], n_results=3)
            contexte = "\n\n".join(res['documents'][0])
            
            prompt = f"Expert RH. Contexte: {contexte}\nQuestion: {question}"
            model = genai.GenerativeModel('gemini-1.5-flash')
            reponse = model.generate_content(prompt)
            
            st.chat_message("assistant").write(reponse.text)
            st.session_state.messages.append({"role": "assistant", "content": reponse.text})
        except Exception as e:
            st.error(f"Erreur : {e}")

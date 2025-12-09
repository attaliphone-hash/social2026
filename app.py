__import__('pysqlite3')
import sys
sys.modules['sqlite3'] = sys.modules.pop('pysqlite3')

import streamlit as st
import google.generativeai as genai
import chromadb
import os

# --- CONFIGURATION ---
st.set_page_config(page_title="Payroll Bot", page_icon="⚖️")
st.title("French Payroll Expert - Assistant IA 🧠")

# --- BARRE LATÉRALE ---
with st.sidebar:
    st.header("🔐 Configuration")
    api_key = st.text_input("Clé API Google", type="password")
    if api_key:
        genai.configure(api_key=api_key)

if not api_key:
    st.warning("⬅️ Entrez votre clé API à gauche pour démarrer.")
    st.stop()

# --- FONCTION D'INDEXATION ---
@st.cache_resource(show_spinner=False)
def get_vector_db():
    # 1. Création de la DB
    client = chromadb.Client()
    try:
        client.delete_collection("payroll")
    except:
        pass
    collection = client.create_collection("payroll")

    # 2. Lecture du fichier
    filename = "accidents du travail.txt"
    if not os.path.exists(filename):
        st.error(f"❌ ERREUR : Le fichier '{filename}' est introuvable sur le serveur.")
        return None

    with open(filename, "r", encoding="utf-8") as f:
        text = f.read()

    # 3. Découpage
    parts = text.split("
    ids = []
    
    # Barre de progression
    my_bar = st.progress(0, text="Lecture du Mémento...")
    total = len(parts)

    for i, part in enumerate(parts):
        if "]" in part:
            source_id, content = part.split("]", 1)
            content = content.strip()
            if len(content) > 20:
                documents.append(f"Source {source_id}: {content}")
                ids.append(f"doc_{i}")
        
        if i % 10 == 0:
            my_bar.progress(min(i / total, 1.0))

    my_bar.empty()

    # 4. Vectorisation (Batch)
    if documents:
        # On utilise une fonction d'embedding simple pour éviter les erreurs de boucle
        collection.add(
            documents=documents,
            ids=ids,
            embeddings=[genai.embed_content(model="models/embedding-001", content=d, task_type="retrieval_document")['embedding'] for d in documents]
        )
        return collection
    else:
        st.error("Le fichier semble vide.")
        return None

# --- LANCEMENT ---
with st.spinner("Chargement de l'intelligence artificielle..."):
    db = get_vector_db()

if db:
    st.success("✅ Système opérationnel !")

    # --- CHATBOT ---
    if "messages" not in st.session_state:
        st.session_state.messages = [{"role": "assistant", "content": "Bonjour ! Je suis prêt à analyser vos questions juridiques."}]

    for msg in st.session_state.messages:
        st.chat_message(msg["role"]).write(msg["content"])

    if user_query := st.chat_input("Votre question..."):
        st.session_state.messages.append({"role": "user", "content": user_query})
        st.chat_message("user").write(user_query)

        # 1. Vectorisation de la question
        q_embed = genai.embed_content(model="models/embedding-001", content=user_query, task_type="retrieval_query")
        
        # 2. Recherche des 3 meilleurs paragraphes
        results = db.query(query_embeddings=[q_embed['embedding']], n_results=3)
        context_text = "\n\n".join(results['documents'][0])

        # 3. Génération de la réponse
        prompt = f"""Tu es un expert en Droit Social. 
        Réponds à la question en utilisant UNIQUEMENT le contexte suivant. 
        Cite les sources (ex: Source 12).
        
        CONTEXTE : {context_text}
        
        QUESTION : {user_query}"""

        model = genai.GenerativeModel('gemini-1.5-flash')
        response = model.generate_content(prompt)
        
        st.chat_message("assistant").write(response.text)
        st.session_state.messages.append({"role": "assistant", "content": response.text})

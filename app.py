__import__('pysqlite3')
import sys
sys.modules['sqlite3'] = sys.modules.pop('pysqlite3')

import streamlit as st
import google.generativeai as genai
import chromadb
import os

st.set_page_config(page_title="Expert RH", page_icon="🧠")
st.title("Assistant Paie & RH 🧠")

# --- 1. CONNEXION ---
with st.sidebar:
    st.header("🔐 Connexion")
    api_key = st.text_input("Clé API Google", type="password")
    if api_key:
        genai.configure(api_key=api_key)

if not api_key:
    st.warning("⬅️ Veuillez entrer votre clé API.")
    st.stop()

# --- 2. CERVEAU (Universel) ---
@st.cache_resource(show_spinner=False)
def charger_cerveau():
    client = chromadb.Client()
    try:
        client.delete_collection("paie")
    except:
        pass
    collection = client.create_collection("paie")

    # Nom du fichier confirmé
    fichier = "accidents-du-travail.txt"
    
    if not os.path.exists(fichier):
        return "INTROUVABLE"

    with open(fichier, "r", encoding="utf-8") as f:
        contenu = f.read()

    # --- NOUVEAU DECOUPAGE (PARAGRAPHES) ---
    # On coupe à chaque double saut de ligne (paragraphe naturel)
    # Plus besoin de balises 
    parts = contenu.split("\n\n")
    
    docs = []
    ids = []
    
    barre = st.progress(0, text="Lecture du fichier...")
    total = len(parts)

    for i, part in enumerate(parts):
        texte = part.strip()
        # On garde les paragraphes qui ont du sens (+ de 50 caractères)
        if len(texte) > 50:
            # On crée une référence automatique "Paragraphe X"
            docs.append(f"Extrait {i+1}: {texte}")
            ids.append(f"doc_{i}")
        
        if total > 0 and i % 10 == 0:
            barre.progress(min(i / total, 1.0))
    
    barre.empty()

    if not docs:
        return "VIDE"

    # Vectorisation
    embeddings = []
    for doc in docs:
        try:
            res = genai.embed_content(model="models/embedding-001", content=doc, task_type="retrieval_document")
            embeddings.append(res['embedding'])
        except:
            pass
    
    if len(embeddings) > 0:
        taille = min(len(docs), len(embeddings))
        collection.add(
            documents=docs[:taille], 
            ids=ids[:taille], 
            embeddings=embeddings[:taille]
        )
        return collection
            
    return "VIDE"

# --- 3. LANCEMENT ---
with st.spinner("Analyse du document..."):
    db = charger_cerveau()

if db == "INTROUVABLE":
    st.error("❌ Le fichier 'accidents-du-travail.txt' est introuvable.")
elif db == "VIDE":
    st.error("❌ Le fichier est lu mais semble vide (pas assez de texte).")
elif db:
    st.success("✅ Mémento chargé avec succès !")

    if "messages" not in st.session_state:
        st.session_state.messages = [{"role": "assistant", "content": "Bonjour ! Je suis prêt."}]

    for msg in st.session_state.messages:
        st.chat_message(msg["role"]).write(msg["content"])

    if question := st.chat_input("Votre question..."):
        st.session_state.messages.append({"role": "user", "content": question})
        st.chat_message("user").write(question)

        try:
            q_vec = genai.embed_content(model="models/embedding-001", content=question, task_type="retrieval_query")
            res = db.query(query_embeddings=[q_vec['embedding']], n_results=3)
            
            if res['documents'] and res['documents'][0]:
                contexte = "\n\n".join(res['documents'][0])
                prompt = f"Expert RH. Utilise ce contexte pour répondre.\nCONTEXTE: {contexte}\nQUESTION: {question}"
                model = genai.GenerativeModel('gemini-1.5-flash')
                reponse = model.generate_content(prompt)
                
                st.chat_message("assistant").write(reponse.text)
                st.session_state.messages.append({"role": "assistant", "content": reponse.text})
            else:
                st.warning("Je ne trouve pas d'info pertinente.")
        except Exception as e:
            st.error(f"Erreur : {e}")

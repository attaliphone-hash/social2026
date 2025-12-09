__import__('pysqlite3')
import sys
sys.modules['sqlite3'] = sys.modules.pop('pysqlite3')

import streamlit as st
import google.generativeai as genai
import chromadb
import os

# --- 1. CONFIGURATION ---
st.set_page_config(page_title="Payroll Bot", page_icon="⚖️")
st.title("Assistant Paie & RH 🧠")

# --- 2. SECURITE ---
with st.sidebar:
    st.header("🔐 Connexion")
    api_key = st.text_input("Clé API Google", type="password")
    if api_key:
        genai.configure(api_key=api_key)

if not api_key:
    st.warning("⬅️ Veuillez entrer votre clé API.")
    st.stop()

# --- 3. CERVEAU (BASE DE DONNEES) ---
@st.cache_resource(show_spinner=False)
def get_db():
    client = chromadb.Client()
    try:
        client.delete_collection("paie")
    except:
        pass
    collection = client.create_collection("paie")

    # Lecture du fichier
    fichier = "accidents du travail.txt"
    if not os.path.exists(fichier):
        st.error(f"Erreur: {fichier} introuvable.")
        return None

    with open(fichier, "r", encoding="utf-8") as f:
        contenu = f.read()

    # Découpage sécurisé pour éviter l'erreur de copie
    partie_1 = "["
    partie_2 = "source:"
    balise = partie_1 + partie_2
    parts = contenu.split(balise)

    docs = []
    ids = []
    
    # Barre de chargement
    barre = st.progress(0, text="Analyse du Mémento...")
    total = len(parts)

    for i, part in enumerate(parts):
        if "]" in part:
            try:
                # On sépare l'ID du texte
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
        # On insère dans la base vectorielle
        embeddings = []
        for doc in docs:
            # Appel API Google pour chaque paragraphe
            try:
                res = genai.embed_content(model="models/embedding-001", content=doc, task_type="retrieval_document")
                embeddings.append(res['embedding'])
            except:
                pass 
        
        # Vérification des tailles avant ajout
        if len(docs) == len(embeddings):
            collection.add(documents=docs, ids=ids, embeddings=embeddings)
            return collection
        else:
            return None
    else:
        return None

# --- 4. INTERFACE ---
with st.spinner("Démarrage du système..."):
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

        # Recherche
        q_embed = genai.embed_content(model="models/embedding-001", content=question, task_type="retrieval_query")
        res = db.query(query_embeddings=[q_embed['embedding']], n_results=3)
        
        contexte = "\n\n".join(res['documents'][0])

        # Réponse
        prompt = f"Expert RH. Utilise ce contexte pour répondre.\nCONTEXTE: {contexte}\nQUESTION: {question}"
        
        model = genai.GenerativeModel('gemini-1.5-flash')
        reponse = model.generate_content(prompt)
        
        st.chat_message("assistant").write(reponse.text)
        st.session_state.messages.append({"role": "assistant", "content": reponse.text})

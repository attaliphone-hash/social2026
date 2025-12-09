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

# --- 2. CERVEAU (Mode "Chunking" Robuste) ---
@st.cache_resource(show_spinner=False)
def charger_cerveau():
    client = chromadb.Client()
    try:
        client.delete_collection("paie")
    except:
        pass
    collection = client.create_collection("paie")

    fichier = "accidents-du-travail.txt"
    
    if not os.path.exists(fichier):
        return "INTROUVABLE"

    with open(fichier, "r", encoding="utf-8") as f:
        contenu = f.read()

    # --- DÉCOUPAGE MATHÉMATIQUE (Chunking) ---
    # On ne cherche plus les paragraphes. On coupe tous les 1000 caractères.
    # C'est impossible à rater.
    taille_bloc = 1000
    chevauchement = 100 # On garde un peu de contexte entre chaque bloc
    
    docs = []
    ids = []
    
    # Boucle mathématique sur le texte
    for i in range(0, len(contenu), taille_bloc - chevauchement):
        morceau = contenu[i : i + taille_bloc]
        
        # Si le morceau contient du texte (plus de 10 lettres)
        if len(morceau.strip()) > 10:
            docs.append(f"Extrait {i//taille_bloc + 1}: {morceau}")
            ids.append(f"doc_{i}")

    if not docs:
        return "VIDE"

    # Vectorisation
    embeddings = []
    barre = st.progress(0, text="Mémorisation des blocs...")
    total = len(docs)

    for i, doc in enumerate(docs):
        try:
            res = genai.embed_content(model="models/embedding-001", content=doc, task_type="retrieval_document")
            embeddings.append(res['embedding'])
        except:
            pass
        
        if total > 0 and i % 5 == 0:
            barre.progress(min(i / total, 1.0))
    
    barre.empty()
    
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
    st.error("❌ Fichier 'accidents-du-travail.txt' introuvable.")
elif db == "VIDE":
    st.error("❌ Le fichier est lu mais semble totalement vide.")
elif db:
    st.success("✅ Mémento chargé ! (Mode Chunking activé)")

    # --- 4. CHAT ---
    if "messages" not in st.session_state:
        st.session_state.messages = [{"role": "assistant", "content": "Bonjour ! Posez votre question."}]

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
                st.warning("Je n'ai rien trouvé de pertinent.")
        except Exception as e:
            st.error(f"Erreur : {e}")

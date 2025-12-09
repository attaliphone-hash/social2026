__import__('pysqlite3')
import sys
sys.modules['sqlite3'] = sys.modules.pop('pysqlite3')

import streamlit as st
import google.generativeai as genai
import chromadb
import os

# --- CONFIGURATION DE LA PAGE ---
st.set_page_config(page_title="Payroll Bot", page_icon="⚖️")
st.title("French Payroll Expert - Assistant IA 🧠")

# --- BARRE LATÉRALE (API KEY) ---
with st.sidebar:
    st.header("🔐 Configuration")
    api_key = st.text_input("Clé API Google", type="password")
    if api_key:
        genai.configure(api_key=api_key)

if not api_key:
    st.warning("⬅️ Entrez votre clé API à gauche pour démarrer.")
    st.stop()

# --- FONCTION D'INDEXATION (CACHE) ---
@st.cache_resource(show_spinner=False)
def get_vector_db():
    # 1. Création de la DB Chroma en mémoire
    client = chromadb.Client()
    try:
        client.delete_collection("payroll")
    except:
        pass
    collection = client.create_collection("payroll")

    # 2. Lecture du fichier texte
    # On cherche le fichier à la racine
    filename = "accidents du travail.txt"
    
    if not os.path.exists(filename):
        st.error(f"❌ ERREUR : Le fichier '{filename}' est introuvable sur le serveur.")
        return None

    with open(filename, "r", encoding="utf-8") as f:
        text = f.read()

    # 3. Découpage du texte
    # C'est ici que ça avait coupé avant. Voici la version corrigée :
    parts = text.split("
    ids = []
    
    # Barre de progression
    my_bar = st.progress(0, text="Lecture du Mémento en cours...")
    total = len(parts)

    # 4. Boucle de traitement
    for i, part in enumerate(parts):
        # On vérifie si le morceau contient le crochet fermant
        if "]" in part:
            try:
                source_id, content = part.split("]", 1)
                content = content.strip()
                # On garde seulement les paragraphes significatifs
                if len(content) > 20:
                    documents.append(f"Source {source_id}: {content}")
                    ids.append(f"doc_{i}")
            except:
                continue
        
        # Mise à jour barre progression (pour éviter de ralentir)
        if total > 0 and i % 10 == 0:
            my_bar.progress(min(i / total, 1.0))

    my_bar.empty()

    # 5. Vectorisation et Stockage (Batch)
    if documents:
        # Création des embeddings via Google
        # On utilise une compréhension de liste simple pour éviter les erreurs d'indentation
        embeddings = [
            genai.embed_content(
                model="models/embedding-001",
                content=d,
                task_type="retrieval_document"
            )['embedding'] 
            for d in documents
        ]
        
        # Ajout dans ChromaDB
        collection.add(
            documents=documents,
            ids=ids,
            embeddings=embeddings
        )
        return collection
    else:
        st.error("Le fichier semble vide ou mal formaté.")
        return None

# --- LANCEMENT DE L'APP ---
with st.spinner("Chargement de l'intelligence artificielle..."):
    db = get_vector_db()

if db:
    st.success("✅ Système opérationnel !")

    # --- ZONE DE CHAT ---
    if "messages" not in st.session_state:
        st.session_state.messages = [{"role": "assistant", "content": "Bonjour ! Je suis prêt à analyser vos questions juridiques."}]

    for msg in st.session_state.messages:
        st.chat_message(msg["role"]).write(msg["content"])

    if user_query := st.chat_input("Votre question..."):
        st.session_state.messages.append({"role": "user", "content": user_query})
        st.chat_message("user").write(user_query)

        # 1. Vectorisation de la question
        q_embed = genai.embed_content(
            model="models/embedding-001",
            content=user_query,
            task_type="retrieval_query"
        )
        
        # 2. Recherche des 3 meilleurs paragraphes
        results = db.query(
            query_embeddings=[q_embed['embedding']],
            n_results=3
        )
        
        # 3. Préparation du contexte pour l'IA
        context_text = "\n\n".join(results['documents'][0])

        # 4. Génération de la réponse
        prompt = f"""Tu es un expert en Droit Social. 
        Réponds à la question en utilisant UNIQUEMENT le contexte suivant. 
        Cite les sources (ex: Source 12).
        
        CONTEXTE : {context_text}
        
        QUESTION : {user_query}"""

        model = genai.GenerativeModel('gemini-1.5-flash')
        response = model.generate_content(prompt)
        
        st.chat_message("assistant").write(response.text)
        st.session_state.messages.append({"role": "assistant", "content": response.text})

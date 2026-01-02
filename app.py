# --- 1. CONFIGURATION SQLITE (CRITIQUE POUR CHROMADB SUR CLOUD RUN) ---
import sys
import os

try:
    __import__('pysqlite3')
    sys.modules['sqlite3'] = sys.modules.pop('pysqlite3')
except ImportError:
    pass

import streamlit as st

# --- 2. IMPORTS DES MODULES (CONTOURNEMENT DU BUG LANGCHAIN) ---
try:
    # Imports de base pour l'IA et la base de données
    from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAIEmbeddings
    from langchain_chroma import Chroma
    from langchain_core.prompts import ChatPromptTemplate
    
    # Correction spécifique : on force le chargement du module parent
    import langchain.chains
    from langchain.chains.retrieval import create_retrieval_chain
    from langchain.chains.combine_documents import create_stuff_documents_chain
    
except ModuleNotFoundError as e:
    st.error(f"⚠️ Erreur de module persistante : {e}")
    st.stop()

# --- 3. CONFIGURATION INTERFACE ET CLÉ API ---
# Utilisation de la clé "Clé Gemini - Assistants" (Consigne du 01-01-26)
os.environ["GOOGLE_API_KEY"] = st.secrets["GEMINI_API_KEY"]

st.set_page_config(page_title="Expert Social Pro 2026", layout="wide")
st.title("🤖 Expert Social Pro 2026")

# --- 4. CHARGEMENT DU SYSTÈME RAG ---
@st.cache_resource
def load_system():
    # Embeddings (modèle stable text-embedding-004)
    embeddings = GoogleGenerativeAIEmbeddings(model="models/text-embedding-004")
    
    # Dossier de la base (Golden Index téléchargé via Dockerfile)
    persist_directory = "chroma_db"
    
    vectorstore = Chroma(
        persist_directory=persist_directory,
        embedding_function=embeddings
    )
    
    # Utilisation obligatoire de gemini-2.0-flash-exp (Consigne du 17-12-25)
    llm = ChatGoogleGenerativeAI(
        model="gemini-2.0-flash-exp",
        temperature=0,
    )
    
    return vectorstore, llm

vectorstore, llm = load_system()

# --- 5. CONFIGURATION DU PROMPT ---
system_prompt = (
    "Tu es un assistant expert en droit social français. "
    "Réponds aux questions en utilisant le contexte fourni. "
    "Cite tes sources de manière précise (BOSS, Code du travail). "
    "\n\n"
    "{context}"
)

prompt = ChatPromptTemplate.from_messages([
    ("system", system_prompt),
    ("human", "{input}"),
])

# Création des chaînes de traitement
question_answer_chain = create_stuff_documents_chain(llm, prompt)
rag_chain = create_retrieval_chain(vectorstore.as_retriever(), question_answer_chain)

# --- 6. GESTION DU CHAT ---
if "messages" not in st.session_state:
    st.session_state.messages = []

# Affichage de l'historique des messages
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Entrée utilisateur et réponse de l'IA
if query := st.chat_input("Posez votre question juridique..."):
    st.session_state.messages.append({"role": "user", "content": query})
    with st.chat_message("user"):
        st.markdown(query)

    with st.chat_message("assistant"):
        with st.spinner("Analyse des sources officielles..."):
            try:
                response = rag_chain.invoke({"input": query})
                answer = response["answer"]
                st.markdown(answer)
                st.session_state.messages.append({"role": "assistant", "content": answer})
            except Exception as e:
                st.error(f"Erreur lors de la génération : {e}")
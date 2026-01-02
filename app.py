# --- 1. CONFIGURATION DES CHEMINS ET SQLITE (CRITIQUE) ---
import sys
import os
import subprocess

# Détection dynamique du dossier des paquets pour forcer le chemin
try:
    python_version = f"{sys.version_info.major}.{sys.version_info.minor}"
    paths_to_check = [
        f"/usr/local/lib/python{python_version}/site-packages",
        os.path.expanduser(f"~/.local/lib/python{python_version}/site-packages")
    ]
    for p in paths_to_check:
        if p not in sys.path:
            sys.path.insert(0, p)
except Exception:
    pass

# Correctif SQLite pour Chromadb
try:
    __import__('pysqlite3')
    sys.modules['sqlite3'] = sys.modules.pop('pysqlite3')
except ImportError:
    pass

# --- 2. IMPORTS DES MODULES ---
import streamlit as st
# Importation sécurisée
try:
    from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAIEmbeddings
    from langchain_chroma import Chroma
    from langchain.chains.retrieval import create_retrieval_chain
    from langchain.chains.combine_documents import create_stuff_documents_chain
    from langchain_core.prompts import ChatPromptTemplate
except ModuleNotFoundError as e:
    st.error(f"Erreur fatale d'importation : {e}")
    st.info(f"Chemins consultés par Python : {sys.path}")
    st.stop()

# --- 3. CONFIGURATION INTERFACE ET CLÉ API ---
os.environ["GOOGLE_API_KEY"] = st.secrets["GEMINI_API_KEY"]

st.set_page_config(page_title="Expert Social Pro 2026", layout="wide")
st.title("🤖 Expert Social Pro 2026")

# --- 4. CHARGEMENT DU SYSTÈME RAG ---
@st.cache_resource
def load_system():
    embeddings = GoogleGenerativeAIEmbeddings(model="models/text-embedding-004")
    persist_directory = "chroma_db"
    
    vectorstore = Chroma(
        persist_directory=persist_directory,
        embedding_function=embeddings
    )
    
    # Utilisation de gemini-2.0-flash-exp (référence 17-12)
    llm = ChatGoogleGenerativeAI(
        model="gemini-2.0-flash-exp",
        temperature=0,
    )
    return vectorstore, llm

vectorstore, llm = load_system()

# --- 5. CONFIGURATION DU PROMPT ---
system_prompt = (
    "Tu es un assistant expert en droit social français. "
    "Réponds en utilisant les extraits fournis. Cite tes sources. "
    "\n\nContext: {context}"
)

prompt = ChatPromptTemplate.from_messages([
    ("system", system_prompt),
    ("human", "{input}"),
])

question_answer_chain = create_stuff_documents_chain(llm, prompt)
rag_chain = create_retrieval_chain(vectorstore.as_retriever(), question_answer_chain)

# --- 6. GESTION DU CHAT ---
if "messages" not in st.session_state:
    st.session_state.messages = []

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

if query := st.chat_input("Posez votre question juridique..."):
    st.session_state.messages.append({"role": "user", "content": query})
    with st.chat_message("user"):
        st.markdown(query)

    with st.chat_message("assistant"):
        with st.spinner("Analyse..."):
            response = rag_chain.invoke({"input": query})
            answer = response["answer"]
            st.markdown(answer)
            st.session_state.messages.append({"role": "assistant", "content": answer})
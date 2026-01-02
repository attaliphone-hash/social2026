# --- 1. CONFIGURATION DES CHEMINS ET SQLITE (CRITIQUE) ---
import sys
import os

# Correctif SQLite pour Chromadb (doit être fait AVANT les imports langchain)
try:
    __import__('pysqlite3')
    sys.modules['sqlite3'] = sys.modules.pop('pysqlite3')
except ImportError:
    pass

# Force Python à scanner les répertoires de paquets Linux
for p in ['/usr/local/lib/python3.10/site-packages', '/root/.local/lib/python3.10/site-packages']:
    if p not in sys.path:
        sys.path.insert(0, p)

# --- 2. IMPORTS DES MODULES (VERSION CORRIGÉE) ---
import streamlit as st
try:
    from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAIEmbeddings
    from langchain_chroma import Chroma
    # Utilisation des chemins d'importation les plus robustes
    from langchain.chains import create_retrieval_chain
    from langchain.chains.combine_documents import create_stuff_documents_chain
    from langchain_core.prompts import ChatPromptTemplate
except ModuleNotFoundError as e:
    st.error(f"⚠️ Erreur de module : {e}")
    st.info(f"Chemins fouillés par l'IA : {sys.path}")
    st.stop()

# --- 3. CONFIGURATION INTERFACE ET CLÉ API ---
# On récupère la clé enregistrée sous le nom "Clé Gemini - Assistants"
os.environ["GOOGLE_API_KEY"] = st.secrets["GEMINI_API_KEY"]

st.set_page_config(page_title="Expert Social Pro 2026", layout="wide")
st.title("🤖 Expert Social Pro 2026")

# --- 4. CHARGEMENT DU SYSTÈME RAG ---
@st.cache_resource
def load_system():
    # Embeddings (modèle 004 stable)
    embeddings = GoogleGenerativeAIEmbeddings(model="models/text-embedding-004")
    
    # Dossier de la base téléchargé par le Dockerfile
    persist_directory = "chroma_db"
    
    vectorstore = Chroma(
        persist_directory=persist_directory,
        embedding_function=embeddings
    )
    
    # Configuration Gemini 2.0 Flash (Consigne du 17-12)
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
    "Si tu ne sais pas, dis-le. Cite tes sources (BOSS, Code du Travail)."
    "\n\n"
    "{context}"
)

prompt = ChatPromptTemplate.from_messages([
    ("system", system_prompt),
    ("human", "{input}"),
])

# Assemblage des chaînes
question_answer_chain = create_stuff_documents_chain(llm, prompt)
rag_chain = create_retrieval_chain(vectorstore.as_retriever(), question_answer_chain)

# --- 6. INTERFACE DE CHAT ---
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
        with st.spinner("Analyse des sources officielles..."):
            response = rag_chain.invoke({"input": query})
            answer = response["answer"]
            st.markdown(answer)
            st.session_state.messages.append({"role": "assistant", "content": answer})
# --- 1. CONFIGURATION SQLITE ---
import sys
import os

__import__('pysqlite3')
sys.modules['sqlite3'] = sys.modules.pop('pysqlite3')

import streamlit as st

# --- 2. IMPORTS DES MODULES (SANS PASSER PAR LANGCHAIN.CHAINS) ---
try:
    from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAIEmbeddings
    from langchain_chroma import Chroma
    from langchain_core.prompts import ChatPromptTemplate
    
    # Imports directs depuis les paquets sources pour éviter le ModuleNotFoundError
    from langchain.chains.retrieval import create_retrieval_chain
    from langchain.chains.combine_documents import create_stuff_documents_chain
    
except ModuleNotFoundError as e:
    # Si ça échoue encore, on utilise une méthode d'importation encore plus profonde
    st.error(f"⚠️ Erreur persistante : {e}")
    st.info("Tentative de contournement en cours...")
    st.stop()

# --- 3. CONFIGURATION INTERFACE ET CLÉ API ---
os.environ["GOOGLE_API_KEY"] = st.secrets["GEMINI_API_KEY"]

st.set_page_config(page_title="Expert Social Pro 2026", layout="wide")
st.title("🤖 Expert Social Pro 2026")

# --- 4. CHARGEMENT DU SYSTÈME RAG ---
@st.cache_resource
def load_system():
    embeddings = GoogleGenerativeAIEmbeddings(model="models/text-embedding-004")
    vectorstore = Chroma(persist_directory="chroma_db", embedding_function=embeddings)
    
    # Gemini 2.0 Flash (Consigne du 17-12)
    llm = ChatGoogleGenerativeAI(model="gemini-2.0-flash-exp", temperature=0)
    return vectorstore, llm

vectorstore, llm = load_system()

# --- 5. CONFIGURATION DU PROMPT ---
system_prompt = (
    "Tu es un assistant expert en droit social français. "
    "Réponds en utilisant le contexte fourni. Cite tes sources."
    "\n\n{context}"
)

prompt = ChatPromptTemplate.from_messages([
    ("system", system_prompt),
    ("human", "{input}"),
])

# Assemblage manuel pour éviter les fonctions de haut niveau qui plantent
question_answer_chain = create_stuff_documents_chain(llm, prompt)
rag_chain = create_retrieval_chain(vectorstore.as_retriever(), question_answer_chain)

# --- 6. INTERFACE DE CHAT ---
if "messages" not in st.session_state:
    st.session_state.messages = []

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

if query := st.chat_input("Posez votre question..."):
    st.session_state.messages.append({"role": "user", "content": query})
    with st.chat_message("user"):
        st.markdown(query)

    with st.chat_message("assistant"):
        with st.spinner("Analyse..."):
            response = rag_chain.invoke({"input": query})
            st.markdown(response["answer"])
            st.session_state.messages.append({"role": "assistant", "content": response["answer"]})
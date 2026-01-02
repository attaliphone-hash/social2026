# --- 1. CORRECTIF CRITIQUE POUR SQLITE SUR GOOGLE CLOUD ---
# Ces 3 lignes doivent rester TOUT EN HAUT avant tout autre import
__import__('pysqlite3')
import sys
sys.modules['sqlite3'] = sys.modules.pop('pysqlite3')

import streamlit as st
import os
from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAIEmbeddings
from langchain_chroma import Chroma
from langchain.chains import create_retrieval_chain
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain_core.prompts import ChatPromptTemplate

# --- 2. CONFIGURATION ---
# Utilisation de votre clé API "Clé Gemini - Assistants"
os.environ["GOOGLE_API_KEY"] = st.secrets["GEMINI_API_KEY"]

st.set_page_config(page_title="Expert Social Pro 2026", layout="wide")
st.title("🤖 Expert Social Pro 2026")

# --- 3. CHARGEMENT DU SYSTÈME IA ---
@st.cache_resource
def load_system():
    # Embeddings Google (Version 004 pour la performance)
    embeddings = GoogleGenerativeAIEmbeddings(model="models/text-embedding-004")
    
    # Dossier de la base de données (téléchargé par le Dockerfile)
    persist_directory = "chroma_db"
    
    vectorstore = Chroma(
        persist_directory=persist_directory,
        embedding_function=embeddings
    )
    
    # Modèle Gemini 2.0 Flash (Version expérimentale comme demandé)
    llm = ChatGoogleGenerativeAI(
        model="gemini-2.0-flash-exp",
        temperature=0,
    )
    
    return vectorstore, llm

vectorstore, llm = load_system()

# --- 4. CONFIGURATION DE LA RÉPONSE EXPERTE ---
system_prompt = (
    "Tu es un assistant expert en droit social français. "
    "Utilise les extraits suivants pour répondre à la question de façon précise et sourcée. "
    "Si tu ne connais pas la réponse, dis-le poliment. "
    "\n\n"
    "{context}"
)

prompt = ChatPromptTemplate.from_messages(
    [
        ("system", system_prompt),
        ("human", "{input}"),
    ]
)

# Assemblage des chaînes LangChain
question_answer_chain = create_stuff_documents_chain(llm, prompt)
rag_chain = create_retrieval_chain(vectorstore.as_retriever(), question_answer_chain)

# --- 5. INTERFACE DE CHAT ---
if "messages" not in st.session_state:
    st.session_state.messages = []

# Affichage des messages passés
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Gestion de la nouvelle saisie
if query := st.chat_input("Posez votre question sur le droit social..."):
    st.session_state.messages.append({"role": "user", "content": query})
    with st.chat_message("user"):
        st.markdown(query)

    with st.chat_message("assistant"):
        with st.spinner("Analyse des sources..."):
            # Lancement de la recherche et génération de la réponse
            response = rag_chain.invoke({"input": query})
            answer = response["answer"]
            st.markdown(answer)
            st.session_state.messages.append({"role": "assistant", "content": answer})
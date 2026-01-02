import streamlit as st
import os
from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAIEmbeddings
from langchain_chroma import Chroma
from langchain.chains.retrieval import create_retrieval_chain
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain_core.prompts import ChatPromptTemplate

# --- CONFIGURATION ---
# Utilisation de la clé enregistrée sous le nom "Clé Gemini - Assistants"
os.environ["GOOGLE_API_KEY"] = st.secrets["GEMINI_API_KEY"]

# Titre de l'application
st.set_page_config(page_title="Expert Social Pro 2026", layout="wide")
st.title("🤖 Expert Social Pro 2026")

# --- INITIALISATION DU MODÈLE ET DE LA BASE ---
@st.cache_resource
def load_system():
    # 1. Chargement des Embeddings
    embeddings = GoogleGenerativeAIEmbeddings(model="models/text-embedding-004")
    
    # 2. Chargement de la base de données (le dossier créé par le Dockerfile)
    persist_directory = "chroma_db"
    vectorstore = Chroma(
        persist_directory=persist_directory,
        embedding_function=embeddings
    )
    
    # 3. Configuration du modèle Gemini 2.0 Flash
    llm = ChatGoogleGenerativeAI(
        model="gemini-2.0-flash-exp",
        temperature=0,
        max_tokens=None,
        timeout=None,
        max_retries=2,
    )
    
    return vectorstore, llm

vectorstore, llm = load_system()

# --- CONSTRUCTION DE LA CHAÎNE DE RÉPONSE ---
system_prompt = (
    "Tu es un assistant expert en droit social français. "
    "Utilise les extraits suivants pour répondre à la question. "
    "Si tu ne connais pas la réponse, dis simplement que tu ne sais pas. "
    "\n\n"
    "{context}"
)

prompt = ChatPromptTemplate.from_messages(
    [
        ("system", system_prompt),
        ("human", "{input}"),
    ]
)

# Création des chaînes
question_answer_chain = create_stuff_documents_chain(llm, prompt)
rag_chain = create_retrieval_chain(vectorstore.as_retriever(), question_answer_chain)

# --- INTERFACE UTILISATEUR ---
if "messages" not in st.session_state:
    st.session_state.messages = []

# Affichage de l'historique
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Zone de saisie
if query := st.chat_input("Posez votre question sur le BOSS ou le Code du Travail..."):
    st.session_state.messages.append({"role": "user", "content": query})
    with st.chat_message("user"):
        st.markdown(query)

    with st.chat_message("assistant"):
        with st.spinner("Analyse des sources en cours..."):
            response = rag_chain.invoke({"input": query})
            answer = response["answer"]
            st.markdown(answer)
            st.session_state.messages.append({"role": "assistant", "content": answer})
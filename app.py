# --- 1. CONFIGURATION SQLITE (CRITIQUE POUR CLOUD RUN) ---
import sys
import os
try:
    __import__('pysqlite3')
    sys.modules['sqlite3'] = sys.modules.pop('pysqlite3')
except ImportError:
    pass

import streamlit as st

# --- 2. IMPORTS DES MODULES ---
from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAIEmbeddings
from langchain_chroma import Chroma
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser

# --- 3. CONFIGURATION INTERFACE ET CLÉ API ---
st.set_page_config(page_title="Expert Social Pro 2026", layout="wide")
st.title("🤖 Expert Social Pro 2026")

# Récupération de la clé GEMINI via Environnement ou Secrets
api_key = os.getenv("GEMINI_API_KEY") 
if not api_key:
    try:
        api_key = st.secrets.get("GEMINI_API_KEY")
    except Exception:
        api_key = None

if not api_key:
    st.error("⚠️ Clé API GEMINI introuvable. Vérifiez vos variables d'environnement.")
    st.stop()

os.environ["GOOGLE_API_KEY"] = api_key

# --- 4. SYSTÈME DE MOT DE PASSE (3 TENTATIVES) ---
def check_password():
    # Initialisation du compteur
    if "retry_count" not in st.session_state:
        st.session_state["retry_count"] = 0

    def password_entered():
        # Récupération sécurisée du mot de passe attendu
        correct_pwd = os.getenv("APP_PASSWORD")
        if not correct_pwd:
            try:
                correct_pwd = st.secrets.get("APP_PASSWORD")
            except Exception:
                correct_pwd = None

        if st.session_state["pwd_input"] == correct_pwd:
            st.session_state["password_correct"] = True
            st.session_state["retry_count"] = 0
            del st.session_state["pwd_input"]
        else:
            st.session_state["password_correct"] = False
            st.session_state["retry_count"] += 1

    if st.session_state.get("password_correct"):
        return True

    if st.session_state["retry_count"] >= 3:
        st.error("🚫 Accès bloqué après 3 tentatives. Veuillez rafraîchir la page.")
        st.stop()

    if st.session_state["retry_count"] > 0:
        st.warning(f"⚠️ Mot de passe erroné. Tentative {st.session_state['retry_count']}/3")
    
    st.text_input("Veuillez saisir le mot de passe :", type="password", on_change=password_entered, key="pwd_input")
    return False

if not check_password():
    st.stop()

# --- 5. CHARGEMENT DU SYSTÈME RAG ---
@st.cache_resource
def load_system():
    # Utilisation des embeddings Google et de la base téléchargée via Dockerfile
    embeddings = GoogleGenerativeAIEmbeddings(model="models/text-embedding-004")
    vectorstore = Chroma(persist_directory="chroma_db", embedding_function=embeddings)
    # Modèle de référence : gemini-2.0-flash-exp [cite: 2025-12-17]
    llm = ChatGoogleGenerativeAI(model="gemini-2.0-flash-exp", temperature=0)
    return vectorstore, llm

vectorstore, llm = load_system()

# --- 6. CONFIGURATION DU PROMPT ET DE LA CHAÎNE ---
prompt = ChatPromptTemplate.from_template("""
Tu es un assistant expert en droit social français. Utilise les documents fournis pour répondre.
Si tu ne sais pas, dis que tu ne sais pas.

Contexte : {context}
Question : {question}
""")

retriever = vectorstore.as_retriever(search_kwargs={"k": 3})
rag_chain = (
    {"context": retriever | (lambda docs: "\n\n".join(d.page_content for d in docs)), "question": RunnablePassthrough()}
    | prompt | llm | StrOutputParser()
)

# --- 7. INTERFACE DE CHAT ---
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
        with st.spinner("Recherche dans la base de données..."):
            answer = rag_chain.invoke(query)
            st.markdown(answer)
            st.session_state.messages.append({"role": "assistant", "content": answer})
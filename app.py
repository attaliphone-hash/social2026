# --- 1. CONFIGURATION SQLITE ---
import sys
import os
try:
    __import__('pysqlite3')
    sys.modules['sqlite3'] = sys.modules.pop('pysqlite3')
except ImportError:
    pass

import streamlit as st

# --- 2. CONFIGURATION PAGE ---
st.set_page_config(page_title="Expert Social Pro 2026", layout="wide")

# --- 3. SYSTÈME DE MOT DE PASSE (LOGIQUE SIMPLIFIÉE V21) ---
if "password_correct" not in st.session_state:
    st.session_state["password_correct"] = False

# Écran de verrouillage
if not st.session_state["password_correct"]:
    st.title("🔐 Accès Restreint")
    # On utilise un champ simple sans on_change pour éviter le refresh automatique
    pwd_input = st.text_input("Veuillez saisir le mot de passe Expert :", type="password")
    
    if st.button("Se connecter"):
        correct_pwd = os.getenv("APP_PASSWORD") or st.secrets.get("APP_PASSWORD")
        if pwd_input == correct_pwd:
            st.session_state["password_correct"] = True
            st.rerun() # On force le rechargement propre
        else:
            st.error("😕 Mot de passe incorrect.")
    st.stop()

# --- 4. SI CONNECTÉ : CHARGEMENT DES IMPORTS LOURDS ---
from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAIEmbeddings
from langchain_chroma import Chroma
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser

st.title("🤖 Expert Social Pro 2026")

api_key = os.getenv("GEMINI_API_KEY") or st.secrets.get("GEMINI_API_KEY")
if not api_key:
    st.error("⚠️ Clé API GEMINI manquante.")
    st.stop()
os.environ["GOOGLE_API_KEY"] = api_key

# --- 5. CHARGEMENT DU SYSTÈME RAG ---
@st.cache_resource
def load_system():
    embeddings = GoogleGenerativeAIEmbeddings(model="models/text-embedding-004")
    vectorstore = Chroma(persist_directory="chroma_db", embedding_function=embeddings)
    # Modèle IA : gemini-2.0-flash-exp [cite: 2025-12-17]
    llm = ChatGoogleGenerativeAI(model="gemini-2.0-flash-exp", temperature=0)
    return vectorstore, llm

vectorstore, llm = load_system()

# --- 6. CHAÎNE RAG (VERSION EXPERT k=10) ---
prompt = ChatPromptTemplate.from_template("""
Tu es un assistant expert en droit social et paie. Ton utilisateur est un professionnel.
CONSIGNE STRICTE : Ne suggère JAMAIS de vérifier le BOSS ou le Code du travail. 
Donne immédiatement les chiffres, plafonds, taux et conditions extraits du contexte. 
Cite les articles de loi ou les paragraphes du BOSS si disponibles.

Contexte : {context}
Question : {question}

Réponse technique et précise :
""")

# k=10 pour fouiller toute la doc [cite: 2026-01-02]
retriever = vectorstore.as_retriever(search_kwargs={"k": 10})
rag_chain = (
    {"context": retriever | (lambda docs: "\n\n".join(d.page_content for d in docs)), "question": RunnablePassthrough()}
    | prompt | llm | StrOutputParser()
)

# --- 7. CHAT ---
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
        with st.spinner("Analyse approfondie du BOSS et des Codes..."):
            answer = rag_chain.invoke(query)
            st.markdown(answer)
            st.session_state.messages.append({"role": "assistant", "content": answer})
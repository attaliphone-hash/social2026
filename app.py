# --- 1. CONFIGURATION SQLITE (CRITIQUE POUR CLOUD RUN) ---
import sys
import os
try:
    __import__('pysqlite3')
    sys.modules['sqlite3'] = sys.modules.pop('pysqlite3')
except ImportError:
    pass

import streamlit as st

# --- 2. CONFIGURATION PAGE (LÉGÈRE POUR ÉVITER LES TIMEOUTS) ---
st.set_page_config(page_title="Expert Social Pro 2026", layout="wide")

# --- 3. SYSTÈME DE MOT DE PASSE (BARRAGE PRIORITAIRE) ---
if "password_correct" not in st.session_state:
    st.session_state["password_correct"] = False

def password_entered():
    """Vérifie le mot de passe et stabilise la session."""
    correct_pwd = os.getenv("APP_PASSWORD") or st.secrets.get("APP_PASSWORD")
    if st.session_state["pwd_input"] == correct_pwd:
        st.session_state["password_correct"] = True
        del st.session_state["pwd_input"]
    else:
        st.error("😕 Mot de passe incorrect.")

if not st.session_state["password_correct"]:
    st.title("🔐 Accès Restreint")
    st.text_input("Veuillez saisir le mot de passe Expert :", 
                  type="password", on_change=password_entered, key="pwd_input")
    st.stop()  # Bloque tout chargement lourd tant que non identifié

# --- 4. SI AUTHENTIFIÉ : CHARGEMENT DES MODULES LOURDS ---
from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAIEmbeddings
from langchain_chroma import Chroma
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser

st.title("🤖 Expert Social Pro 2026")

# Clé API
api_key = os.getenv("GEMINI_API_KEY") or st.secrets.get("GEMINI_API_KEY")
if not api_key:
    st.error("⚠️ Clé API GEMINI introuvable.")
    st.stop()
os.environ["GOOGLE_API_KEY"] = api_key

# --- 5. CHARGEMENT DU SYSTÈME RAG (CACHÉ) ---
@st.cache_resource
def load_system():
    embeddings = GoogleGenerativeAIEmbeddings(model="models/text-embedding-004")
    # Chargement de la base "Golden Index" de 167 Mo
    vectorstore = Chroma(persist_directory="chroma_db", embedding_function=embeddings)
    # Modèle IA : gemini-2.0-flash-exp
    llm = ChatGoogleGenerativeAI(model="gemini-2.0-flash-exp", temperature=0)
    return vectorstore, llm

vectorstore, llm = load_system()

# --- 6. CONFIGURATION EXPERT (k=10 ET PROMPT DIRECTIF) ---
# k=10 permet d'aller chercher les détails précis souvent cachés dans les sous-sections
retriever = vectorstore.as_retriever(search_kwargs={"k": 10})

prompt = ChatPromptTemplate.from_template("""
Tu es un assistant expert en droit social et paie français. Ton utilisateur est un professionnel.
CONSIGNE STRICTE : Ne suggère JAMAIS de vérifier le BOSS ou le Code du travail (l'utilisateur le sait). 
Donne immédiatement les chiffres, plafonds, taux et conditions extraits du contexte. 
Cite les articles de loi ou les paragraphes du BOSS si disponibles.

Contexte : {context}
Question : {question}

Réponse technique et précise :
""")

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

if query := st.chat_input("Posez votre question technique (ex: cumul FMD, bonus transport, etc.)..."):
    st.session_state.messages.append({"role": "user", "content": query})
    with st.chat_message("user"):
        st.markdown(query)
    
    with st.chat_message("assistant"):
        with st.spinner("Analyse experte en cours..."):
            answer = rag_chain.invoke(query)
            st.markdown(answer)
            st.session_state.messages.append({"role": "assistant", "content": answer})
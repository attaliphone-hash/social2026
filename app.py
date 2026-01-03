# --- 1. CONFIGURATION SQLITE (CRITIQUE POUR CLOUD RUN) ---
import sys
import os
try:
    __import__('pysqlite3')
    sys.modules['sqlite3'] = sys.modules.pop('pysqlite3')
except ImportError:
    pass

import streamlit as st

# --- 2. CONFIGURATION PAGE (LÉGÈRE) ---
st.set_page_config(page_title="Expert Social Pro 2026", layout="wide")

# --- 3. SYSTÈME DE MOT DE PASSE (LOGIQUE BOUTON V21 - LA PLUS STABLE) ---
if "password_correct" not in st.session_state:
    st.session_state["password_correct"] = False

if not st.session_state["password_correct"]:
    st.title("🔐 Accès Réservé")
    
    # Utilisation d'un champ simple sans on_change pour éviter les boucles automatiques
    pwd_input = st.text_input("Veuillez saisir votre mot de passe :", type="password")
    
    if st.button("Accéder à l'Expert Social"):
        correct_pwd = os.getenv("APP_PASSWORD") or st.secrets.get("APP_PASSWORD")
        if pwd_input == correct_pwd:
            st.session_state["password_correct"] = True
            st.rerun() # Rechargement immédiat pour valider l'accès
        else:
            st.error("😕 Mot de passe incorrect. Veuillez réessayer")
    st.stop() # Bloque le reste du script tant que password_correct est False

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
    vectorstore = Chroma(persist_directory="chroma_db", embedding_function=embeddings)
    # Modèle IA de référence : gemini-2.0-flash-exp [cite: 2025-12-17]
    llm = ChatGoogleGenerativeAI(model="gemini-2.0-flash-exp", temperature=0)
    return vectorstore, llm

vectorstore, llm = load_system()

# --- 6. CONFIGURATION EXPERT (k=10 ET PROMPT DIRECTIF) ---
retriever = vectorstore.as_retriever(search_kwargs={"k": 10})

prompt = ChatPromptTemplate.from_template("""
Tu es un assistant expert en droit social et paie français. Ton utilisateur est un professionnel.
CONSIGNE STRICTE : Ne suggère JAMAIS de vérifier le BOSS ou le Code du travail. 
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

if query := st.chat_input("Posez votre question ici..."):
    st.session_state.messages.append({"role": "user", "content": query})
    with st.chat_message("user"):
        st.markdown(query)
    
    with st.chat_message("assistant"):
        with st.spinner("Analyse experte en cours..."):
            answer = rag_chain.invoke(query)
            st.markdown(answer)
            st.session_state.messages.append({"role": "assistant", "content": answer})
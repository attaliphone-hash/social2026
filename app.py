# --- 1. CONFIGURATION SQLITE (CRITIQUE POUR CLOUD RUN) ---
import sys
import os

# Force l'utilisation de pysqlite3 pour éviter l'erreur de version SQLite sur Debian
try:
    __import__('pysqlite3')
    sys.modules['sqlite3'] = sys.modules.pop('pysqlite3')
except ImportError:
    pass

import streamlit as st

# --- 2. IMPORTS DES MODULES LANGCHAIN ---
from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAIEmbeddings
from langchain_chroma import Chroma
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser

# --- 3. CONFIGURATION INTERFACE ET CLÉ API ---
st.set_page_config(page_title="Expert Social Pro 2026", layout="wide")
st.title("🤖 Expert Social Pro 2026")

# Récupération de la clé API via l'environnement (Cloud Run) ou les secrets (Streamlit)
api_key = os.getenv("GEMINI_API_KEY") 
if not api_key:
    try:
        api_key = st.secrets.get("GEMINI_API_KEY")
    except Exception:
        api_key = None

if not api_key:
    st.error("⚠️ Clé API GEMINI introuvable. Vérifiez votre configuration.")
    st.stop()

os.environ["GOOGLE_API_KEY"] = api_key

# --- 4. SYSTÈME DE MOT DE PASSE (CORRECTIF BOUCLE DE CHAT) ---
# Initialisation de l'état de connexion [cite: 2026-01-02]
if "password_correct" not in st.session_state:
    st.session_state["password_correct"] = False

def password_entered():
    """Vérifie le mot de passe et met à jour l'état de la session."""
    correct_pwd = os.getenv("APP_PASSWORD")
    if not correct_pwd:
        try:
            correct_pwd = st.secrets.get("APP_PASSWORD")
        except Exception:
            correct_pwd = None

    if st.session_state["pwd_input"] == correct_pwd:
        st.session_state["password_correct"] = True
        del st.session_state["pwd_input"] # Nettoyage après succès
    else:
        st.session_state["password_correct"] = False
        st.error("😕 Mot de passe incorrect.")

# Affichage de l'écran de verrouillage tant que le mot de passe n'est pas correct
if not st.session_state["password_correct"]:
    st.text_input("Veuillez saisir le mot de passe pour accéder à l'Expert Social :", 
                  type="password", on_change=password_entered, key="pwd_input")
    st.stop() # Arrête l'exécution ici tant que l'accès n'est pas validé

# --- 5. CHARGEMENT DU SYSTÈME RAG (CACHÉ) ---
@st.cache_resource
def load_system():
    # Modèle d'embeddings Google
    embeddings = GoogleGenerativeAIEmbeddings(model="models/text-embedding-004")
    # Chargement de la base SQLite "Golden Index" (167 Mo) [cite: 2025-12-18]
    vectorstore = Chroma(persist_directory="chroma_db", embedding_function=embeddings)
    # Modèle IA de référence : gemini-2.0-flash-exp [cite: 2025-12-17]
    llm = ChatGoogleGenerativeAI(model="gemini-2.0-flash-exp", temperature=0)
    return vectorstore, llm

vectorstore, llm = load_system()

# --- 6. CONFIGURATION DU PROMPT ET DE LA CHAÎNE RAG ---
prompt = ChatPromptTemplate.from_template("""
Tu es un assistant expert en droit social français. 
Utilise exclusivement le contexte fourni pour répondre. Si la réponse n'est pas dans le contexte, dis-le.

Contexte : {context}
Question : {question}

Réponse experte :
""")

retriever = vectorstore.as_retriever(search_kwargs={"k": 3})
rag_chain = (
    {"context": retriever | (lambda docs: "\n\n".join(d.page_content for d in docs)), "question": RunnablePassthrough()}
    | prompt | llm | StrOutputParser()
)

# --- 7. INTERFACE DE DISCUSSION (MÉMOIRE DE SESSION) ---
if "messages" not in st.session_state:
    st.session_state.messages = []

# Affichage des anciens messages
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Zone de saisie utilisateur
if query := st.chat_input("Posez votre question sur le Code du travail ou le BOSS..."):
    # Ajout du message utilisateur
    st.session_state.messages.append({"role": "user", "content": query})
    with st.chat_message("user"):
        st.markdown(query)
    
    # Génération et affichage de la réponse
    with st.chat_message("assistant"):
        with st.spinner("Analyse des sources en cours..."):
            answer = rag_chain.invoke(query)
            st.markdown(answer)
            st.session_state.messages.append({"role": "assistant", "content": answer})
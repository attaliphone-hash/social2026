# --- 1. CONFIGURATION SQLITE ET IMPORTS ---
import sys
import os
import base64 

# Indispensable pour ChromaDB sur Cloud Run
try:
    __import__('pysqlite3')
    sys.modules['sqlite3'] = sys.modules.pop('pysqlite3')
except ImportError:
    pass

import streamlit as st

# --- 2. FONCTIONS DESIGN & CSS ---

def get_base64(bin_file):
    """Encode une image locale en base64."""
    with open(bin_file, 'rb') as f:
        data = f.read()
    return base64.b64encode(data).decode()

def set_design(bg_image_file, sidebar_color):
    """Injecte le CSS pour le fond et la sidebar."""
    try:
        bin_str = get_base64(bg_image_file)
        extension = "webp" if bg_image_file.endswith(".webp") else "png"
        page_bg_img = f'''
        <style>
        .stApp {{
            background-image: url("data:image/{extension};base64,{bin_str}");
            background-size: cover;
            background-repeat: no-repeat;
            background-attachment: fixed;
        }}
        [data-testid="stToolbar"] {{ visibility: hidden; height: 0%; }}
        [data-testid="stDecoration"] {{ visibility: hidden; height: 0%; }}
        header {{ background-color: transparent !important; }}
        .block-container {{ padding-top: 1rem !important; }}
        [data-testid="stSidebar"] > div:first-child {{ background-color: {sidebar_color}; }}
        [data-testid="stSidebar"] h1, [data-testid="stSidebar"] h2, [data-testid="stSidebar"] h3, 
        [data-testid="stSidebar"] p, [data-testid="stSidebar"] span, [data-testid="stSidebar"] label,
        [data-testid="stSidebar"] .stCaption, [data-testid="stSidebar"] div.stMarkdown p {{
             color: white !important;
        }}
        .stChatMessage {{
            background-color: rgba(255, 255, 255, 0.95);
            border-radius: 15px;
            padding: 10px;
            margin-bottom: 10px;
        }}
        </style>
        '''
        st.markdown(page_bg_img, unsafe_allow_html=True)
    except FileNotFoundError:
        pass

# --- 3. CONFIGURATION PAGE ET AUTHENTIFICATION ---
st.set_page_config(page_title="Expert Social Pro 2026", layout="wide", page_icon="⚖️")

# Correction : Logique de session robuste pour Cloud Run
if "password_correct" not in st.session_state:
    st.session_state["password_correct"] = False

def check_password():
    """Vérifie le mot de passe et met à jour la session."""
    correct_pwd = os.getenv("APP_PASSWORD") or st.secrets.get("APP_PASSWORD")
    if st.session_state["pwd_input"] == correct_pwd:
        st.session_state["password_correct"] = True
        del st.session_state["pwd_input"]  # Supprime le mot de passe de la mémoire après validation
    else:
        st.error("Mot de passe incorrect.")

# Écran de verrouillage
if not st.session_state["password_correct"]:
    set_design('background.webp', '#024c6f')
    st.markdown("<h1 style='text-align: center; color: #024c6f; margin-top: 100px;'>🔐 Accès Expert Réservé</h1>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1,2,1])
    with col2:
        st.text_input("Veuillez saisir le code d'accès :", type="password", key="pwd_input", on_change=check_password)
    st.stop()

# Si authentifié, appliquer le design complet
set_design('background.webp', '#024c6f')

# --- 4. CHARGEMENT IA ---
from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAIEmbeddings
from langchain_chroma import Chroma
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough, RunnableParallel
from langchain_core.output_parsers import StrOutputParser

# --- 5. CHARGEMENT SYSTÈME (RAG) ---
api_key = os.getenv("GOOGLE_API_KEY") or st.secrets.get("GOOGLE_API_KEY")
if not api_key:
    st.error("⚠️ Clé API GEMINI manquante.")
    st.stop()
os.environ["GOOGLE_API_KEY"] = api_key

@st.cache_resource
def load_system():
    # Utilisation du modèle d'embedding recommandé
    embeddings = GoogleGenerativeAIEmbeddings(model="models/text-embedding-004")
    # Chargement de la base vectorielle chroma_db (163 MiB)
    vectorstore = Chroma(persist_directory="chroma_db", embedding_function=embeddings)
    # Configuration de Gemini 2.0 Flash
    llm = ChatGoogleGenerativeAI(model="gemini-2.0-flash-exp", temperature=0)
    return vectorstore, llm

vectorstore, llm = load_system()
retriever = vectorstore.as_retriever(search_kwargs={"k": 10})

# --- 6. PROMPT EXPERT ---
prompt = ChatPromptTemplate.from_template("""
Tu es un assistant expert en droit social et paie français (Expert Social Pro 2026).
CONSIGNE : Ne suggère JAMAIS de vérifier le BOSS. Donne directement les chiffres, taux et conditions. 
Cite systématiquement le nom du fichier source (ex: BOSS_Frais_Pro.txt) et les articles de loi entre parenthèses.

Contexte : {context}
Question : {question}

Réponse technique et précise :
""")

rag_chain_with_sources = RunnableParallel(
    {"context": retriever, "question": RunnablePassthrough()}
).assign(answer= prompt | llm | StrOutputParser())

# --- 7. SIDEBAR ---
with st.sidebar:
    st.markdown("##") 
    st.markdown("**Bienvenue sur votre expert social dédié.**")
    st.markdown("---")
    st.subheader("Contexte Juridique")
    st.info("📅 **Année Fiscale : 2026**\n\nBase à jour des dernières LFSS et Ordonnances.")
    st.markdown("---")
    if st.button("🗑️ Nouvelle Conversation", use_container_width=True):
        st.session_state.messages = []
        st.rerun()
    st.markdown("---")
    st.caption("Expert Social Pro v3.1 - Déploiement Cloud Run")

# --- 8. INTERFACE CHAT ---
col_logo, col_title = st.columns([1, 12]) 
with col_logo:
    try:
        st.image("avatar-logo.png", width=70)
    except:
        st.write("⚖️")
with col_title:
    st.title("Expert Social Pro 2026")

st.markdown("Analyse du BOSS, Code du travail et Code de la Sécurité sociale en temps réel.")
st.markdown("---")

if "messages" not in st.session_state:
    st.session_state.messages = []

# Affichage de l'historique
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Zone de saisie
if query := st.chat_input("Posez votre question technique ici..."):
    st.session_state.messages.append({"role": "user", "content": query})
    with st.chat_message("user"):
        st.markdown(query)
    
    with st.chat_message("assistant"):
        with st.spinner("Analyse croisée des sources officielles..."):
            response = rag_chain_with_sources.invoke(query)
            st.markdown(response["answer"])
            
            # Affichage des sources pour la traçabilité
            with st.expander("📚 Voir les extraits juridiques utilisés"):
                for i, doc in enumerate(response["context"]):
                    source_name = doc.metadata.get("source", "Source inconnue")
                    st.markdown(f"**Source {i+1} : {source_name}**")
                    st.caption(doc.page_content)
                    st.markdown("---")
            st.session_state.messages.append({"role": "assistant", "content": response["answer"]})
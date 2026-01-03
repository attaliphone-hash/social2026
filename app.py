# --- 1. CONFIGURATION SQLITE ET IMPORTS ---
import sys
import os
import base64 
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
    """Injecte le CSS pour le fond, la sidebar et masques les éléments parasites."""
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
    [data-testid="stSidebar"] .stAlert {{
        background-color: rgba(255, 255, 255, 0.05) !important;
        color: white !important;
        border: 1px solid rgba(255, 255, 255, 0.5) !important;
    }}
    [data-testid="stSidebar"] button {{
        background-color: transparent !important;
        border: 1px solid white !important;
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

# --- 3. CONFIGURATION PAGE ET AUTHENTIFICATION ---
st.set_page_config(page_title="Expert Social Pro 2026", layout="wide", page_icon="⚖️")

try:
    set_design('background.webp', '#024c6f')
except FileNotFoundError:
    pass

if "password_correct" not in st.session_state:
    st.session_state["password_correct"] = False

if not st.session_state["password_correct"]:
    st.markdown("<h1 style='text-align: center; color: #024c6f;'>🔐 Accès Expert Réservé</h1>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1,2,1])
    with col2:
        pwd_input = st.text_input("Mot de passe :", type="password", label_visibility="collapsed")
        if st.button("Connexion sécurisée", type="primary", use_container_width=True):
            correct_pwd = os.getenv("APP_PASSWORD") or st.secrets.get("APP_PASSWORD")
            if pwd_input == correct_pwd:
                st.session_state["password_correct"] = True
                st.rerun()
            else:
                st.error("Identifiants incorrects.")
    st.stop()

# --- 4. CHARGEMENT IA ---
from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAIEmbeddings
from langchain_chroma import Chroma
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough, RunnableParallel
from langchain_core.output_parsers import StrOutputParser

# --- 5. SIDEBAR ---
with st.sidebar:
    st.markdown("##") 
    st.markdown("**Bienvenue sur votre expert social dédié.**")
    st.markdown("---")
    st.subheader("Contexte Juridique")
    st.info("📅 **Année Fiscale : 2026**\n\nBase à jour des dernières LFSS et Ordonnances connues.")
    st.markdown("---")
    if st.button("🗑️ Nouvelle Conversation", use_container_width=True):
        st.session_state.messages = []
        st.rerun()
    st.markdown("---")
    st.caption("Expert Social Pro v3.1 - Accès Cabinet")

# --- 6. INTERFACE PRINCIPALE ---
col_logo, col_title = st.columns([1, 12]) 
with col_logo:
    st.image("avatar-logo.png", width=70) 
with col_title:
    st.title("Expert Social Pro 2026")

st.markdown("""
Posez vos questions techniques en droit social et paie. L'IA analyse le BOSS, le Code du travail, le Code de la Sécurité sociale et les conventions pour vous fournir des réponses basées exclusivement sur des textes officiels.
""")
st.markdown("---")

api_key = os.getenv("GOOGLE_API_KEY") or st.secrets.get("GOOGLE_API_KEY")
if not api_key:
    st.error("⚠️ Clé API GEMINI manquante.")
    st.stop()
os.environ["GOOGLE_API_KEY"] = api_key

# RAG
@st.cache_resource
def load_system():
    embeddings = GoogleGenerativeAIEmbeddings(model="models/text-embedding-004")
    vectorstore = Chroma(persist_directory="chroma_db", embedding_function=embeddings)
    llm = ChatGoogleGenerativeAI(model="gemini-2.0-flash-exp", temperature=0)
    return vectorstore, llm

vectorstore, llm = load_system()

# --- 7. CHAÎNE RAG (MODIFIÉ POUR TXT) ---
retriever = vectorstore.as_retriever(search_kwargs={"k": 10})

prompt = ChatPromptTemplate.from_template("""
Tu es un assistant expert en droit social et paie français.
CONSIGNE : Ne suggère JAMAIS de vérifier le BOSS. Donne directement les chiffres, taux et conditions. 
Cite le nom du fichier source (ex: BOSS_Frais_Pro.txt) et les articles de loi ou paragraphes du BOSS entre parenthèses quand tu les utilises.

Contexte : {context}
Question : {question}

Réponse technique et précise :
""")

rag_chain_with_sources = RunnableParallel(
    {"context": retriever, "question": RunnablePassthrough()}
).assign(answer= prompt | llm | StrOutputParser())

# --- 8. CHAT (MODIFIÉ POUR LES SOURCES TXT) ---

assistant_avatar = "avatar-logo.png"
user_avatar = "🧑‍💼"

if "messages" not in st.session_state:
    st.session_state.messages = []

for message in st.session_state.messages:
    avatar_to_use = assistant_avatar if message["role"] == "assistant" else user_avatar
    with st.chat_message(message["role"], avatar=avatar_to_use):
        st.markdown(message["content"])

if query := st.chat_input("Posez votre question technique ici..."):
    st.session_state.messages.append({"role": "user", "content": query})
    with st.chat_message("user", avatar=user_avatar):
        st.markdown(query)
    
    with st.chat_message("assistant", avatar=assistant_avatar):
        with st.spinner("Analyse croisée des textes officiels en cours..."):
            response = rag_chain_with_sources.invoke(query)
            st.markdown(response["answer"])
            with st.expander("📚 Voir les sources officielles et extraits juridiques utilisés"):
                for i, doc in enumerate(response["context"]):
                    source_name = doc.metadata.get("source", "Source inconnue")
                    st.markdown(f"**Source {i+1} : {source_name}**")
                    st.caption(doc.page_content)
                    st.markdown("---")
            st.session_state.messages.append({"role": "assistant", "content": response["answer"]})
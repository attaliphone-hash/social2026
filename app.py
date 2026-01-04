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
    with open(bin_file, 'rb') as f:
        data = f.read()
    return base64.b64encode(data).decode()

def set_design(bg_image_file, sidebar_color):
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
        /* Texte blanc pour le titre et sous-titre principal */
        h1, .stMarkdown p {{ color: white !important; }}
        
        [data-testid="stToolbar"] {{ visibility: hidden; height: 0%; }}
        [data-testid="stDecoration"] {{ visibility: hidden; height: 0%; }}
        header {{ background-color: transparent !important; }}
        .block-container {{ padding-top: 1rem !important; }}
        
        /* Sidebar */
        [data-testid="stSidebar"] > div:first-child {{ background-color: {sidebar_color}; }}
        [data-testid="stSidebar"] h1, [data-testid="stSidebar"] h2, [data-testid="stSidebar"] h3, 
        [data-testid="stSidebar"] p, [data-testid="stSidebar"] span, [data-testid="stSidebar"] label,
        [data-testid="stSidebar"] .stCaption, [data-testid="stSidebar"] div.stMarkdown p {{
             color: white !important;
        }}
        
        /* Bouton Nouvelle Conversation corrigé */
        [data-testid="stSidebar"] button {{
            background-color: white !important;
            color: #024c6f !important;
            border: 1px solid #024c6f !important;
            font-weight: bold !important;
            height: 3em !important;
            width: 100% !important;
            display: flex !important;
            align-items: center !important;
            justify-content: center !important;
        }}
        /* Force la visibilité du texte "Nouvelle Conversation" */
        [data-testid="stSidebar"] button p {{
            color: #024c6f !important;
            margin: 0 !important;
            font-size: 14px !important;
        }}
        
        .stChatMessage {{
            background-color: rgba(255, 255, 255, 0.95);
            border-radius: 15px;
            padding: 10px;
            margin-bottom: 10px;
        }}
        /* Ajustement des textes dans les messages pour lisibilité sur fond blanc */
        .stChatMessage p {{ color: black !important; }}
        </style>
        '''
        st.markdown(page_bg_img, unsafe_allow_html=True)
    except FileNotFoundError:
        pass

# --- 3. CONFIGURATION PAGE ET AUTHENTIFICATION ---
st.set_page_config(page_title="Expert Social Pro 2026", layout="wide", page_icon="⚖️")

if "password_correct" not in st.session_state:
    st.session_state["password_correct"] = False

def check_password():
    correct_pwd = os.getenv("APP_PASSWORD") or st.secrets.get("APP_PASSWORD")
    if st.session_state["pwd_input"] == correct_pwd:
        st.session_state["password_correct"] = True
        del st.session_state["pwd_input"]
    else:
        st.error("Mot de passe incorrect.")

if not st.session_state["password_correct"]:
    set_design('background.webp', '#024c6f')
    st.markdown("<h1 style='text-align: center; color: white; margin-top: 100px;'>🔐 Accès Expert Réservé</h1>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1,2,1])
    with col2:
        st.text_input("Veuillez saisir le code d'accès :", type="password", key="pwd_input", on_change=check_password)
    st.stop()

set_design('background.webp', '#024c6f')

# --- 4. CHARGEMENT IA ---
from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAIEmbeddings
from langchain_chroma import Chroma
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough, RunnableParallel
from langchain_core.output_parsers import StrOutputParser

api_key = os.getenv("GOOGLE_API_KEY") or st.secrets.get("GOOGLE_API_KEY")
if not api_key:
    st.error("⚠️ Clé API GEMINI manquante.")
    st.stop()
os.environ["GOOGLE_API_KEY"] = api_key

@st.cache_resource
def load_system():
    embeddings = GoogleGenerativeAIEmbeddings(model="models/text-embedding-004")
    vectorstore = Chroma(persist_directory="chroma_db", embedding_function=embeddings)
    llm = ChatGoogleGenerativeAI(model="gemini-2.0-flash-exp", temperature=0)
    return vectorstore, llm

vectorstore, llm = load_system()
retriever = vectorstore.as_retriever(search_kwargs={"k": 10})

# --- 5. PROMPT EXPERT ---
prompt = ChatPromptTemplate.from_template("""
Tu es un assistant expert en droit social et paie français (Expert Social Pro 2026).
CONSIGNE : Ne suggère JAMAIS de vérifier le BOSS. Donne directement les chiffres et taux. 
IMPORTANT : Quand tu cites tes sources, ne donne pas le nom du fichier (ex: BOSS_Frais_Pro.txt), utilise simplement le terme "BOSS" ou "Code du travail" selon le contexte.

Contexte : {context}
Question : {question}

Réponse technique et précise :
""")

def format_source_name(name):
    """Simplifie le nom de la source pour l'affichage utilisateur."""
    if "BOSS" in name.upper(): return "BOSS"
    if "LEGITEXT" in name.upper() or "CODE" in name.upper(): return "Code du Travail"
    return "Source officielle"

rag_chain_with_sources = RunnableParallel(
    {"context": retriever, "question": RunnablePassthrough()}
).assign(answer= prompt | llm | StrOutputParser())

# --- 6. SIDEBAR ---
with st.sidebar:
    st.markdown("##") 
    st.markdown("### **Bienvenue sur votre expert social dédié.**")
    st.markdown("---")
    st.subheader("Contexte Juridique")
    st.info("📅 **Année Fiscale : 2026**\n\nBase à jour des dernières LFSS et Ordonnances.")
    st.markdown("---")
    if st.button("🗑️ Nouvelle Conversation", use_container_width=True):
        st.session_state.messages = []
        st.rerun()
    st.markdown("---")
    st.caption("Expert Social Pro ©BusinessAgentAi")

# --- 7. INTERFACE CHAT ---
col_logo, col_title = st.columns([1, 12]) 
with col_logo:
    try:
        st.image("avatar-logo.png", width=70)
    except:
        st.write("⚖️")
with col_title:
    st.markdown("<h1 style='color: white; margin-bottom: 0;'>Expert Social Pro 2026</h1>", unsafe_allow_html=True)
    st.markdown("<p style='color: white; font-style: italic;'>Analyse du BOSS, Code du travail et Code de la Sécurité sociale en temps réel.</p>", unsafe_allow_html=True)

st.markdown("---")

assistant_avatar = "avatar-logo.png"
user_avatar = "🧑‍💼"

if "messages" not in st.session_state:
    st.session_state.messages = []

for message in st.session_state.messages:
    with st.chat_message(message["role"], avatar=assistant_avatar if message["role"] == "assistant" else user_avatar):
        st.markdown(message["content"])

if query := st.chat_input("Posez votre question technique ici..."):
    st.session_state.messages.append({"role": "user", "content": query})
    with st.chat_message("user", avatar=user_avatar):
        st.markdown(query)
    
    with st.chat_message("assistant", avatar=assistant_avatar):
        with st.spinner("Analyse croisée des sources officielles..."):
            response = rag_chain_with_sources.invoke(query)
            st.markdown(response["answer"])
            
            with st.expander("📚 Voir les extraits juridiques utilisés"):
                for i, doc in enumerate(response["context"]):
                    raw_source = doc.metadata.get("source", "Source inconnue")
                    source_display = format_source_name(raw_source)
                    st.markdown(f"**Source {i+1} : {source_display}**")
                    st.caption(doc.page_content)
                    st.markdown("---")
            st.session_state.messages.append({"role": "assistant", "content": response["answer"]})
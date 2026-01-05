# --- 1. CONFIGURATION SQLITE ET PATCH ---
import sys
import os
import base64 
import streamlit as st

# Patch critique pour Cloud Run
try:
    __import__('pysqlite3')
    sys.modules['sqlite3'] = sys.modules.pop('pysqlite3')
except ImportError:
    pass

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
        /* Image de fond principale */
        .stApp {{
            background-image: url("data:image/{extension};base64,{bin_str}");
            background-size: cover;
            background-repeat: no-repeat;
            background-attachment: fixed;
        }}
        
        /* Masquer Toolbar et Décoration standard */
        [data-testid="stToolbar"] {{ visibility: hidden; height: 0%; }}
        [data-testid="stDecoration"] {{ visibility: hidden; height: 0%; }}
        header {{ background-color: transparent !important; }}
        
        /* --- DESIGN SIDEBAR (Capture 1) --- */
        [data-testid="stSidebar"] > div:first-child {{ background-color: {sidebar_color}; }}
        [data-testid="stSidebar"] h1, [data-testid="stSidebar"] h2, [data-testid="stSidebar"] h3, 
        [data-testid="stSidebar"] p, [data-testid="stSidebar"] span, [data-testid="stSidebar"] label,
        [data-testid="stSidebar"] .stCaption, [data-testid="stSidebar"] div.stMarkdown p {{
             color: white !important;
        }}
        /* On retire le style agressif des boutons blancs dans la sidebar car il n'y en a plus */
        
        /* --- DESIGN HEADER (Capture 2) --- */
        .block-container {{ padding-top: 2rem !important; }}

        /* Style spécifique des boutons du Header (Transparents + Bordure Blanche) */
        /* Note: cela cible les boutons dans la zone principale */
        .main .stButton > button {{
            background-color: rgba(255, 255, 255, 0.1) !important;
            color: white !important;
            border: 1px solid white !important;
            border-radius: 5px !important;
            font-size: 14px !important;
            padding: 0.5rem 1rem !important;
        }}
        .main .stButton > button:hover {{
            background-color: rgba(255, 255, 255, 0.3) !important;
            border-color: white !important;
            color: white !important;
        }}

        /* --- DESIGN CHAT --- */
        .stChatMessage {{
            background-color: rgba(255, 255, 255, 0.95);
            border-radius: 15px;
            padding: 10px;
            margin-bottom: 10px;
            border: none;
        }}
        .stChatMessage p, .stChatMessage li {{ color: black !important; }}
        
        /* --- DESIGN SOURCES --- */
        .streamlit-expanderHeader {{
            background-color: rgba(220, 255, 220, 0.5) !important;
            color: black !important;
            border-radius: 5px;
        }}
        .streamlit-expanderContent p {{ color: black !important; font-size: 0.9em; }}
        </style>
        '''
        st.markdown(page_bg_img, unsafe_allow_html=True)
    except FileNotFoundError:
        pass

# --- 3. AUTHENTIFICATION ---
st.set_page_config(page_title="Expert Social Pro 2026", layout="wide", page_icon="⚖️")

def check_password():
    """Vérifie le mot de passe."""
    if st.session_state.get("password_correct"):
        return True

    # Pour l'écran de login, on garde le design de base
    set_design('background.webp', '#024c6f')
    st.markdown("<h1 style='text-align: center; color: white; margin-top: 100px;'>🔐 Accès Expert Réservé</h1>", unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        password = st.text_input("Veuillez saisir le code d'accès :", type="password")
        if st.button("Se connecter") or password:
            correct_pwd = os.getenv("APP_PASSWORD") or st.secrets.get("APP_PASSWORD")
            if password == correct_pwd:
                st.session_state["password_correct"] = True
                st.rerun()
            elif password:
                st.error("Mot de passe incorrect.")
    st.stop()

check_password()
# Activation du design complet (Image + Sidebar bleu foncé)
set_design('background.webp', '#024c6f')

# --- 4. CHARGEMENT IA (Lazy Loading) ---
@st.cache_resource
def load_system():
    from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAIEmbeddings
    from langchain_chroma import Chroma
    
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        return None, None

    embeddings = GoogleGenerativeAIEmbeddings(model="models/text-embedding-004")
    vectorstore = Chroma(persist_directory="chroma_db", embedding_function=embeddings)
    llm = ChatGoogleGenerativeAI(model="gemini-2.0-flash-exp", temperature=0)
    return vectorstore, llm

# --- 5. LOGIQUE PRINCIPALE ---
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough, RunnableParallel
from langchain_core.output_parsers import StrOutputParser

if not os.getenv("GOOGLE_API_KEY"):
    st.error("⚠️ Clé API GEMINI manquante.")
    st.stop()

vectorstore, llm = load_system()
if not vectorstore:
    st.error("Erreur de chargement du système.")
    st.stop()

retriever = vectorstore.as_retriever(search_kwargs={"k": 10})

prompt = ChatPromptTemplate.from_template("""
Tu es un assistant expert en droit social et paie français (Expert Social Pro 2026).
CONSIGNE : Ne suggère JAMAIS de vérifier le BOSS. Donne directement les chiffres et taux. 
IMPORTANT : Quand tu cites tes sources, utilise simplement le terme "BOSS" ou "Code du travail".

Contexte : {context}
Question : {question}

Réponse technique et précise :
""")

def format_source_name(name):
    if "BOSS" in name.upper(): return "BOSS"
    if "CODE" in name.upper() or "TRAVAIL" in name.upper() or "LEGITEXT" in name.upper(): return "Code du Travail"
    return "Source officielle"

rag_chain_with_sources = RunnableParallel(
    {"context": retriever, "question": RunnablePassthrough()}
).assign(answer= prompt | llm | StrOutputParser())

# --- 6. SIDEBAR (TEXTE UNIQUEMENT) ---
with st.sidebar:
    st.markdown("##") 
    st.markdown("### **Bienvenue sur votre expert social dédié.**")
    st.markdown("---")
    # Info box style (Streamlit natif, s'adapte au thème)
    st.info("📅 **Année Fiscale : 2026**\n\nBase à jour.")
    
    # ICI : J'ai supprimé st.button("Nouvelle conversation") qui créait le module blanc
    
    st.markdown("---")
    st.caption("Expert Social Pro ©BusinessAgentAi")

# --- 7. HEADER & LAYOUT (Capture 2) ---
col_logo, col_title, col_btn1, col_btn2 = st.columns([0.8, 5, 1.5, 2], gap="small", vertical_alignment="center")

with col_logo:
    try: st.image("avatar-logo.png", width=80)
    except: st.write("⚖️")

with col_title:
    st.markdown("<h1 style='color: white; margin: 0; padding: 0; font-size: 2.5rem;'>Expert Social Pro 2026</h1>", unsafe_allow_html=True)

with col_btn1:
    if st.button("Nouvelle conversation", use_container_width=True):
        st.session_state.messages = []
        st.rerun()

with col_btn2:
    st.button("Télécharger un document pour analyse", use_container_width=True)

st.markdown("---")

# --- 8. CHAT ---
if "messages" not in st.session_state:
    st.session_state.messages = []

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

if query := st.chat_input("Posez votre question technique ici..."):
    st.session_state.messages.append({"role": "user", "content": query})
    with st.chat_message("user"):
        st.markdown(query)
    
    with st.chat_message("assistant"):
        with st.spinner("Analyse..."):
            try:
                response = rag_chain_with_sources.invoke(query)
                st.markdown(response["answer"])
                
                with st.expander("📚 Sources utilisées"):
                    for i, doc in enumerate(response["context"]):
                        source_display = format_source_name(doc.metadata.get("source", ""))
                        st.markdown(f"**Source {i+1} : {source_display}**")
                        st.caption(doc.page_content)
                st.session_state.messages.append({"role": "assistant", "content": response["answer"]})
            except Exception as e:
                st.error(f"Une erreur est survenue lors de l'analyse : {e}")
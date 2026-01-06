# --- 1. CONFIGURATION SQLITE ET PATCH ---
import sys
import os
import base64 
import streamlit as st
import pypdf 
import uuid 
from langchain_text_splitters import RecursiveCharacterTextSplitter 

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
        .stApp {{
            background-image: url("data:image/{extension};base64,{bin_str}");
            background-size: cover;
            background-repeat: no-repeat;
            background-attachment: fixed;
        }}
        [data-testid="stToolbar"] {{ visibility: hidden; height: 0%; }}
        [data-testid="stDecoration"] {{ visibility: hidden; height: 0%; }}
        header {{ background-color: transparent !important; }}
        [data-testid="stSidebar"] > div:first-child {{ background-color: {sidebar_color}; }}
        [data-testid="stSidebar"] * {{ color: white !important; }}
        .block-container {{ padding-top: 2rem !important; }}
        .main .stButton > button {{
            background-color: rgba(255, 255, 255, 0.1) !important;
            color: white !important;
            border: 1px solid white !important;
            border-radius: 8px !important;
            height: 45px !important;
            font-weight: 500 !important;
            width: 100% !important;
        }}
        .main .stButton > button:hover {{
            background-color: rgba(255, 255, 255, 0.3) !important;
            border-color: white !important;
        }}
        .stChatMessage {{
            background-color: rgba(255, 255, 255, 0.95);
            border-radius: 15px;
            padding: 10px;
            margin-bottom: 10px;
        }}
        .stChatMessage p, .stChatMessage li {{ color: black !important; }}
        [data-testid="stExpander"] {{
            background-color: rgba(255, 255, 255, 0.9);
            border-radius: 10px;
            border: none;
        }}
        </style>
        '''
        st.markdown(page_bg_img, unsafe_allow_html=True)
    except FileNotFoundError:
        pass

# --- 3. CONFIGURATION PAGE & AUTHENTIFICATION ---
st.set_page_config(page_title="Expert Social Pro 2026", layout="wide", page_icon="⚖️")

def check_password():
    if st.session_state.get("password_correct"):
        return True
    set_design('background.webp', '#024c6f')
    st.markdown("<h1 style='text-align: center; color: white; margin-top: 100px;'>🔐 Accès Expert Réservé</h1>", unsafe_allow_html=True)
    col_a, col_b, col_c = st.columns([1, 2, 1])
    with col_b:
        password = st.text_input("Saisissez le code d'accès :", type="password")
        if st.button("Se connecter") or password:
            correct_pwd = os.getenv("APP_PASSWORD") or st.secrets.get("APP_PASSWORD")
            if password == correct_pwd:
                st.session_state["password_correct"] = True
                st.rerun()
            elif password:
                st.error("Mot de passe incorrect.")
    st.stop()

check_password()
set_design('background.webp', '#003366')

# --- 4. CHARGEMENT SYSTÈME IA ---
@st.cache_resource
def load_system():
    from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAIEmbeddings
    from langchain_chroma import Chroma
    api_key = os.getenv("GOOGLE_API_KEY") or st.secrets.get("GOOGLE_API_KEY")
    if not api_key:
        return None, None
    embeddings = GoogleGenerativeAIEmbeddings(
        model="models/text-embedding-004",
        google_api_key=api_key
    )
    vectorstore = Chroma(persist_directory="chroma_db", embedding_function=embeddings)
    llm = ChatGoogleGenerativeAI(
        model="gemini-2.0-flash-exp", 
        temperature=0,
        google_api_key=api_key
    )
    return vectorstore, llm

# --- 5. LOGIQUE RAG ET PROMPT EXPERT ---
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough, RunnableParallel
from langchain_core.output_parsers import StrOutputParser

vectorstore, llm = load_system()
if not vectorstore:
    st.error("⚠️ Erreur : Clé API manquante ou invalide.")
    st.stop()

retriever = vectorstore.as_retriever(search_kwargs={"k": 10})

prompt = ChatPromptTemplate.from_template("""
Tu es Expert Social Pro 2026, un assistant spécialisé pour les gestionnaires de paie et DRH.
CONSIGNES DE RÉPONSE :
1. Réponds toujours sous forme de liste à puces pour les conditions techniques.
2. Cite tes sources précisément (ex: BOSS, Code du travail).

Contexte : {context}
Question : {question}

Réponse technique et précise :
""")

rag_chain_with_sources = RunnableParallel(
    {"context": retriever, "question": RunnablePassthrough()}
).assign(answer= prompt | llm | StrOutputParser())

# --- 6. SIDEBAR ---
with st.sidebar:
    st.markdown("##") 
    st.markdown("### **Bienvenue sur SocialPro2026**")
    st.markdown("---")
    st.info("📅 **Base 2026 à jour**\n\nIncluant le BOSS et le Code du Travail.")
    st.markdown("---")
    st.caption("©BusinessAgentAi")

# --- 7. HEADER ET ANALYSE DE DOCUMENTS ---
def process_file(uploaded_file):
    try:
        if uploaded_file.name.endswith('.pdf'):
            reader = pypdf.PdfReader(uploaded_file)
            text = "\n".join([p.extract_text() for p in reader.pages if p.extract_text()])
        else:
            text = uploaded_file.read().decode("utf-8")
        if not text: return None
        text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=100)
        chunks = text_splitter.split_text(text)
        return vectorstore.add_texts(texts=chunks, metadatas=[{"source": uploaded_file.name} for _ in chunks])
    except: return None

if 'doc_ids' not in st.session_state: st.session_state['doc_ids'] = []
if 'uploader_key' not in st.session_state: st.session_state['uploader_key'] = str(uuid.uuid4())

col_logo, col_title, col_btn = st.columns([1, 5, 2], vertical_alignment="center")
with col_logo:
    if os.path.exists("avatar-logo.png"): st.image("avatar-logo.png", width=80)
with col_title:
    st.markdown("<h1 style='color: white; margin: 0; font-size: 2.5rem;'>Expert Social Pro 2026</h1>", unsafe_allow_html=True)
with col_btn:
    if st.button("Nouvelle conversation", use_container_width=True):
        if st.session_state['doc_ids']:
            try: vectorstore.delete(ids=st.session_state['doc_ids'])
            except: pass
        st.session_state['doc_ids'] = []
        st.session_state.messages = []
        st.session_state['uploader_key'] = str(uuid.uuid4())
        st.rerun()

st.markdown("---")

# --- 8. CHAT INTERFACE ---
if "messages" not in st.session_state:
    st.session_state.messages = []

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

if query := st.chat_input("Votre question technique..."):
    st.session_state.messages.append({"role": "user", "content": query})
    with st.chat_message("user"):
        st.markdown(query)
    
    with st.chat_message("assistant"):
        with st.spinner("Expertise en cours..."):
            response = rag_chain_with_sources.invoke(query)
            st.markdown(response["answer"])
            
            # BLOC SOURCES : AFFICHAGE BRUT ET COMPLET SANS NETTOYAGE
            st.markdown("### 📚 Sources utilisées")
            for i, doc in enumerate(response["context"]):
                source_name = doc.metadata.get('source', 'Source inconnue')
                st.markdown(f"**Source {i+1} : {source_name}**")
                st.write(doc.page_content)
                st.markdown("---")
            
            st.session_state.messages.append({"role": "assistant", "content": response["answer"]})
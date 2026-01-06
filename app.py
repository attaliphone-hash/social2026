# --- 1. CONFIGURATION SQLITE ET PATCH ---
import sys
import os

try:
    import pysqlite3
    sys.modules['sqlite3'] = pysqlite3
except ImportError:
    pass

import base64 
import streamlit as st
import pypdf 
import uuid 
from langchain_text_splitters import RecursiveCharacterTextSplitter 

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
        .stChatMessage {{
            background-color: rgba(255, 255, 255, 0.95);
            border-radius: 15px;
            padding: 10px;
            margin-bottom: 10px;
        }}
        .stChatMessage p, .stChatMessage li {{ color: black !important; }}
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

# Augmentation du K pour assurer la visibilité du document téléversé
retriever = vectorstore.as_retriever(search_kwargs={"k": 25})

prompt = ChatPromptTemplate.from_template("""
Tu es Expert Social Pro 2026, spécialisé en audit juridique.

CONTEXTE : {context}
QUESTION : {question}

CONSIGNES CRITIQUES :
1. ANALYSE PRIORITAIRE : Tu DOIS utiliser les extraits identifiés comme "VOTRE DOCUMENT". 
2. CONFRONTATION : Compare ligne par ligne le contenu de "VOTRE DOCUMENT" avec les règles du "CODE DU TRAVAIL" ou "BOSS" présentes dans le contexte.
3. RÉSULTAT : Liste ce qui est conforme, ce qui est manquant (ex: mentions obligatoires) et ce qui présente un risque.
4. ABSENCE DE DOC : Si aucun extrait ne commence par "VOTRE DOCUMENT", signale que tu ne peux pas analyser de fichier spécifique.

Réponse technique (exclusivement en listes à puces) :
""")

rag_chain_with_sources = RunnableParallel(
    {"context": retriever, "question": RunnablePassthrough()}
).assign(answer= prompt | llm | StrOutputParser())

# --- 6. SIDEBAR ---
with st.sidebar:
    st.markdown("### **SocialPro2026**")
    st.info("📅 **Base 2026 à jour**")
    st.caption("©BusinessAgentAi")

# --- 7. TRAITEMENT ROBUSTE DES DOCUMENTS ---
def process_file(uploaded_file):
    try:
        text = ""
        if uploaded_file.name.endswith('.pdf'):
            reader = pypdf.PdfReader(uploaded_file)
            for page in reader.pages:
                extracted = page.extract_text()
                if extracted: text += extracted + "\n"
        else:
            text = uploaded_file.read().decode("utf-8")
        
        if not text or len(text.strip()) < 20:
            return "ERROR_EMPTY"
            
        text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=100)
        chunks = text_splitter.split_text(text)
        
        # Marquage explicite de la source pour le retriever
        metadatas = [{"source": f"VOTRE DOCUMENT : {uploaded_file.name}"} for _ in chunks]
        return vectorstore.add_texts(texts=chunks, metadatas=metadatas)
    except Exception as e:
        return None

if 'doc_ids' not in st.session_state: st.session_state['doc_ids'] = []
if 'uploader_key' not in st.session_state: st.session_state['uploader_key'] = str(uuid.uuid4())

# --- 8. INTERFACE ET CHAT ---
col_logo, col_title, col_btn = st.columns([1, 5, 2], vertical_alignment="center")
with col_logo:
    if os.path.exists("avatar-logo.png"): st.image("avatar-logo.png", width=80)
with col_title:
    st.markdown("<h1 style='color: white; margin: 0;'>Expert Social Pro 2026</h1>", unsafe_allow_html=True)
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

with st.expander("📎 Analyser un document externe (PDF/TXT)", expanded=False):
    uploaded_file = st.file_uploader("Fichier", type=["pdf", "txt"], key=st.session_state['uploader_key'])
    if uploaded_file and uploaded_file.name not in st.session_state.get('history', []):
        with st.spinner("Analyse du texte en cours..."):
            res = process_file(uploaded_file)
            if res == "ERROR_EMPTY":
                st.error("Le PDF semble être une image (scan). L'extraction de texte est impossible sans OCR.")
            elif res:
                st.session_state['doc_ids'].extend(res)
                if 'history' not in st.session_state: st.session_state['history'] = []
                st.session_state['history'].append(uploaded_file.name)
                st.success(f"Document '{uploaded_file.name}' prêt pour l'analyse !")
                st.rerun()

if "messages" not in st.session_state: st.session_state.messages = []
for message in st.session_state.messages:
    with st.chat_message(message["role"]): st.markdown(message["content"])

if query := st.chat_input("Posez votre question sur le document ou la loi..."):
    st.session_state.messages.append({"role": "user", "content": query})
    with st.chat_message("user"): st.markdown(query)
    
    with st.chat_message("assistant"):
        with st.spinner("Expertise en cours..."):
            response = rag_chain_with_sources.invoke(query)
            st.markdown(response["answer"])
            
            with st.expander("📚 Sources et extraits analysés"):
                for doc in response["context"]:
                    src = doc.metadata.get('source', '').upper()
                    label = "BOSS" if "BOSS" in src else "CODE DU TRAVAIL" if "CODE" in src else "MÉMO 2026" if "MEMO" in src else src
                    st.markdown(f"**Source : {label}**")
                    st.caption(doc.page_content)
                    st.markdown("---")
            
            st.session_state.messages.append({"role": "assistant", "content": response["answer"]})
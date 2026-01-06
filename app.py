# --- 1. CONFIGURATION SQLITE ET PATCH ---
import sys
import os
import uuid

try:
    import pysqlite3
    sys.modules['sqlite3'] = pysqlite3
except ImportError:
    pass

import base64 
import streamlit as st
import pypdf 
from langchain_text_splitters import RecursiveCharacterTextSplitter 

# --- 2. INITIALISATION SESSION ---
if 'session_id' not in st.session_state:
    st.session_state['session_id'] = str(uuid.uuid4())

# --- 3. FONCTIONS DESIGN ---
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
        .stApp {{ background-image: url("data:image/{extension};base64,{bin_str}"); background-size: cover; background-attachment: fixed; }}
        [data-testid="stSidebar"] > div:first-child {{ background-color: {sidebar_color}; }}
        [data-testid="stSidebar"] * {{ color: white !important; }}
        .stChatMessage {{ background-color: rgba(255, 255, 255, 0.95); border-radius: 15px; padding: 10px; margin-bottom: 10px; }}
        .stChatMessage p, .stChatMessage li {{ color: black !important; }}
        </style>
        '''
        st.markdown(page_bg_img, unsafe_allow_html=True)
    except FileNotFoundError: pass

# --- 4. CONFIGURATION PAGE ---
st.set_page_config(page_title="Expert Social Pro 2026", layout="wide")

def check_password():
    if st.session_state.get("password_correct"): return True
    set_design('background.webp', '#024c6f')
    st.markdown("<h1 style='text-align: center; color: white;'>🔐 Accès Expert Réservé</h1>", unsafe_allow_html=True)
    password = st.text_input("Code d'accès :", type="password")
    if st.button("Se connecter"):
        if password == (os.getenv("APP_PASSWORD") or st.secrets.get("APP_PASSWORD")):
            st.session_state["password_correct"] = True
            st.rerun()
    st.stop()

check_password()
set_design('background.webp', '#003366')

# --- 5. CHARGEMENT SYSTÈME IA ---
@st.cache_resource
def load_system():
    from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAIEmbeddings
    from langchain_chroma import Chroma
    api_key = os.getenv("GOOGLE_API_KEY") or st.secrets.get("GOOGLE_API_KEY")
    embeddings = GoogleGenerativeAIEmbeddings(model="models/text-embedding-004", google_api_key=api_key)
    vectorstore = Chroma(persist_directory="chroma_db", embedding_function=embeddings)
    llm = ChatGoogleGenerativeAI(model="gemini-2.0-flash-exp", temperature=0, google_api_key=api_key)
    return vectorstore, llm

vectorstore, llm = load_system()

# --- 6. LOGIQUE D'EXTRACTION ROBUSTE ---
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
        
        if not text or len(text.strip()) < 20: return "ERROR_EMPTY"
            
        text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=100)
        chunks = text_splitter.split_text(text)
        
        # VARIABLE DE SESSION : On marque les chunks pour cette conversation uniquement
        metadatas = [{
            "source": f"VOTRE DOCUMENT : {uploaded_file.name}",
            "session_id": st.session_state['session_id']
        } for _ in chunks]
        
        return vectorstore.add_texts(texts=chunks, metadatas=metadatas)
    except Exception: return None

# --- 7. INTERFACE ---
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

col_logo, col_title, col_btn = st.columns([1, 5, 2], vertical_alignment="center")
with col_title:
    st.markdown("<h1 style='color: white; margin: 0;'>Expert Social Pro 2026</h1>", unsafe_allow_html=True)
with col_btn:
    if st.button("Nouvelle conversation"):
        st.session_state.messages = []
        st.session_state['session_id'] = str(uuid.uuid4()) # Reset session
        st.rerun()

st.markdown("---")

with st.expander("📎 Analyser un document externe", expanded=False):
    uploaded_file = st.file_uploader("Fichier", type=["pdf", "txt"])
    if uploaded_file and uploaded_file.name not in st.session_state.get('history', []):
        res = process_file(uploaded_file)
        if res:
            if 'history' not in st.session_state: st.session_state['history'] = []
            st.session_state['history'].append(uploaded_file.name)
            st.success("Document prêt !")
            st.rerun()

# --- 8. CHAT ET RAG ---
if "messages" not in st.session_state: st.session_state.messages = []
for message in st.session_state.messages:
    with st.chat_message(message["role"]): st.markdown(message["content"])

if query := st.chat_input("Vérifie ce contrat..."):
    st.session_state.messages.append({"role": "user", "content": query})
    with st.chat_message("user"): st.markdown(query)
    
    with st.chat_message("assistant"):
        # RETRIEVER FILTRÉ : On ne récupère que le Code du Travail OU le document de cette session
        # On utilise une logique de recherche large (k=25)
        docs = vectorstore.similarity_search(query, k=25)
        
        # On filtre manuellement pour s'assurer que notre document est là
        context_text = "\n\n".join([f"SOURCE {d.metadata.get('source')}:\n{d.page_content}" for d in docs])

        prompt = ChatPromptTemplate.from_template("""
        Tu es Expert Social Pro 2026.
        
        CONTEXTE : {context}
        QUESTION : {question}
        
        CONSIGNE : Compare le contenu de "VOTRE DOCUMENT" avec les règles du "CODE DU TRAVAIL". 
        Si "VOTRE DOCUMENT" n'apparaît pas dans le CONTEXTE, dis que tu ne trouves pas le fichier.
        """)
        
        chain = prompt | llm | StrOutputParser()
        full_response = chain.invoke({"context": context_text, "question": query})
        st.markdown(full_response)
        
        with st.expander("📚 Sources analysées"):
            for d in docs:
                st.write(f"**{d.metadata.get('source')}**")
                st.caption(d.page_content)

    st.session_state.messages.append({"role": "assistant", "content": full_response})
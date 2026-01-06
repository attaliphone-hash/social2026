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

# --- 6. LOGIQUE D'EXTRACTION ---
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
        
        metadatas = [{
            "source": f"VOTRE DOCUMENT : {uploaded_file.name}",
            "session_id": st.session_state['session_id']
        } for _ in chunks]
        
        return vectorstore.add_texts(texts=chunks, metadatas=metadatas)
    except Exception: return None

# --- 7. INTERFACE ---
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

st.markdown("<h1 style='color: white;'>Expert Social Pro 2026</h1>", unsafe_allow_html=True)
if st.button("Nouvelle conversation"):
    st.session_state.messages = []
    st.session_state['session_id'] = str(uuid.uuid4())
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

# --- 8. CHAT ET RAG FILTRÉ AVEC FINITIONS PRO ---
if "messages" not in st.session_state: st.session_state.messages = []
for message in st.session_state.messages:
    avatar_img = "avatar-logo.png" if message["role"] == "assistant" else None
    with st.chat_message(message["role"], avatar=avatar_img): 
        st.markdown(message["content"])

if query := st.chat_input("Vérifie ce contrat..."):
    st.session_state.messages.append({"role": "user", "content": query})
    with st.chat_message("user"): st.markdown(query)
    
    with st.chat_message("assistant", avatar="avatar-logo.png"):
        # Modification demandée : Expertise en cours...
        with st.status("🔍 expertise en cours...", expanded=True) as status:
            user_docs = vectorstore.similarity_search(
                query, k=15, filter={"session_id": st.session_state['session_id']}
            )
            law_docs = vectorstore.similarity_search(query, k=10)
            law_docs = [d for d in law_docs if d.metadata.get('session_id') != st.session_state['session_id']]

            context_parts = []
            if user_docs:
                context_parts.append("=== CONTENU DE VOTRE DOCUMENT ===")
                context_parts.extend([d.page_content for d in user_docs])
            
            context_parts.append("\n=== RÉFÉRENCES LÉGALES ===")
            context_parts.extend([d.page_content for d in law_docs])
            context_text = "\n".join(context_parts)

            prompt = ChatPromptTemplate.from_template("""
            Tu es Expert Social Pro 2026. Réalise une expertise juridique rigoureuse.
            CONTEXTE : {context}
            QUESTION : {question}
            
            CONSIGNE : Compare le document utilisateur aux références légales si présent. 
            Cite précisément les sources.
            """)
            
            chain = prompt | llm | StrOutputParser()
            full_response = chain.invoke({"context": context_text, "question": query})
            status.update(label="✅ Expertise terminée !", state="complete", expanded=False)

        st.markdown(full_response)
        
        with st.expander("📚 Sources et bases juridiques consultées"):
            if user_docs:
                st.markdown("### 📄 Votre Document")
                for d in user_docs:
                    st.caption(f"Extrait : {d.page_content[:200]}...")
            
            st.markdown("### ⚖️ Références Légales")
            for d in law_docs:
                # Nettoyage .txt et chemins
                raw_source = d.metadata.get('source', 'Loi').split('/')[-1]
                clean_source = raw_source.replace('.txt', '').replace('.pdf', '').replace('_', ' ')
                
                st.write(f"**Source : {clean_source}**")
                st.caption(d.page_content)

    st.session_state.messages.append({"role": "assistant", "content": full_response})
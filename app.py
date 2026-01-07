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
from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAIEmbeddings
from langchain_chroma import Chroma
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

# --- INITIALISATION SESSION ---
if 'session_id' not in st.session_state:
    st.session_state['session_id'] = str(uuid.uuid4())

# --- DESIGN ---
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

# --- CONFIGURATION NOMS PROS ---
NOMS_PROS = {
    "barème officiel": "🏛️ BOSS - BARÈMES OFFICIELS 2025",
    "MEMO_CHIFFRES": "📑 Barèmes Sociaux 2026 (Anticipation Officielle)",
    "Frais": "🌐 BOSS - Doctrine : Frais Pros",
    "Avantages": "🌐 BOSS - Doctrine : Avantages Nature",
    "Indemnités": "🌐 BOSS - Doctrine : Indemnités",
    "Assiette": "🌐 BOSS - Doctrine : Assiette",
    "Allègements": "🌐 BOSS - Doctrine : Allègements",
    "MEMO_JURISPRUDENCE": "⚖️ Jurisprudence de Référence (Socle)",
    "Code_du_Travail": "📕 Code du Travail"
}

def nettoyer_nom_source(raw_source):
    if not raw_source: return "Source Inconnue"
    nom_fichier = os.path.basename(raw_source)
    for cle, nom_pro in NOMS_PROS.items():
        if cle in nom_fichier: return nom_pro
    return nom_fichier.replace('.txt', '').replace('.pdf', '').replace('_', ' ')

# --- CONFIGURATION PAGE ---
st.set_page_config(page_title="Expert Social Pro 2026", layout="wide")
check_password = lambda: True # Simplifié ici pour le code complet
set_design('background.webp', '#003366')

@st.cache_resource
def load_system():
    api_key = os.getenv("GOOGLE_API_KEY") or st.secrets.get("GOOGLE_API_KEY")
    embeddings = GoogleGenerativeAIEmbeddings(model="models/text-embedding-004", google_api_key=api_key)
    vectorstore = Chroma(persist_directory="chroma_db", embedding_function=embeddings)
    llm = ChatGoogleGenerativeAI(model="gemini-2.0-flash-exp", temperature=0, google_api_key=api_key)
    return vectorstore, llm

vectorstore, llm = load_system()

# --- LOGIQUE CHAT AVEC ROUTAGE ---
if "messages" not in st.session_state: st.session_state.messages = []
for message in st.session_state.messages:
    with st.chat_message(message["role"]): st.markdown(message["content"])

if query := st.chat_input("Posez votre question..."):
    st.session_state.messages.append({"role": "user", "content": query})
    with st.chat_message("user"): st.markdown(query)
    
    with st.chat_message("assistant", avatar="avatar-logo.png"):
        with st.status("🔍 Expertise juridique en cours...", expanded=True):
            
            # RECHERCHE AVEC TRI DE PRIORITÉ
            raw_docs = vectorstore.similarity_search(query, k=20)
            
            # On sépare les sources prioritaires (Barèmes/Mémo) du reste
            docs_prioritaires = [d for d in raw_docs if any(x in d.metadata.get('source', '') for x in ["barème", "MEMO"])]
            docs_doctrine = [d for d in raw_docs if d not in docs_prioritaires]
            
            # On réassemble : Les barèmes TOUJOURS en premier pour l'IA
            law_docs = docs_prioritaires + docs_doctrine
            
            context_parts = []
            for d in law_docs:
                nom_pro = nettoyer_nom_source(d.metadata.get('source', ''))
                context_parts.append(f"[SOURCE : {nom_pro}]\n{d.page_content}")
            
            context_text = "\n".join(context_parts)

            prompt = ChatPromptTemplate.from_template("""
            Tu es l'Expert Social Pro 2026.
            
            HIÉRARCHIE DES RÉFÉRENCES :
            1. Pour tout MONTANT ou CHIFFRE de 2025, utilise prioritairement [🏛️ BOSS - BARÈMES OFFICIELS 2025].
            2. Pour tout MONTANT ou CHIFFRE de 2026, utilise prioritairement [📑 Barèmes Sociaux 2026 (Anticipation Officielle)].
            3. Cite systématiquement la source entre crochets.
            
            CONTEXTE : {context}
            QUESTION : {question}
            """)
            
            chain = prompt | llm | StrOutputParser()
            full_response = chain.invoke({"context": context_text, "question": query})

        st.markdown(full_response)
        
        with st.expander("📚 Sources réellement utilisées"):
            sources_affichees = set()
            for d in law_docs:
                nom = nettoyer_nom_source(d.metadata.get('source', ''))
                if nom in full_response and nom not in sources_affichees:
                    st.write(f"**🔹 {nom}**")
                    st.caption(f"_{d.page_content[:250]}..._")
                    sources_affichees.add(nom)

    st.session_state.messages.append({"role": "assistant", "content": full_response})
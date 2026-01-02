import streamlit as st
import os
import sys
from dotenv import load_dotenv

# --- 1. CORRECTIF SQLITE POUR STREAMLIT CLOUD ---
try:
    __import__('pysqlite3')
    sys.modules['sqlite3'] = sys.modules.pop('pysqlite3')
except ImportError:
    pass

from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAIEmbeddings
from langchain_chroma import Chroma
from langchain.chains import create_retrieval_chain
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain_core.prompts import ChatPromptTemplate
import pypdf

# --- 2. CONFIGURATION DE LA PAGE ---
st.set_page_config(page_title="Social Pro 2026", page_icon="⚖️", layout="wide")

# Style CSS pour le design (coins arrondis)
st.markdown("""
<style>
    img { border-radius: 15px; margin-bottom: 20px; }
    .stButton button { border-radius: 20px; }
</style>
""", unsafe_allow_html=True)

# --- 3. CLÉ API & MOT DE PASSE ---
load_dotenv()
api_key = os.getenv("GOOGLE_API_KEY") or st.secrets.get("GOOGLE_API_KEY")

if not api_key:
    st.error("❌ Clé API Google manquante dans les Secrets.")
    st.stop()

if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

def check_password():
    if st.session_state.password_input == "social2026":
        st.session_state.authenticated = True
        del st.session_state.password_input
    else:
        st.error("Mot de passe incorrect")

if not st.session_state.authenticated:
    st.title("🔐 Accès Restreint - Social Pro")
    st.text_input("Mot de passe :", type="password", key="password_input", on_change=check_password)
    st.stop()

# --- 4. ANALYSE DE DOCUMENTS TÉLÉVERSÉS ---
def extract_text_from_upload(uploaded_file):
    text = ""
    try:
        if uploaded_file.type == "application/pdf":
            pdf_reader = pypdf.PdfReader(uploaded_file)
            for page in pdf_reader.pages:
                text += page.extract_text() + "\n"
        elif uploaded_file.type == "text/plain":
            text = uploaded_file.read().decode("utf-8")
    except Exception as e:
        return f"Erreur de lecture : {e}"
    return text

# --- 5. CHARGEMENT IA & BASE BOSS (LangChain) ---
@st.cache_resource
def load_chain():
    # Gemini 2.0 Flash Experimental
    llm = ChatGoogleGenerativeAI(
        model="gemini-2.0-flash-exp",
        temperature=0,
        google_api_key=api_key
    )
    
    # Embeddings conformes à ton build_db.py
    embeddings = GoogleGenerativeAIEmbeddings(
        model="models/text-embedding-004", 
        google_api_key=api_key
    )
    
    # Connexion à ton dossier chroma_db
    vectorstore = Chroma(
        persist_directory="./chroma_db", 
        embedding_function=embeddings
    )
    
    retriever = vectorstore.as_retriever(search_kwargs={"k": 5})

    system_instruction = """
    Tu es un assistant juridique expert en Droit Social (BOSS, Code du Travail, Code Sécu).
    
    RÈGLES :
    1. Cite TOUJOURS tes sources (ex: Article L.1234-9 ou Fiche BOSS).
    2. Si un DOCUMENT UTILISATEUR est présent ci-dessous, utilise-le pour personnaliser ta réponse.
    3. Ton ton est expert et direct.
    
    DOCUMENT UTILISATEUR : {user_doc}
    
    CONTEXTE JURIDIQUE :
    {context}
    """

    prompt = ChatPromptTemplate.from_messages([
        ("system", system_instruction),
        ("human", "{input}")
    ])

    document_chain = create_stuff_documents_chain(llm, prompt)
    return create_retrieval_chain(retriever, document_chain)

chain = load_chain()

# --- 6. SIDEBAR & DESIGN ---
with st.sidebar:
    st.header("👔 Social Pro 2026")
    st.image("https://images.unsplash.com/photo-1554224155-6726b3ff858f?auto=format&fit=crop&w=400&q=80")
    
    st.subheader("📂 Analyser une pièce")
    uploaded_file = st.file_uploader("Ajouter un PDF ou TXT", type=["pdf", "txt"])
    user_doc_content = "Aucun document fourni."
    if uploaded_file:
        user_doc_content = extract_text_from_upload(uploaded_file)
        st.success("✅ Document analysé")

    st.markdown("---")
    st.caption("Version : Social Pro 2026 V1")

# --- 7. CHAT PRINCIPAL ---
st.title("⚖️ Social Pro 2026")
st.caption("Expert BOSS & Codes Officiels")

if "messages" not in st.session_state:
    st.session_state.messages = []

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

if prompt := st.chat_input("Votre question juridique..."):
    st.chat_message("user").markdown(prompt)
    st.session_state.messages.append({"role": "user", "content": prompt})

    with st.chat_message("assistant"):
        with st.spinner("Recherche dans le BOSS et les Codes..."):
            try:
                response = chain.invoke({
                    "input": prompt,
                    "user_doc": user_doc_content
                })
                answer = response["answer"]
                st.markdown(answer)
                st.session_state.messages.append({"role": "assistant", "content": answer})
                st.rerun()
            except Exception as e:
                st.error(f"Une erreur est survenue : {e}")
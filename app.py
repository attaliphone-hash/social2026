import streamlit as st
import os
import tempfile
import base64
from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAIEmbeddings
from langchain_chroma import Chroma
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_community.document_loaders import PyPDFLoader, TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter

# --- CONFIGURATION DE LA PAGE ---
st.set_page_config(
    page_title="Expert Social Pro 2026",
    page_icon="⚖️",
    layout="wide"
)

# --- GESTION DU FOND D'ÉCRAN ---
def get_base64(bin_file):
    with open(bin_file, 'rb') as f:
        data = f.read()
    return base64.b64encode(data).decode()

def set_background(png_file):
    bin_str = get_base64(png_file)
    page_bg_img = '''
    <style>
    .stApp {
    background-image: url("data:image/png;base64,%s");
    background-size: cover;
    }
    </style>
    ''' % bin_str
    st.markdown(page_bg_img, unsafe_allow_html=True)

# Chargement du fond (support PNG ou WEBP)
if os.path.exists("background.png"):
    set_background("background.png")
elif os.path.exists("background.webp"):
    set_background("background.webp")

# --- STYLES CSS ---
st.markdown("""
<style>
    .main { background-color: transparent; }
    .stChatMessage { background-color: white; border-radius: 10px; padding: 15px; box-shadow: 0 2px 5px rgba(0,0,0,0.05); }
    .stButton>button { width: 100%; border-radius: 5px; }
    h1 { color: #2c3e50; }
</style>
""", unsafe_allow_html=True)

# --- INITIALISATION SESSION ---
if "session_id" not in st.session_state:
    st.session_state.session_id = os.urandom(4).hex()
if "messages" not in st.session_state:
    st.session_state.messages = []
if "uploader_key" not in st.session_state:
    st.session_state.uploader_key = 0

# --- CHARGEMENT DU CERVEAU (MODEL & DB) ---
api_key = os.getenv("GOOGLE_API_KEY")
if not api_key:
    st.error("❌ CLÉ API MANQUANTE. Vérifiez vos variables d'environnement.")
    st.stop()

# Modèle IA
llm = ChatGoogleGenerativeAI(
    model="gemini-2.0-flash-exp",
    temperature=0,
    api_key=api_key
)

# Base de données Vectorielle
embeddings = GoogleGenerativeAIEmbeddings(model="models/text-embedding-004", google_api_key=api_key)
vectorstore = Chroma(persist_directory="chroma_db", embedding_function=embeddings)

# --- BARRE LATÉRALE (UPLOAD) ---
with st.sidebar:
    st.image("avatar-logo.png", width=80)
    st.title("Expert Social 2026")
    st.markdown("---")
    
    # Upload fichier temporaire
    uploaded_file = st.file_uploader(
        "📎 Analyser un document (PDF/TXT)", 
        type=["pdf", "txt"],
        key=f"uploader_{st.session_state.uploader_key}"
    )
    
    if uploaded_file:
        with st.status("📥 Lecture en cours...", expanded=True):
            try:
                # Sauvegarde temporaire
                with tempfile.NamedTemporaryFile(delete=False, suffix=f".{uploaded_file.name.split('.')[-1]}") as tmp:
                    tmp.write(uploaded_file.getvalue())
                    tmp_path = tmp.name
                
                # Chargement selon le type
                if uploaded_file.name.endswith(".pdf"):
                    loader = PyPDFLoader(tmp_path)
                else:
                    loader = TextLoader(tmp_path)
                    
                docs = loader.load()
                
                # Ajout métadonnées (Session ID + Nom Source)
                for doc in docs:
                    doc.metadata["session_id"] = st.session_state.session_id
                    doc.metadata["source"] = f"📁 {uploaded_file.name}"
                
                # Découpage et Vectorisation
                text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=100)
                chunks = text_splitter.split_documents(docs)
                
                vectorstore.add_documents(chunks)
                
                os.unlink(tmp_path) # Nettoyage
                st.success("✅ Document mémorisé !")
                
            except Exception as e:
                st.error(f"Erreur : {e}")

    st.markdown("---")
    if st.button("🧹 Nouvelle Conversation"):
        st.session_state.messages = []
        st.session_state.uploader_key += 1
        st.rerun()

# --- INTERFACE DE CHAT ---
st.title("⚖️ Assistant Juridique & RH")
st.caption("Expertise fiable basée sur le Code du Travail, le BOSS et la Jurisprudence 2026.")

# Affichage de l'historique
for msg in st.session_state.messages:
    with st.chat_message(msg["role"], avatar="avatar-logo.png" if msg["role"] == "assistant" else None):
        st.markdown(msg["content"])

# --- LOGIQUE DE RÉPONSE ---
if query := st.chat_input("Posez votre question juridique..."):
    
    # 1. Message Utilisateur
    st.session_state.messages.append({"role": "user", "content": query})
    with st.chat_message("user"):
        st.markdown(query)

    # 2. Réponse IA
    with st.chat_message("assistant", avatar="avatar-logo.png"):
        with st.status("🔍 Analyse juridique en cours...", expanded=True) as status:
            
            # A. RECHERCHE DOCUMENTAIRE
            # Docs utilisateur (Session en cours uniquement)
            user_docs = vectorstore.similarity_search(
                query, k=10, filter={"session_id": st.session_state.session_id}
            )
            
            # Docs juridiques (Tout sauf session en cours)
            raw_law_docs = vectorstore.similarity_search(query, k=20)
            law_docs = [d for d in raw_law_docs if d.metadata.get("session_id") != st.session_state.session_id]

            # B. PRÉPARATION DU CONTEXTE
            context_text = ""
            
            if user_docs:
                context_text += "\n=== DOCUMENT UTILISATEUR ===\n"
                for d in user_docs:
                    context_text += d.page_content + "\n"
            
            context_text += "\n=== RÉFÉRENCES JURIDIQUES (LOI, BOSS, JURISPRUDENCE) ===\n"
            for d in law_docs:
                src = d.metadata.get('source', 'Source inconnue')
                context_text += f"[Source: {src}]\n{d.page_content}\n"

            # C. PROMPT
            prompt = ChatPromptTemplate.from_template("""
            Tu es Expert Social Pro 2026.
            CONTEXTE : {context}
            QUESTION : {question}
            
            CONSIGNE :
            - Compare le document utilisateur aux références légales si présent.
            - Cite précisément les sources utilisées (Code du Travail, BOSS, Jurisprudence).
            - Si la réponse n'est pas dans le contexte, dis-le.
            """)
            
            chain = prompt | llm | StrOutputParser()
            full_response = chain.invoke({"context": context_text, "question": query})
            
            status.update(label="✅ Expertise terminée !", state="complete", expanded=False)

        st.markdown(full_response)
        
        # D. AFFICHAGE DES SOURCES (Version Standard)
        with st.expander("📚 Sources et bases juridiques consultées"):
            if user_docs:
                st.markdown("### 📄 Votre Document")
                for d in user_docs:
                    st.caption(f"Extrait : {d.page_content[:200]}...")
            
            st.markdown("### ⚖️ Références Légales")
            sources_vues = set()
            for d in law_docs:
                src = d.metadata.get('source', 'Inconnue')
                # Petit nettoyage visuel simple pour éviter les chemins complets moches
                src_clean = os.path.basename(src).replace('.txt', '').replace('.pdf', '').replace('_', ' ')
                
                if src_clean not in sources_vues:
                    st.write(f"**Source : {src_clean}**")
                    st.caption(d.page_content[:300] + "...")
                    sources_vues.add(src_clean)

    st.session_state.messages.append({"role": "assistant", "content": full_response})
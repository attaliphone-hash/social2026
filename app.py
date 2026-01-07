import sys
import os
import uuid
import base64 
import streamlit as st
import pypdf 

# --- 1. PATCH SQLITE POUR CLOUD RUN ---
try:
    import pysqlite3
    sys.modules['sqlite3'] = pysqlite3
except ImportError:
    pass

from langchain_text_splitters import RecursiveCharacterTextSplitter 
from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAIEmbeddings
from langchain_chroma import Chroma
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

# --- 2. CONFIGURATION PAGE ---
st.set_page_config(page_title="Expert Social Pro 2026", layout="wide")

# --- 3. DESIGN PRO (Zéro bandeau blanc / Menu masqué) ---
def get_base64(bin_file):
    if os.path.exists(bin_file):
        with open(bin_file, 'rb') as f:
            return base64.b64encode(f.read()).decode()
    return ""

def apply_pro_design():
    st.markdown("""
        <style>
        #MainMenu {visibility: hidden;}
        header {visibility: hidden !important; height: 0px;}
        footer {visibility: hidden;}
        [data-testid="stHeader"] {display: none;}
        .block-container { padding-top: 1rem !important; }
        .stApp { margin-top: -60px; } 
        
        /* Style des bulles de chat */
        .stChatMessage { background-color: rgba(255, 255, 255, 0.95); border-radius: 15px; padding: 10px; margin-bottom: 10px; border: 1px solid #e0e0e0; }
        .stChatMessage p, .stChatMessage li { color: black !important; font-size: 16px; }
        .stExpander details summary p { color: white !important; font-weight: bold; }
        </style>
    """, unsafe_allow_html=True)
    
    bg_data = get_base64('background.webp')
    if bg_data:
        st.markdown(f"""
            <style>
            .stApp {{ background-image: url("data:image/webp;base64,{bg_data}"); background-size: cover; background-attachment: fixed; }}
            </style>
        """, unsafe_allow_html=True)

# --- 4. SÉCURITÉ ACCÈS ---
def check_password():
    if st.session_state.get("password_correct"): return True
    apply_pro_design()
    st.markdown("<br><br><br><br>", unsafe_allow_html=True)
    st.markdown("<h1 style='text-align: center; color: white;'>🔐 Accès Expert Réservé</h1>", unsafe_allow_html=True)
    col_l, col_m, col_r = st.columns([1, 2, 1])
    with col_m:
        pwd = st.text_input("Veuillez saisir votre code d'accès :", type="password")
        if st.button("Déverrouiller"):
            valid_pwd = os.getenv("APP_PASSWORD") or st.secrets.get("APP_PASSWORD")
            if pwd == str(valid_pwd):
                st.session_state["password_correct"] = True
                st.rerun()
            else: st.error("Code incorrect.")
    st.stop()

check_password()
apply_pro_design()

# --- 5. INITIALISATION IA & DICTIONNAIRE ---
if 'session_id' not in st.session_state: st.session_state['session_id'] = str(uuid.uuid4())

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

@st.cache_resource
def load_system():
    api_key = os.getenv("GOOGLE_API_KEY") or st.secrets.get("GOOGLE_API_KEY")
    embeddings = GoogleGenerativeAIEmbeddings(model="models/text-embedding-004", google_api_key=api_key)
    vectorstore = Chroma(persist_directory="chroma_db", embedding_function=embeddings)
    llm = ChatGoogleGenerativeAI(model="gemini-2.0-flash-exp", temperature=0, google_api_key=api_key)
    return vectorstore, llm

vectorstore, llm = load_system()

# --- 6. GESTION DES DOCUMENTS UTILISATEURS ---
def process_file(uploaded_file):
    try:
        text = ""
        if uploaded_file.name.endswith('.pdf'):
            reader = pypdf.PdfReader(uploaded_file)
            for page in reader.pages:
                extracted = page.extract_text()
                if extracted: text += extracted + "\n"
        else: text = uploaded_file.read().decode("utf-8")
        if not text or len(text.strip()) < 20: return None
        text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=100)
        chunks = text_splitter.split_text(text)
        metadatas = [{"source": f"VOTRE DOCUMENT : {uploaded_file.name}", "session_id": st.session_state['session_id']} for _ in chunks]
        return vectorstore.add_texts(texts=chunks, metadatas=metadatas)
    except Exception: return None

# --- 7. INTERFACE PRINCIPALE ---
col_t, col_b = st.columns([4, 1])
with col_t: st.markdown("<h1 style='color: white;'>Expert Social Pro 2026</h1>", unsafe_allow_html=True)
with col_b:
    if st.button("Nouvelle conversation"):
        st.session_state.messages = []
        st.session_state['session_id'] = str(uuid.uuid4())
        st.rerun()

st.markdown("---")
with st.expander("📎 Analyser un document externe", expanded=False):
    uploaded_file = st.file_uploader("Fichier (PDF ou TXT)", type=["pdf", "txt"])
    if uploaded_file and uploaded_file.name not in st.session_state.get('history', []):
        if process_file(uploaded_file):
            if 'history' not in st.session_state: st.session_state['history'] = []
            st.session_state['history'].append(uploaded_file.name)
            st.success("Document analysé avec succès !")
            st.rerun()

# --- 8. MOTEUR DE CHAT ET RAG PRIORITAIRE ---
if "messages" not in st.session_state: st.session_state.messages = []
for message in st.session_state.messages:
    with st.chat_message(message["role"], avatar=("avatar-logo.png" if message["role"] == "assistant" else None)):
        st.markdown(message["content"])

if query := st.chat_input("Posez votre question juridique ou sociale..."):
    st.session_state.messages.append({"role": "user", "content": query})
    with st.chat_message("user"): st.markdown(query)
    
    with st.chat_message("assistant", avatar="avatar-logo.png"):
        with st.status("🔍 Analyse en cours...", expanded=True):
            # Recherche filtrée session
            user_docs = vectorstore.similarity_search(query, k=10, filter={"session_id": st.session_state['session_id']})
            # Recherche base globale
            raw_law = vectorstore.similarity_search(query, k=25)
            law_docs = [d for d in raw_law if d.metadata.get('session_id') != st.session_state['session_id']]
            
            # --- TRI DE PRIORITÉ (OBJECTIF 2) ---
            prioritaires = [d for d in law_docs if any(x in d.metadata.get('source', '') for x in ["barème", "MEMO"])]
            autres = [d for d in law_docs if d not in prioritaires]
            final_docs = prioritaires + autres
            
            # Construction du contexte
            context = []
            if user_docs:
                context.append("=== DOC UTILISATEUR ===\n" + "\n".join([d.page_content for d in user_docs]))
            context.append("=== RÉFÉRENCES LÉGALES ===\n" + "\n".join([f"[SOURCE : {nettoyer_nom_source(d.metadata.get('source',''))}]\n{d.page_content}" for d in final_docs]))

            prompt = ChatPromptTemplate.from_template("""
            Tu es l'Expert Social Pro 2026. Réponds avec précision.
            
            RÈGLES DE RÉFÉRENCE (OBJECTIF 3) :
            1. Pour les données de 2025, utilise prioritairement [🏛️ BOSS - BARÈMES OFFICIELS 2025]. 
            2. Pour les données de 2026, utilise prioritairement [📑 Barèmes Sociaux 2026 (Anticipation Officielle)].
            3. Ne dis jamais que l'info est manquante si elle est présente dans les références légales ci-jointes.
            
            CONSIGNE : Cite la source entre crochets pour chaque montant.
            CONTEXTE : {context}
            QUESTION : {question}
            """)
            
            full_response = (prompt | llm | StrOutputParser()).invoke({"context": "\n".join(context), "question": query})

        st.markdown(full_response)
        with st.expander("📚 Sources réellement utilisées"):
            used = set()
            if user_docs: st.write("**📄 Votre document**")
            for d in final_docs:
                nom = nettoyer_nom_source(d.metadata.get('source', ''))
                if nom in full_response and nom not in used:
                    st.write(f"**🔹 {nom}**")
                    used.add(nom)

    st.session_state.messages.append({"role": "assistant", "content": full_response})
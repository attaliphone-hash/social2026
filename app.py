import sys
import os
import uuid
import base64 
import requests 
from bs4 import BeautifulSoup 
import streamlit as st
import pypdf 

# --- 1. PATCH SQLITE ---
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

# --- FONCTION WATCHDOG BOSS ---
def check_boss_updates():
    url = "https://boss.gouv.fr/portail/accueil/actualites.html"
    try:
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
        response = requests.get(url, headers=headers, timeout=5)
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            first_news = soup.find('h2', class_='boss-article-title') 
            if first_news:
                return first_news.get_text(strip=True)
    except Exception:
        return None
    return None

# --- 3. DESIGN PRO ---
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
        .block-container { padding-top: 3.5rem !important; }
        .stChatMessage { background-color: rgba(255, 255, 255, 0.95); border-radius: 15px; padding: 10px; margin-bottom: 10px; border: 1px solid #e0e0e0; }
        .stChatMessage p, .stChatMessage li { color: black !important; }
        .stExpander details summary p { color: #024c6f !important; font-weight: bold; }
        </style>
    """, unsafe_allow_html=True)
    
    bg_data = get_base64('background.webp')
    if bg_data:
        st.markdown(f"""
            <style>
            .stApp {{ background-image: url("data:image/webp;base64,{bg_data}"); background-size: cover; background-attachment: fixed; }}
            </style>
        """, unsafe_allow_html=True)

# --- 4. SÉCURITÉ (DOUBLE ACCÈS CORRIGÉ) ---
def check_password():
    if st.session_state.get("password_correct"): return True
    apply_pro_design()
    st.markdown("<br><br><br><br>", unsafe_allow_html=True)
    st.markdown("<h1 style='text-align: center; color: #024c6f;'>🔐 Accès Expert Réservé</h1>", unsafe_allow_html=True)
    col_l, col_m, col_r = st.columns([1, 2, 1])
    with col_m:
        pwd = st.text_input("Code d'accès :", type="password")
        if st.button("Se connecter"):
            # Correction : Utilisation de os.getenv uniquement pour éviter l'erreur StreamlitSecretNotFoundError
            valid_pwd = os.getenv("APP_PASSWORD", "DEFAUT_USER_123")
            admin_pwd = os.getenv("ADMIN_PASSWORD", "ADMIN2026")
            
            if pwd == str(admin_pwd):
                st.session_state["password_correct"] = True
                st.session_state["is_admin"] = True
                st.rerun()
            elif pwd == str(valid_pwd):
                st.session_state["password_correct"] = True
                st.session_state["is_admin"] = False
                st.rerun()
            else: 
                st.error("Code erroné.")
    st.stop()

check_password()
apply_pro_design()

# --- 5. INITIALISATION IA ---
if 'session_id' not in st.session_state: st.session_state['session_id'] = str(uuid.uuid4())

NOMS_PROS = {
    "REF_2026_": "🏛️ BARÈMES ET RÉFÉRENTIELS OFFICIELS 2026",
    "MEMO_CHIFFRES": "📑 RÉFÉRENTIEL CHIFFRÉS 2026",
    "REF_": "✅ RÉFÉRENCES :\n- BOSS\n- Code du Travail\n- Code de la Sécurité Sociale\n- Organismes Sociaux",
    "DOC_BOSS_": "🌐 BULLETIN OFFICIEL SÉCURITÉ SOCIALE (BOSS)",
    "LEGAL_": "📕 SOCLE LÉGAL (CODES)",
    "DOC_JURISPRUDENCE": "⚖️ JURISPRUDENCE (PRÉCÉDENTS)",
    "barème officiel": "🏛️ BOSS - ARCHIVES BARÈMES"
}

def nettoyer_nom_source(raw_source):
    if not raw_source: return "Source Inconnue"
    nom_fichier = os.path.basename(raw_source)
    for cle, nom_pro in NOMS_PROS.items():
        if cle in nom_fichier: return nom_pro
    return nom_fichier.replace('.txt', '').replace('.pdf', '').replace('_', ' ')

def get_data_clean_context():
    context_list = []
    if os.path.exists("data_clean"):
        for filename in os.listdir("data_clean"):
            if filename.endswith(".txt"):
                with open(f"data_clean/{filename}", "r", encoding="utf-8") as f:
                    context_list.append(f"[{nettoyer_nom_source(filename)}] : {f.read()}")
    return "\n".join(context_list)

@st.cache_resource
def load_system():
    api_key = os.getenv("GOOGLE_API_KEY") or st.secrets.get("GOOGLE_API_KEY")
    embeddings = GoogleGenerativeAIEmbeddings(model="models/text-embedding-004", google_api_key=api_key)
    vectorstore = Chroma(embedding_function=embeddings)
    llm = ChatGoogleGenerativeAI(model="gemini-2.0-flash-exp", temperature=0, google_api_key=api_key)
    
    if os.path.exists("data_clean"):
        files = [f for f in os.listdir("data_clean") if f.endswith(".txt")]
        texts_to_add = []
        metadatas = []
        for filename in files:
            with open(f"data_clean/{filename}", "r", encoding="utf-8") as f:
                content = f.read()
                texts_to_add.append(content)
                metadatas.append({"source": filename, "session_id": "system_init"})
        if texts_to_add:
            vectorstore.add_texts(texts=texts_to_add, metadatas=metadatas)
    return vectorstore, llm

vectorstore, llm = load_system()

# --- 6. FONCTIONS ---
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

# --- 7. INTERFACE ---
col_t, col_b = st.columns([4, 1])
with col_t: st.markdown("<h1 style='color: #024c6f; margin-top: 0;'>Expert Social Pro 2026</h1>", unsafe_allow_html=True)
with col_b:
    if st.button("Nouvelle session"):
        st.session_state.messages = []
        st.session_state['session_id'] = str(uuid.uuid4())
        st.rerun()

# --- ZONE ADMIN PRIVÉE ---
if st.session_state.get("is_admin", False):
    last_news = check_boss_updates()
    if last_news:
        st.info(f"📢 **VEILLE BOSS (MODE ADMIN) :** {last_news}")
        if st.button("🤖 Analyser et générer la fiche"):
            with st.status("Analyse juridique...", expanded=True):
                news_context = f"Titre de l'actualité BOSS : {last_news}."
                prompt_veille = ChatPromptTemplate.from_template("Analyse cette news BOSS pour 2026 et crée une fiche OBJET/SOURCE/TEXTE : {news}")
                analyste = (prompt_veille | llm | StrOutputParser()).invoke({"news": news_context})
                st.code(analyste, language="text")

with st.expander("📎 Analyser un document externe", expanded=False):
    uploaded_file = st.file_uploader("Fichier", type=["pdf", "txt"])
    if uploaded_file and uploaded_file.name not in st.session_state.get('history', []):
        if process_file(uploaded_file):
            if 'history' not in st.session_state: st.session_state['history'] = []
            st.session_state['history'].append(uploaded_file.name)
            st.success("Document intégré !")
            st.rerun()

# --- 8. CHAT ---
if "messages" not in st.session_state: st.session_state.messages = []
for message in st.session_state.messages:
    with st.chat_message(message["role"], avatar=("avatar-logo.png" if message["role"] == "assistant" else None)):
        st.markdown(message["content"])

if query := st.chat_input("Posez votre question..."):
    st.session_state.messages.append({"role": "user", "content": query})
    with st.chat_message("user"): st.markdown(query)
    with st.chat_message("assistant", avatar="avatar-logo.png"):
        with st.status("🔍 Recherche en cours...", expanded=True):
            priorite_context = get_data_clean_context()
            raw_law = vectorstore.similarity_search(query, k=20)
            user_docs = vectorstore.similarity_search(query, k=10, filter={"session_id": st.session_state['session_id']})
            context = []
            if priorite_context: context.append("### FICHES D'EXPERTISE PRIORITAIRES (2025-2026) ###\n" + priorite_context)
            if user_docs: context.append("### CAS CLIENT (VOTRE DOCUMENT) ###\n" + "\n".join([d.page_content for d in user_docs]))
            context.append("\n### DOCTRINE ET ARCHIVES ###")
            for d in raw_law:
                nom = nettoyer_nom_source(d.metadata.get('source',''))
                context.append(f"[SOURCE : {nom}]\n{d.page_content}")
            prompt = ChatPromptTemplate.from_template("""
            Tu es l'Expert Social Pro 2026. 
            MISSION : Réponds via les fiches prioritaires. Saute deux lignes avant d'écrire [SOURCE : ...].
            CONTEXTE : {context}
            QUESTION : {question}
            """)
            full_response = (prompt | llm | StrOutputParser()).invoke({"context": "\n".join(context), "question": query})
        st.markdown(full_response)
    st.session_state.messages.append({"role": "assistant", "content": full_response})
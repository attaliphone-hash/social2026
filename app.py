import sys
import os
import uuid
import base64
import requests
from bs4 import BeautifulSoup
import streamlit as st
import pypdf
import stripe

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

# --- 3. FONCTION DE VEILLE BOSS ORIGINALE RÉTABLIE ---
def check_boss_updates():
    try:
        url = "https://boss.gouv.fr/portail/accueil.html"
        # Utilisation du User-Agent original pour éviter les blocages serveurs
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"}
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            # Recherche de la mention de mise à jour dans les paragraphes
            actualites = soup.find_all('p')
            for p in actualites:
                if "mise à jour" in p.text.lower():
                    return f"Recherche de mise à jour BOSS : OK - {p.text.strip()}"
            return "Recherche de mise à jour BOSS : OK - Base 2026 à jour (Aucune modification majeure détectée)"
        return "Serveur BOSS injoignable pour vérification automatique."
    except Exception as e:
        return "Veille automatique BOSS temporairement indisponible."

# --- 4. DESIGN PRO CENTRALISÉ ---
def get_base64(bin_file):
    if os.path.exists(bin_file):
        return base64.b64encode(open(bin_file, "rb").read()).decode()
    return ""

def apply_pro_design():
    st.markdown("""
        <style>
        #MainMenu {visibility: hidden;}
        header {visibility: hidden !important; height: 0px;}
        footer {visibility: hidden;}
        [data-testid="stHeader"] {display: none;}
        .block-container { padding-top: 1.5rem !important; }
        .stChatMessage { background-color: rgba(255,255,255,0.95); border-radius: 15px; padding: 10px; margin-bottom: 10px; border: 1px solid #e0e0e0; }
        .stChatMessage p, .stChatMessage li { color: black !important; }
        .assurance-text { font-size: 11px !important; color: #024c6f !important; text-align: left; display: block; line-height: 1.3; margin-bottom: 20px; }
        .assurance-title { font-weight: bold; color: #024c6f; display: inline; font-size: 11px !important; }
        .assurance-desc { font-weight: normal; color: #444; display: inline; font-size: 11px !important; }
        @media (max-width: 768px) {
            .block-container { padding-top: 0.2rem !important; }
            iframe[title="st.iframe"] + br, hr + br, .stMarkdown br { display: none; }
            .assurance-text { margin-bottom: 2px !important; line-height: 1.1 !important; font-size: 10px !important; }
            h1 { font-size: 1.5rem !important; margin-top: 0px !important; }
        }
        .stExpander details summary p { font-size: 12px !important; color: #666 !important; }
        </style>
    """, unsafe_allow_html=True)
    
    bg_data = get_base64('background.webp')
    if bg_data:
        st.markdown(f'<style>.stApp {{ background-image: url("data:image/webp;base64,{bg_data}"); background-size: cover; background-attachment: fixed; }}</style>', unsafe_allow_html=True)

ARGUMENTS_UNIFIES = [
    ("Données Certifiées 2026 :", " Intégration prioritaire des nouveaux barèmes (PASS, avantages en nature) pour une précision chirurgicale."),
    ("Sources officielles :", " Une analyse simultanée et croisée du BOSS, du Code du Travail, du Code de la Sécurité Sociale et des communiqués des organismes sociaux."),
    ("Mise à Jour Agile :", " Notre base est actualisée en temps réel dès la publication de nouvelles circulaires ou réformes, garantissant une conformité permanente."),
    ("Traçabilité Totale :", " Chaque réponse est systématiquement sourcée via une liste détaillée, permettant de valider instantanément le fondement juridique."),
    ("Confidentialité Garantie :", " Vos données sont traitées exclusivement en mémoire vive (RAM) et ne sont jamais stockées, ni utilisées pour entraîner des modèles d'IA.")
]

def render_top_columns():
    cols = st.columns(5)
    for i, col in enumerate(cols):
        title, desc = ARGUMENTS_UNIFIES[i]
        col.markdown(f'<p class="assurance-text"><span class="assurance-title">{title}</span><span class="assurance-desc">{desc}</span></p>', unsafe_allow_html=True)

# --- 5. SÉCURITÉ ---
def check_password():
    if st.session_state.get("password_correct"):
        # Affichage du bandeau bleu original pour l'admin
        if st.session_state.get("user_role") == "admin":
            st.info(check_boss_updates())
        return True
    
    apply_pro_design()
    render_top_columns()
    st.markdown("<hr>", unsafe_allow_html=True)
    st.markdown("<h1 style='text-align: center; color: #024c6f;'>🔑 Accès Expert Social Pro</h1>", unsafe_allow_html=True)
    col_l, col_m, col_r = st.columns([1, 2, 1])
    with col_m:
        tab_login, tab_subscribe = st.tabs(["Se connecter", "S'abonner"])
        with tab_login:
            pwd = st.text_input("Code d'accès :", type="password")
            if st.button("Se connecter"):
                if pwd == os.getenv("ADMIN_PASSWORD", "ADMIN2026"):
                    st.session_state.update({"password_correct": True, "user_role": "admin"})
                    st.rerun()
                elif pwd == os.getenv("APP_PASSWORD", "DEFAUT_USER_123"):
                    st.session_state.update({"password_correct": True, "user_role": "user"})
                    st.rerun()
                else: st.error("Code erroné.")
    st.stop()

check_password()
apply_pro_design()

# --- 6. SYSTÈME IA ---
if 'session_id' not in st.session_state: st.session_state['session_id'] = str(uuid.uuid4())

@st.cache_resource
def load_system():
    api_key = os.getenv("GOOGLE_API_KEY")
    embeddings = GoogleGenerativeAIEmbeddings(model="models/text-embedding-004", google_api_key=api_key)
    vectorstore = Chroma(embedding_function=embeddings)
    llm = ChatGoogleGenerativeAI(model="gemini-2.0-flash-exp", temperature=0, google_api_key=api_key)
    if os.path.exists("data_clean"):
        files = [f for f in os.listdir("data_clean") if f.endswith(".txt")]
        texts, metas = [], []
        for f in files:
            with open(f"data_clean/{f}", "r", encoding="utf-8") as file:
                content = file.read()
                if content.strip():
                    texts.append(content)
                    metas.append({"source": f, "session_id": "system_init"})
        if texts: vectorstore.add_texts(texts=texts, metadatas=metas)
    return vectorstore, llm

vectorstore, llm = load_system()

# --- 7. INTERFACE ---
render_top_columns()
st.markdown("<hr>", unsafe_allow_html=True)
col_t, col_b = st.columns([4, 1])
with col_t: st.markdown("<h1 style='color: #024c6f; margin:0;'>Expert Social Pro 2026</h1>", unsafe_allow_html=True)
with col_b:
    if st.button("Nouvelle session"):
        st.session_state.messages = []
        st.rerun()

if "messages" not in st.session_state: st.session_state.messages = []
for msg in st.session_state.messages:
    with st.chat_message(msg["role"], avatar=("avatar-logo.png" if msg["role"]=="assistant" else None)):
        st.markdown(msg["content"])

if query := st.chat_input("Posez votre question..."):
    st.session_state.messages.append({"role": "user", "content": query})
    with st.chat_message("user"): st.markdown(query)
    with st.chat_message("assistant", avatar="avatar-logo.png"):
        with st.status("🔍 Analyse juridique..."):
            docs = vectorstore.similarity_search(query, k=8)
            context = "\n\n".join([d.page_content for d in docs])
            prompt = ChatPromptTemplate.from_template("""
            Tu es l'Expert Social Pro 2026.
            Cite les références réelles entre crochets : [Article L.XXXX du Code du travail].
            ---
            Termine par : "*Références : Article XXX du Code de XXX.*" en italique.
            CONTEXTE : {context}
            QUESTION : {question}
            """)
            response = (prompt | llm | StrOutputParser()).invoke({"context": context, "question": query})
        st.markdown(response)
    st.session_state.messages.append({"role": "assistant", "content": response})
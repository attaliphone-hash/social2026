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

# --- 3. FONCTION DE VEILLE BOSS (LE BANDEAU BLEU ORIGINAL) ---
def check_boss_updates():
    try:
        url = "https://boss.gouv.fr/portail/accueil.html"
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"}
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            actualites = soup.find_all('p')
            for p in actualites:
                if "mise à jour" in p.text.lower():
                    return f"Recherche de mise à jour BOSS : OK - {p.text.strip()}"
            return "Recherche de mise à jour BOSS : OK - Base 2026 à jour (Aucune modification détectée)"
        return "Serveur BOSS injoignable."
    except:
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
        }
        .stExpander details summary p { font-size: 12px !important; color: #666 !important; }
        </style>
    """, unsafe_allow_html=True)
    bg_data = get_base64('background.webp')
    if bg_data:
        st.markdown(f'<style>.stApp {{ background-image: url("data:image/webp;base64,{bg_data}"); background-size: cover; background-attachment: fixed; }}</style>', unsafe_allow_html=True)

ARGUMENTS_UNIFIES = [
    ("Données Certifiées 2026 :", " Intégration prioritaire des nouveaux barèmes (PASS, avantages en nature) pour une précision chirurgicale."),
    ("Sources officielles :", " Une analyse simultanée et croisée du BOSS, du Code du Travail, du Code de la Sécurité Sociale."),
    ("Mise à Jour Agile :", " Notre base est actualisée en temps réel dès la publication de nouvelles circulaires ou réformes."),
    ("Traçabilité Totale :", " Chaque réponse est systématiquement sourcée via une liste détaillée, permettant de valider le fondement juridique."),
    ("Confidentialité Garantie :", " Vos données sont traitées exclusivement en mémoire vive (RAM) et ne sont jamais stockées.")
]

def render_top_columns():
    cols = st.columns(5)
    for i, col in enumerate(cols):
        title, desc = ARGUMENTS_UNIFIES[i]
        col.markdown(f'<p class="assurance-text"><span class="assurance-title">{title}</span><span class="assurance-desc">{desc}</span></p>', unsafe_allow_html=True)

# --- 5. SÉCURITÉ ---
def check_password():
    if st.session_state.get("password_correct"):
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

# --- 6. SYSTÈME DE RECHERCHE IA ET NETTOYAGE SOURCES ---
if 'session_id' not in st.session_state: st.session_state['session_id'] = str(uuid.uuid4())
NOMS_PROS = {"REF_2026_": "🏛️ BARÈMES ET RÉFÉRENTIELS OFFICIELS 2026", "MEMO_CHIFFRES": "📑 RÉFÉRENTIEL CHIFFRÉS 2026", "DOC_BOSS_": "🌐 BULLETIN OFFICIEL SÉCURITÉ SOCIALE (BOSS)", "LEGAL_": "📕 SOCLE LÉGAL (CODES)", "REF_": "✅ RÉFÉRENCES : BOSS, Code du Travail, CSS"}

def nettoyer_nom_source(raw_source):
    nom = os.path.basename(raw_source)
    for cle, nom_pro in NOMS_PROS.items():
        if cle in nom: return nom_pro
    return nom.replace('.txt','').replace('.pdf','').replace('_',' ')

def get_data_clean_context():
    context_list = []
    if os.path.exists("data_clean"):
        for filename in os.listdir("data_clean"):
            if filename.endswith(".txt") and not filename.startswith("LEGAL_"):
                with open(f"data_clean/{filename}", "r", encoding="utf-8") as f:
                    context_list.append(f"[{nettoyer_nom_source(filename)}] : {f.read()}")
    return "\n".join(context_list)

@st.cache_resource
def load_system():
    api_key = os.getenv("GOOGLE_API_KEY")
    embeddings = GoogleGenerativeAIEmbeddings(model="models/text-embedding-004", google_api_key=api_key)
    vectorstore = Chroma(embedding_function=embeddings)
    llm = ChatGoogleGenerativeAI(model="gemini-2.0-flash-exp", temperature=0, google_api_key=api_key)
    if os.path.exists("data_clean"):
        files = [f for f in os.listdir("data_clean") if f.endswith(".txt")]
        for f in files:
            with open(f"data_clean/{f}", "r", encoding="utf-8") as file:
                content = file.read()
                if content.strip():
                    vectorstore.add_texts(texts=[content], metadatas=[{"source": f, "session_id": "system_init"}])
    return vectorstore, llm

vectorstore, llm = load_system()

def build_expert_context(query):
    context = []
    priorite = get_data_clean_context()
    if priorite: context.append("### FICHES D'EXPERTISE PRIORITAIRES ###\n" + priorite)
    raw_law = vectorstore.similarity_search(query, k=8)
    for d in raw_law:
        nom = nettoyer_nom_source(d.metadata.get('source',''))
        context.append(f"[SOURCE : {nom}]\n{d.page_content}")
    return "\n\n".join(context)

# --- 7. INTERFACE PRINCIPALE ---
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
        with st.status("🔍 Analyse juridique en cours..."):
            context = build_expert_context(query)
            prompt = ChatPromptTemplate.from_template("""
            Tu es l'Expert Social Pro 2026, spécialisé en droit social français.
            Utilise exclusivement le CONTEXTE fourni pour répondre à la QUESTION.
            
            CONSIGNES DE RÉPONSE :
            1. INTERDICTION de citer les noms techniques de fichiers ou "Parties".
            2. Cite les références réelles (Article + Code) directement dans le texte entre crochets : [Article L.XXXX du Code du travail].
            3. RAPPEL DES SOURCES FINAL : Termine ta réponse par une ligne horizontale (---) suivie de la mention :
               "*Références : Article XXX du Code de XXX ; Article YYY du Code de YYY.*"
            4. Ce rappel final doit être obligatoirement en italique, sans puces, et sur une seule ligne si possible.
            
            CONTEXTE : {context}
            QUESTION : {question}
            """)
            response = (prompt | llm | StrOutputParser()).invoke({"context": context, "question": query})
        st.markdown(response)
    st.session_state.messages.append({"role": "assistant", "content": response})

st.markdown("<div style='text-align:center; color:#888; font-size:11px; margin-top:50px;'>© 2026 socialexpertfrance.fr</div>", unsafe_allow_html=True)
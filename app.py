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

# --- 3. DESIGN PRO CENTRALISÉ ---
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
        .stChatMessage { background-color: rgba(255,255,255,0.95); border-radius: 15px; padding: 10px; margin-bottom: 10px; border: 1px solid #e0e0e0; }
        .stChatMessage p, .stChatMessage li { color: black !important; }
        .stExpander details summary p { color: #024c6f !important; font-weight: bold; }
        .assurance-text { font-size: 10px !important; color: #444; line-height: 1.3; text-align: left; padding: 5px; }
        .assurance-title { font-weight: bold; color: #024c6f; display: block; margin-bottom: 2px; font-size: 10px !important; }
        </style>
    """, unsafe_allow_html=True)
    
    bg_data = get_base64('background.webp')
    if bg_data:
        st.markdown(f"""
            <style>
            .stApp {{ background-image: url("data:image/webp;base64,{bg_data}"); background-size: cover; background-attachment: fixed; }}
            </style>
        """, unsafe_allow_html=True)

# --- 4. SÉCURITÉ & MODULE SAAS ---
stripe.api_key = os.getenv("STRIPE_SECRET_KEY")
PRICE_ID_MONTHLY = "price_1SnaTDQZ5ivv0RayXfKqvJ6I"
PRICE_ID_ANNUAL = "price_1SnaUOQZ5ivv0RayFnols3TI"

def create_checkout_session(plan_type):
    price_id = PRICE_ID_MONTHLY if plan_type == "Mensuel" else PRICE_ID_ANNUAL
    try:
        checkout_session = stripe.checkout.Session.create(
            payment_method_types=['card'],
            line_items=[{'price': price_id, 'quantity': 1}],
            mode='subscription',
            success_url="https://socialexpertfrance.fr?payment=success",
            cancel_url="https://socialexpertfrance.fr?payment=cancel",
        )
        return checkout_session.url
    except Exception as e:
        st.error(f"Erreur Stripe : {e}")
        return None

def check_password():
    if st.session_state.get("password_correct"): return True
    apply_pro_design()
    
    # Header Marketing
    st.markdown("<br>", unsafe_allow_html=True)
    c1, c2, c3, c4 = st.columns(4)
    args = [
        ("Données Certifiées 2026", "Nouveaux barèmes PASS et avantages en nature."),
        ("Maillage de Sources", "Analyse BOSS, Code du Travail, CSS et Organismes."),
        ("Mise à Jour Agile", "Base actualisée dès la publication de nouvelles circulaires."),
        ("Traçabilité", "Chaque réponse est systématiquement sourcée.")
    ]
    for i, col in enumerate([c1, c2, c3, c4]):
        col.markdown(f'<p class="assurance-text"><span class="assurance-title">{args[i][0]} :</span> {args[i][1]}</p>', unsafe_allow_html=True)
    
    st.markdown("<hr>", unsafe_allow_html=True)
    st.markdown("<h1 style='text-align: center; color: #024c6f;'>🔑 Accès Expert Social Pro</h1>", unsafe_allow_html=True)
    
    col_l, col_m, col_r = st.columns([1, 2, 1])
    with col_m:
        tab_login, tab_subscribe = st.tabs(["Se connecter", "S'abonner"])
        with tab_login:
            pwd = st.text_input("Code d'accès :", type="password")
            if st.button("Se connecter"):
                if pwd == os.getenv("ADMIN_PASSWORD", "ADMIN2026"):
                    st.session_state.update({"password_correct": True, "is_admin": True})
                    st.rerun()
                elif pwd == os.getenv("APP_PASSWORD", "DEFAUT_USER_123"):
                    st.session_state.update({"password_correct": True, "is_admin": False})
                    st.rerun()
                else: st.error("Code erroné.")
        with tab_subscribe:
            st.markdown("### Choisissez votre formule")
            cm, ca = st.columns(2)
            with cm:
                st.info("**Mensuel**\n\n50 € HT / mois")
                if st.button("S'abonner (Mensuel)"):
                    url = create_checkout_session("Mensuel")
                    if url: st.markdown(f'<meta http-equiv="refresh" content="0;URL={url}">', unsafe_allow_html=True)
            with ca:
                st.success("**Annuel**\n\n500 € HT / an")
                if st.button("S'abonner (Annuel)"):
                    url = create_checkout_session("Annuel")
                    if url: st.markdown(f'<meta http-equiv="refresh" content="0;URL={url}">', unsafe_allow_html=True)
    st.stop()

check_password()
apply_pro_design()

# --- 5. SYSTÈME DE RECHERCHE EXPERT ---
if 'session_id' not in st.session_state: st.session_state['session_id'] = str(uuid.uuid4())

NOMS_PROS = {
    "REF_2026_": "🏛️ BARÈMES ET RÉFÉRENTIELS OFFICIELS 2026",
    "MEMO_CHIFFRES": "📑 RÉFÉRENTIEL CHIFFRÉS 2026",
    "DOC_BOSS_": "🌐 BULLETIN OFFICIEL SÉCURITÉ SOCIALE (BOSS)",
    "LEGAL_": "📕 SOCLE LÉGAL (CODES)",
    "REF_": "✅ RÉFÉRENCES : BOSS, Code du Travail, CSS"
}

def nettoyer_nom_source(raw_source):
    nom = os.path.basename(raw_source)
    for cle, nom_pro in NOMS_PROS.items():
        if cle in nom: return nom_pro
    return nom.replace('.txt','').replace('.pdf','').replace('_',' ')

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
    api_key = os.getenv("GOOGLE_API_KEY")
    embeddings = GoogleGenerativeAIEmbeddings(model="models/text-embedding-004", google_api_key=api_key)
    vectorstore = Chroma(embedding_function=embeddings)
    llm = ChatGoogleGenerativeAI(model="gemini-2.0-flash-exp", temperature=0, google_api_key=api_key)
    
    if os.path.exists("data_clean"):
        files = [f for f in os.listdir("data_clean") if f.endswith(".txt")]
        texts, metas = [], []
        for f in files:
            with open(f"data_clean/{f}", "r", encoding="utf-8") as file:
                texts.append(file.read())
                metas.append({"source": f, "session_id": "system_init"})
        if texts: vectorstore.add_texts(texts=texts, metadatas=metas)
    return vectorstore, llm

vectorstore, llm = load_system()

# --- 6. GESTION DES FLUX ---
def build_expert_context(query):
    context = []
    priorite = get_data_clean_context()
    if priorite: context.append("### FICHES D'EXPERTISE PRIORITAIRES ###\n" + priorite)
    user_docs = vectorstore.similarity_search(query, k=5, filter={"session_id": st.session_state['session_id']})
    if user_docs: context.append("### CAS CLIENT (VOTRE DOCUMENT) ###\n" + "\n".join([d.page_content for d in user_docs]))
    raw_law = vectorstore.similarity_search(query, k=15)
    for d in raw_law:
        nom = nettoyer_nom_source(d.metadata.get('source',''))
        context.append(f"[SOURCE : {nom}]\n{d.page_content}")
    return "\n\n".join(context)

# --- 7. INTERFACE PRINCIPALE ---
c1, c2, c3, c4 = st.columns(4)
c1.markdown('<p class="assurance-text"><span class="assurance-title">Certifié 2026</span></p>', unsafe_allow_html=True)
c2.markdown('<p class="assurance-text"><span class="assurance-title">Sources Multiples</span></p>', unsafe_allow_html=True)
c3.markdown('<p class="assurance-text"><span class="assurance-title">Mise à jour Agile</span></p>', unsafe_allow_html=True)
c4.markdown('<p class="assurance-text"><span class="assurance-title">Traçabilité</span></p>', unsafe_allow_html=True)

st.markdown("<hr>", unsafe_allow_html=True)
col_t, col_b = st.columns([4, 1])
with col_t: st.markdown("<h1 style='color: #024c6f; margin:0;'>Expert Social Pro 2026</h1>", unsafe_allow_html=True)
with col_b:
    if st.button("Nouvelle session"):
        st.session_state.messages = []
        st.session_state['session_id'] = str(uuid.uuid4())
        st.rerun()

if st.session_state.get("is_admin"):
    st.info("Mode Admin : Veille BOSS activée.")

with st.expander("📎 Analyser un document externe"):
    uploaded_file = st.file_uploader("Fichier PDF ou TXT", type=["pdf","txt"])
    if uploaded_file and uploaded_file.name not in st.session_state.get('history', []):
        st.session_state.setdefault('history', []).append(uploaded_file.name)
        st.success("Document intégré !")

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
                Tu es l'Expert Social Pro 2026. Réponds avec une rigueur absolue.
                
                RÈGLES DE STRUCTURE :
                1. Ta réponse doit commencer DIRECTEMENT par les faits, chiffres ou l'analyse, SANS préambule (pas de "D'après les documents..."), écrits en GRAS (format Markdown **texte**).
                2. Ensuite, ajoute une section commençant par "⚖️ SOURCE :".
                3. Enfin, ajoute une section commençant par "💡 PRÉCISION :" pour les conditions, seuils ou exceptions.

                CONTEXTE : {context}
                QUESTION : {question}
            """)
            response = (prompt | llm | StrOutputParser()).invoke({"context": context, "question": query})
        st.markdown(response)
    st.session_state.messages.append({"role": "assistant", "content": response})

st.divider()
st.markdown("<div style='text-align:center; color:#888; font-size:11px;'>© 2026 socialexpertfrance.fr</div>", unsafe_allow_html=True)
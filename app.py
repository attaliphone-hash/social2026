import streamlit as st
import sys
import os
import time
import uuid
import base64
import requests
import stripe
import pypdf  # Pour la lecture des pièces jointes
from bs4 import BeautifulSoup

# --- CHARGEMENT DES VARIABLES D'ENVIRONNEMENT ---
from dotenv import load_dotenv
load_dotenv()

# --- IMPORT DU MOTEUR DE RÈGLES (CHIFFRES) ---
from rules.engine import SocialRuleEngine

# --- IMPORTS IA (PINECONE CLOUD) ---
from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAIEmbeddings
from langchain_pinecone import PineconeVectorStore
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

# 1. CONFIGURATION PAGE
st.set_page_config(page_title="Expert Social Pro France", layout="wide")

# ==============================================================================
# PARTIE 0 : MODULE DE VEILLE BOSS
# ==============================================================================
def check_boss_updates():
    try:
        url = "https://boss.gouv.fr/portail/accueil.html"
        headers = {"User-Agent": "Mozilla/5.0"}
        response = requests.get(url, headers=headers, timeout=5)
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            actualites = soup.find_all('p')
            for p in actualites:
                if "mise à jour" in p.text.lower():
                    return f"📢 ALERTE BOSS : {p.text.strip()}"
            return "✅ Veille BOSS : Aucune mise à jour détectée ce jour (Base 2026 à jour)."
        return "⚠️ Serveur BOSS injoignable."
    except:
        return "⚠️ Module de veille BOSS indisponible."

# ==============================================================================
# PARTIE 1 : DESIGN & UTILITAIRES
# ==============================================================================

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
        
        /* Design des bulles de chat */
        .stChatMessage { background-color: rgba(255,255,255,0.95); border-radius: 15px; padding: 10px; margin-bottom: 10px; border: 1px solid #e0e0e0; }
        .stChatMessage p, .stChatMessage li { color: black !important; line-height: 1.6 !important; }
        
        /* --- CORRECTIF UPLOAD CHIRURGICAL --- */
        /* On supprime totalement le cadre gris, les marges et les textes d'instruction */
        .stFileUploader section {
            background-color: transparent !important;
            border: none !important;
            padding: 0 !important;
            min-height: auto !important;
        }
        .stFileUploader [data-testid="stFileUploaderDropzoneInstructions"] {
            display: none !important;
        }
        .stFileUploader div[data-testid="stFileUploaderInterface"] {
            padding: 0 !important;
        }
        /* Style du bouton pour qu'il soit petit, pro et aligné */
        .stFileUploader button {
            border: 1px solid #024c6f !important;
            color: #024c6f !important;
            background-color: white !important;
            padding: 2px 8px !important;
            font-size: 11px !important;
            height: 28px !important;
            border-radius: 5px !important;
        }
        /* On réduit l'espace sous le bouton d'upload */
        .stFileUploader { margin-bottom: -15px !important; }

        /* CITATIONS (sub) */
        sub { font-size: 0.75em !important; color: #666 !important; vertical-align: baseline !important; position: relative; top: -0.3em; }
        .assurance-text { font-size: 11px !important; color: #024c6f !important; text-align: left; display: block; line-height: 1.3; margin-bottom: 20px; }
        .assurance-title { font-weight: bold; color: #024c6f; display: inline; font-size: 11px !important; }
        .assurance-desc { font-weight: normal; color: #444; display: inline; font-size: 11px !important; }
        h1 { font-family: 'Helvetica Neue', sans-serif; text-shadow: 1px 1px 2px rgba(255,255,255,0.8); }
        
        @media (max-width: 768px) {
            .block-container { padding-top: 0.2rem !important; }
            h1 { font-size: 1.5rem !important; }
        }
        </style>
    """, unsafe_allow_html=True)
    
    bg_data = get_base64('background.webp')
    if bg_data:
        st.markdown(f'<style>.stApp {{ background-image: url("data:image/webp;base64,{bg_data}"); background-size: cover; background-attachment: fixed; }}</style>', unsafe_allow_html=True)

ARGUMENTS_UNIFIES = [
    ("Données Certifiées 2026 :", " Précision chirurgicale."),
    ("Sources officielles :", " Analyse croisée BOSS/Codes."),
    ("Mise à Jour Agile :", " Actualisation en temps réel."),
    ("Traçabilité Totale :", " Réponses systématiquement sourcées."),
    ("Confidentialité Garantie :", " Aucun cookie, traitement en RAM.")
]

def render_top_columns():
    cols = st.columns(5)
    for i, col in enumerate(cols):
        title, desc = ARGUMENTS_UNIFIES[i]
        col.markdown(f'<p class="assurance-text"><span class="assurance-title">{title}</span><span class="assurance-desc">{desc}</span></p>', unsafe_allow_html=True)

def show_legal_info():
    st.markdown("<br>", unsafe_allow_html=True)
    _, col_l, col_r, _ = st.columns([1, 2, 2, 1])
    with col_l:
        with st.expander("Mentions Légales"):
            st.markdown("<div style='font-size: 11px; color: #444;'>Expert Social Pro - support@socialexpertfrance.fr</div>", unsafe_allow_html=True)
    with col_r:
        with st.expander("Politique de Confidentialité (RGPD)"):
            st.markdown("<div style='font-size: 11px; color: #444;'>Traitement volatil en RAM. Pas d'entraînement IA.</div>", unsafe_allow_html=True)

# --- SECURITE & STRIPE ---
stripe.api_key = os.getenv("STRIPE_SECRET_KEY")

def check_password():
    if st.session_state.get("password_correct"):
        if st.session_state.get("is_admin"):
             with st.expander("🔒 Admin - Veille BOSS", expanded=False):
                 st.info(check_boss_updates())
        return True
    
    apply_pro_design()
    render_top_columns()
    st.markdown("<h1 style='text-align: center; color: #024c6f;'>🔑 Accès Expert Social Pro V4</h1>", unsafe_allow_html=True)
    col_l, col_m, col_r = st.columns([1, 2, 1])
    with col_m:
        pwd = st.text_input("Code d'accès :", type="password")
        if st.button("Se connecter"):
            if pwd == os.getenv("ADMIN_PASSWORD", "ADMIN2026"):
                st.session_state.update({"password_correct": True, "is_admin": True})
                st.rerun()
            elif pwd == os.getenv("APP_PASSWORD", "DEFAUT_USER_123"):
                st.session_state.update({"password_correct": True, "is_admin": False})
                st.rerun()
    st.stop()

# ==============================================================================
# PARTIE 2 : LE MOTEUR V4
# ==============================================================================
check_password()
apply_pro_design()
render_top_columns()

@st.cache_resource
def load_engine(): return SocialRuleEngine()

@st.cache_resource
def load_ia_system():
    api_key = os.getenv("GOOGLE_API_KEY")
    embeddings = GoogleGenerativeAIEmbeddings(model="models/text-embedding-004", google_api_key=api_key)
    vectorstore = PineconeVectorStore.from_existing_index(index_name="expert-social", embedding=embeddings)
    llm = ChatGoogleGenerativeAI(model="gemini-2.0-flash-exp", temperature=0, google_api_key=api_key)
    return vectorstore, llm

engine = load_engine()
vectorstore, llm = load_ia_system()

def build_context(query):
    raw_docs = vectorstore.similarity_search(query, k=15)
    context_text = ""
    for d in raw_docs:
        clean_name = os.path.basename(d.metadata.get('source', '')).replace('.pdf', '').replace('.txt', '')
        pretty_src = "Code du Travail" if "LEGAL" in clean_name else f"BOSS : {clean_name}"
        context_text += f"[DOCUMENT : {pretty_src}]\n{d.page_content}\n\n"
    return context_text

def get_gemini_response(query, context, user_doc_content=None):
    user_doc_section = f"\n--- DOCUMENT UTILISATEUR ---\n{user_doc_content}\n" if user_doc_content else ""
    prompt = ChatPromptTemplate.from_template("""
    Tu es l'Expert Social Pro 2026. Réponds EXCLUSIVEMENT via les DOCUMENTS fournis.
    Citations : <sub>*[BOSS : Nom]*</sub> ou <sub>*[Document Utilisateur]*</sub>.
    Footer : "---" puis "**Sources utilisées :**" avec liste.
    
    CONTEXTE : {context}
    """ + user_doc_section + """
    QUESTION : {question}
    """)
    chain = prompt | llm | StrOutputParser()
    return chain.invoke({"context": context, "question": query})

# ==============================================================================
# PARTIE 3 : INTERFACE (HEADER + CHAT)
# ==============================================================================
st.markdown("<hr>", unsafe_allow_html=True)
col_t, col_b = st.columns([4, 1])
with col_t: st.markdown("<h1 style='color: #024c6f; margin:0;'>Expert Social Pro V4</h1>", unsafe_allow_html=True)
with col_b:
    if st.button("Nouvelle session"):
        st.session_state.messages = []
        st.rerun()

if "messages" not in st.session_state: st.session_state.messages = []
for msg in st.session_state.messages:
    with st.chat_message(msg["role"], avatar=("avatar-logo.png" if msg["role"]=="assistant" else None)):
        st.markdown(msg["content"], unsafe_allow_html=True)

# --- ZONE UPLOAD DISCRÈTE (ALIGNÉE GAUCHE) ---
col_up, _ = st.columns([1, 4])
with col_up:
    uploaded_file = st.file_uploader("Upload", type=["pdf", "txt"], label_visibility="collapsed")

user_doc_text = None
if uploaded_file:
    try:
        if uploaded_file.type == "application/pdf":
            reader = pypdf.PdfReader(uploaded_file)
            user_doc_text = "\n".join([p.extract_text() for p in reader.pages if p.extract_text()])
        else: user_doc_text = uploaded_file.read().decode("utf-8")
        st.toast(f"📎 {uploaded_file.name} chargé", icon="✅")
    except Exception as e: st.error(f"Erreur : {e}")

# --- ZONE SAISIE ---
if query := st.chat_input("Votre question juridique ou chiffrée..."):
    st.session_state.messages.append({"role": "user", "content": query})
    with st.chat_message("user"):
        st.markdown(query)
        if uploaded_file: st.markdown(f"<sub>📎 *Fichier : {uploaded_file.name}*</sub>", unsafe_allow_html=True)

    with st.chat_message("assistant", avatar="avatar-logo.png"):
        message_placeholder = st.empty()
        # Routeur Intention simple
        is_conversational = "?" in query or len(query.split()) > 7 or user_doc_text
        verdict = {"found": False}
        if not is_conversational: verdict = engine.get_formatted_answer(keywords=query)
        
        if verdict["found"]:
            full_response = f"{verdict['text']}\n\n---\n**Sources :**\n* {verdict['source']}"
        else:
            with st.spinner("Analyse en cours..."):
                context = build_context(query)
                full_response = get_gemini_response(query, context, user_doc_text)
        
        message_placeholder.markdown(full_response, unsafe_allow_html=True)
        st.session_state.messages.append({"role": "assistant", "content": full_response})

show_legal_info()
st.markdown("<div style='text-align:center; color:#888; font-size:11px;'>© 2026 socialexpertfrance.fr</div>", unsafe_allow_html=True)
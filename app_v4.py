import streamlit as st
import sys
import os
import time
import uuid
import base64
import requests
import stripe
from bs4 import BeautifulSoup

# --- CORRECTION : CHARGEMENT DU FICHIER .ENV ---
from dotenv import load_dotenv
load_dotenv()

# --- IMPORT DU MOTEUR V4 (La seule nouveauté logique) ---
from rules.engine import SocialRuleEngine

# --- IMPORTS IA ---
from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAIEmbeddings
from langchain_chroma import Chroma
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

# 1. CONFIGURATION PAGE
st.set_page_config(page_title="Expert Social Pro V4", layout="wide")

# ==============================================================================
# PARTIE 1 : LA CARROSSERIE (RECUPERATION STRICTE DE TON CODE EN LIGNE)
# ==============================================================================

# --- FONCTIONS UTILITAIRES VISUELLES ---
def get_base64(bin_file):
    if os.path.exists(bin_file):
        return base64.b64encode(open(bin_file, "rb").read()).decode()
    return ""

def apply_pro_design():
    # TON CSS EXACT (V3)
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
        
        /* CITATIONS (sub) - Style Expert Social */
        sub {
            font-size: 0.75em !important;
            color: #666 !important;
            vertical-align: baseline !important;
            position: relative;
            top: -0.3em;
        }
        
        .assurance-text { font-size: 11px !important; color: #024c6f !important; text-align: left; display: block; line-height: 1.3; margin-bottom: 20px; }
        .assurance-title { font-weight: bold; color: #024c6f; display: inline; font-size: 11px !important; }
        .assurance-desc { font-weight: normal; color: #444; display: inline; font-size: 11px !important; }
        
        h1 { font-family: 'Helvetica Neue', sans-serif; text-shadow: 1px 1px 2px rgba(255,255,255,0.8); }
        
        @media (max-width: 768px) {
            .block-container { padding-top: 0.2rem !important; }
            .assurance-text { margin-bottom: 2px !important; line-height: 1.1 !important; font-size: 10px !important; }
        }
        .stExpander details summary p { font-size: 12px !important; color: #666 !important; }
        .stExpander { border: none !important; background-color: transparent !important; }
        </style>
    """, unsafe_allow_html=True)
    
    # CHARGEMENT FOND D'ECRAN
    bg_data = get_base64('background.webp')
    if bg_data:
        st.markdown(f'<style>.stApp {{ background-image: url("data:image/webp;base64,{bg_data}"); background-size: cover; background-attachment: fixed; }}</style>', unsafe_allow_html=True)
    else:
        # Fallback si l'image n'est pas trouvée localement (Texture papier)
        st.markdown("""<style>.stApp { background-image: url("https://www.transparenttextures.com/patterns/legal-pad.png"); background-size: cover; background-color: #f0f2f6; }</style>""", unsafe_allow_html=True)

# --- TEXTES DE RÉASSURANCE (TES TEXTES) ---
ARGUMENTS_UNIFIES = [
    ("Données Certifiées 2026 :", " Intégration prioritaire des nouveaux textes pour une précision chirurgicale."),
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

# --- MODULES LEGAUX ---
def show_legal_info():
    st.markdown("<br><br>", unsafe_allow_html=True)
    _, col_l, col_r, _ = st.columns([1, 2, 2, 1])
    
    with col_l:
        with st.expander("Mentions Légales"):
            # HTML propre collé à gauche pour éviter les erreurs d'indentation Markdown
            st.markdown("""
<div style='font-size: 11px; color: #444; line-height: 1.4;'>
    <strong>ÉDITEUR :</strong><br>
    Le site <em>socialexpertfrance.fr</em> est édité par la Direction Expert Social Pro.<br>
    Contact : support@socialexpertfrance.fr<br><br>
    <strong>PROPRIÉTÉ INTELLECTUELLE :</strong><br>
    L'ensemble de ce site relève de la législation française et internationale sur le droit d'auteur.
    Toute reproduction est interdite sans autorisation.<br><br>
    <strong>RESPONSABILITÉ :</strong><br>
    Les réponses sont fournies à titre indicatif et ne remplacent pas une consultation juridique.
</div>
""", unsafe_allow_html=True)
            
    with col_r:
        with st.expander("Politique de Confidentialité (RGPD)"):
            st.markdown("""
<div style='font-size: 11px; color: #444; line-height: 1.4;'>
    <strong>CONFIDENTIALITÉ TOTALE :</strong><br>
    1. <strong>Aucun Stockage :</strong> Traitement volatil en RAM. Données détruites après la réponse.<br>
    2. <strong>Pas d'Entraînement IA :</strong> Vos données ne servent jamais à entraîner les modèles.<br>
    3. <strong>Sécurité Stripe :</strong> Aucune donnée bancaire ne transite par nos serveurs.<br><br>
    <em>Conformité RGPD : Droit à l'oubli garanti par défaut (No-Log).</em>
</div>
""", unsafe_allow_html=True)

# --- SECURITE & STRIPE ---
stripe.api_key = os.getenv("STRIPE_SECRET_KEY")
def create_checkout_session(plan_type):
    # Tes IDs Stripe originaux
    price_id = "price_1SnaTDQZ5ivv0RayXfKqvJ6I" if plan_type == "Mensuel" else "price_1SnaUOQZ5ivv0RayFnols3TI"
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
    """Gère l'authentification et l'affichage de la page de login"""
    
    # 1. SI DÉJÀ CONNECTÉ
    if st.session_state.get("password_correct"):
        return True
    
    # 2. SI NON CONNECTÉ (Ecran de Login)
    apply_pro_design()
    render_top_columns() # AFFICHE LES COLONNES SUR LA PAGE DE LOGIN
    
    st.markdown("<hr>", unsafe_allow_html=True)
    st.markdown("<h1 style='text-align: center; color: #024c6f;'>🔑 Accès Expert Social Pro V4 (Alpha)</h1>", unsafe_allow_html=True)
    
    col_l, col_m, col_r = st.columns([1, 2, 1])
    with col_m:
        tab_login, tab_subscribe = st.tabs(["Se connecter", "S'abonner"])
        with tab_login:
            pwd = st.text_input("Code d'accès :", type="password")
            if st.button("Se connecter"):
                # Gestion propre des variables pour éviter les erreurs .env
                admin_pwd = os.getenv("ADMIN_PASSWORD", "ADMIN2026")
                user_pwd = os.getenv("APP_PASSWORD", "DEFAUT_USER_123")
                
                if pwd == admin_pwd or pwd == user_pwd:
                    st.session_state.update({"password_correct": True})
                    st.rerun()
                else:
                    st.error("Code erroné.")
        
        with tab_subscribe:
            if st.button("S'abonner (Mensuel)"):
                url = create_checkout_session("Mensuel")
                if url: st.markdown(f'<meta http-equiv="refresh" content="0;URL={url}">', unsafe_allow_html=True)
    
    show_legal_info()
    st.stop()

# ==============================================================================
# PARTIE 2 : LE MOTEUR V4 (INTELLIGENCE HYBRIDE)
# ==============================================================================

# Vérification Connexion
check_password()
# Rappel du design et des colonnes une fois connecté pour l'interface principale
apply_pro_design()
render_top_columns()

@st.cache_resource
def load_engine():
    """Charge le Cerveau Logique V4 (Règles YAML)"""
    return SocialRuleEngine()

@st.cache_resource
def load_ia_system():
    """Charge le Cerveau Créatif (Gemini + Chroma)"""
    api_key = os.getenv("GOOGLE_API_KEY")
    embeddings = GoogleGenerativeAIEmbeddings(model="models/text-embedding-004", google_api_key=api_key)
    vectorstore = Chroma(embedding_function=embeddings)
    llm = ChatGoogleGenerativeAI(model="gemini-2.0-flash-exp", temperature=0, google_api_key=api_key)
    
    # Indexation Volatile (Comme V3 mais structure V4)
    if os.path.exists("data_clean"):
        files = [f for f in os.listdir("data_clean") if f.endswith(".txt")]
        texts, metas = [], []
        for f in files:
            with open(f"data_clean/{f}", "r", encoding="utf-8") as file:
                content = file.read()
                if content.strip():
                    clean_source = f.replace('.txt', '').replace('_', ' ')
                    texts.append(content)
                    metas.append({"source": clean_source})
        if texts:
            for i in range(0, len(texts), 1000):
                vectorstore.add_texts(texts=texts[i:i+1000], metadatas=metas[i:i+1000])
    return vectorstore, llm

# Init Moteurs
engine = load_engine()
vectorstore, llm = load_ia_system()

def build_context(query):
    """Construction contexte IA avec priorité aux documents"""
    raw_docs = vectorstore.similarity_search(query, k=5)
    context_text = ""
    for d in raw_docs:
        src = d.metadata.get('source', 'Source Inconnue')
        # Logique V3 adaptée : affichage propre pour l'IA
        if "REF" in src: pretty_src = "Barème Officiel"
        elif "BOSS" in src: pretty_src = "BOSS"
        elif "LEGAL" in src: pretty_src = "Code du Travail"
        else: pretty_src = src
        context_text += f"[DOCUMENT : {pretty_src}]\n{d.page_content}\n\n"
    return context_text

def get_gemini_response(query, context):
    """Prompt Hybride : Intelligence V4 + Formatage Visuel V3 + Footer Sources"""
    prompt = ChatPromptTemplate.from_template("""
    Tu es l'Expert Social Pro 2026.
    
    MISSION :
    Réponds aux questions en t'appuyant EXCLUSIVEMENT sur les DOCUMENTS fournis.
    
    CONSIGNES D'AFFICHAGE STRICTES (CRITIQUE) :
    1. CITATIONS DANS LE TEXTE : Utilise la balise HTML <sub> pour les citations précises.
       Format : <sub>*[Nom Source - Art. X]*</sub>
       Exemple : <sub>*[Code du Travail - Art. L.1234-9]*</sub>
    
    2. FOOTER RÉCAPITULATIF (OBLIGATOIRE) :
       À la toute fin de ta réponse, saute deux lignes, ajoute une ligne de séparation "---" puis saute encore une ligne.
       Ensuite, liste les sources en utilisant simplement de l'italique (Markdown).
       NE METS PAS DE BALISES HTML DANS LE FOOTER POUR ÉVITER LES BUGS D'AFFICHAGE.
       Format attendu pour le footer : *Sources utilisées : Code du Travail (Art. L.XXX), BOSS (Fiche Y)...*
    
    INTELLIGENCE JURIDIQUE :
    - Ne te contente pas du nom du fichier. Cherche l'article de loi ou la référence précise DANS le texte.
    
    CONTEXTE :
    {context}
    
    QUESTION : 
    {question}
    """)
    chain = prompt | llm | StrOutputParser()
    return chain.invoke({"context": context, "question": query})

# ==============================================================================
# PARTIE 3 : L'INTERFACE UTILISATEUR (HEADER + CHAT)
# ==============================================================================

# Entête (Colonnes)
# Note : render_top_columns est déjà appelé plus haut ligne 224, 
# mais on garde le hr et le titre ici pour la structure
st.markdown("<hr>", unsafe_allow_html=True)

# Titre Principal
col_t, col_b = st.columns([4, 1])
with col_t: st.markdown("<h1 style='color: #024c6f; margin:0;'>Expert Social Pro V4</h1>", unsafe_allow_html=True)
with col_b:
    if st.button("Nouvelle session"):
        st.session_state.messages = []
        st.rerun()

# Affichage Historique
if "messages" not in st.session_state:
    st.session_state.messages = []

for msg in st.session_state.messages:
    with st.chat_message(msg["role"], avatar=("avatar-logo.png" if msg["role"]=="assistant" else None)):
        st.markdown(msg["content"], unsafe_allow_html=True)

# Zone de Saisie & Traitement
if query := st.chat_input("Votre question juridique ou chiffrée..."):
    
    st.session_state.messages.append({"role": "user", "content": query})
    with st.chat_message("user"):
        st.markdown(query)

    with st.chat_message("assistant", avatar="avatar-logo.png"):
        message_placeholder = st.empty()
        full_response = ""
        
        # --- ETAPE 1 : ROUTEUR D'INTENTION (ARCHITECTURAL) ---
        # On détermine si la requête est une "Conversation/Question" (-> IA) ou une "Recherche de Donnée" (-> Moteur)
        # Critères de détection d'une phrase complexe ou d'une question :
        markers = ["?", "comment", "pourquoi", "est-ce", "quand", "quel", "quelle", "un salarié", "mon salarié", "l'employeur", "peut-on"]
        is_conversational = (
            "?" in query  # Ponctuation explicite
            or any(m in query.lower() for m in markers)  # Marqueurs de questions ou de mise en situation
            or len(query.split()) > 7  # Sécurité : une phrase de +7 mots est rarement une simple recherche de variable
        )

        verdict = {"found": False}
        
        # On n'active le Moteur de Règles QUE si ce n'est PAS une conversation/analyse
        if not is_conversational:
            verdict = engine.get_formatted_answer(keywords=query)
        
        if verdict["found"]:
            # Réponse Certifiée par Règle (Pour les chiffres/taux simples uniquement)
            full_response = f"{verdict['text']}\n\n--- \n<sub>*Source certifiée : {verdict['source']}*</sub>"
            message_placeholder.markdown(full_response, unsafe_allow_html=True)
            
        else:
            # --- ETAPE 2 : IA GENERATIVE (GEMINI) ---
            # Tout ce qui est analyse, question complexe, situation salarié -> GEMINI
            with st.spinner("🔍 Analyse juridique et recherche des articles..."):
                context = build_context(query)
                gemini_response = get_gemini_response(query, context)
                full_response = gemini_response
                message_placeholder.markdown(full_response, unsafe_allow_html=True)

    st.session_state.messages.append({"role": "assistant", "content": full_response})

# Pied de page (Legal)
show_legal_info()
st.markdown("<div style='text-align:center; color:#888; font-size:11px; margin-top:30px;'>© 2026 socialexpertfrance.fr</div>", unsafe_allow_html=True)
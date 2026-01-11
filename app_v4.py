import streamlit as st
import sys
import os
import time
import uuid
import base64
import requests
import stripe
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
st.set_page_config(page_title="Expert Social Pro V4", layout="wide")

# ==============================================================================
# PARTIE 0 : MODULE DE VEILLE BOSS (RÉINTÉGRATION)
# ==============================================================================
def check_boss_updates():
    """Scrape le site du BOSS pour vérifier les mises à jour récentes"""
    try:
        url = "https://boss.gouv.fr/portail/accueil.html"
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"}
        response = requests.get(url, headers=headers, timeout=5) # Timeout court pour ne pas ralentir
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            actualites = soup.find_all('p')
            for p in actualites:
                if "mise à jour" in p.text.lower():
                    return f"📢 ALERTE BOSS : {p.text.strip()}"
            return "✅ Veille BOSS : Aucune mise à jour détectée ce jour (Base 2026 à jour)."
        return "⚠️ Serveur BOSS injoignable pour vérification."
    except:
        return "⚠️ Module de veille BOSS temporairement indisponible."

# ==============================================================================
# PARTIE 1 : DESIGN & UTILITAIRES
# ==============================================================================

def get_base64(bin_file):
    if os.path.exists(bin_file):
        return base64.b64encode(open(bin_file, "rb").read()).decode()
    return ""

def apply_pro_design():
    # CSS EXACT (V3 + CORRECTIF MOBILE RÉINTÉGRÉ)
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
        
        /* --- OPTIMISATION MOBILE (RÉINTÉGRÉE) --- */
        @media (max-width: 768px) {
            .block-container { padding-top: 0.2rem !important; }
            /* Cache les sauts de ligne inutiles sur mobile pour gagner de la place */
            iframe[title="st.iframe"] + br, hr + br, .stMarkdown br { display: none; }
            /* Ajustement fin des textes d'assurance */
            .assurance-text { margin-bottom: 2px !important; line-height: 1.1 !important; font-size: 10px !important; }
            /* Réduction de la taille du Titre H1 sur mobile */
            h1 { font-size: 1.5rem !important; margin-top: 0px !important; }
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
        st.markdown("""<style>.stApp { background-image: url("https://www.transparenttextures.com/patterns/legal-pad.png"); background-size: cover; background-color: #f0f2f6; }</style>""", unsafe_allow_html=True)

# --- TEXTES DE RÉASSURANCE ---
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
            st.markdown("""
<div style='font-size: 11px; color: #444; line-height: 1.4;'>
    <strong>ÉDITEUR :</strong><br>
    Le site <em>socialexpertfrance.fr</em> est édité par Sylvain Attal EI.<br>
    Contact : sylvain.attal@businessagent-ai.com<br><br>
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
    # IDs Stripe
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
        # -- SI ADMIN : VEILLE BOSS --
        if st.session_state.get("is_admin"):
             with st.expander("🔒 Espace Admin - Veille BOSS", expanded=True):
                 st.info(check_boss_updates())
        return True
    
    # 2. SI NON CONNECTÉ (Ecran de Login)
    apply_pro_design()
    render_top_columns()
    
    st.markdown("<hr>", unsafe_allow_html=True)
    st.markdown("<h1 style='text-align: center; color: #024c6f;'>🔑 Accès Expert Social Pro V4</h1>", unsafe_allow_html=True)
    
    col_l, col_m, col_r = st.columns([1, 2, 1])
    with col_m:
        tab_login, tab_subscribe = st.tabs(["Se connecter", "S'abonner"])
        with tab_login:
            pwd = st.text_input("Code d'accès :", type="password")
            if st.button("Se connecter"):
                # Récupération des mots de passe (avec valeurs par défaut identiques à app.py)
                admin_pwd = os.getenv("ADMIN_PASSWORD", "ADMIN2026")
                user_pwd = os.getenv("APP_PASSWORD", "DEFAUT_USER_123")
                
                if pwd == admin_pwd:
                    st.session_state.update({"password_correct": True, "is_admin": True})
                    st.rerun()
                elif pwd == user_pwd:
                    st.session_state.update({"password_correct": True, "is_admin": False})
                    st.rerun()
                else:
                    st.error("Code erroné.")
        
        # --- BOUTONS ABONNEMENT EN DEUX COLONNES ---
        with tab_subscribe:
            st.markdown("<br>", unsafe_allow_html=True)
            col_sub1, col_sub2 = st.columns(2)
            
            with col_sub1:
                st.info("📅 **Mensuel**\n\nFlexibilité totale.")
                if st.button("S'abonner (Mensuel)", use_container_width=True):
                    url = create_checkout_session("Mensuel")
                    if url: st.markdown(f'<meta http-equiv="refresh" content="0;URL={url}">', unsafe_allow_html=True)
            
            with col_sub2:
                st.success("🗓 **Annuel**\n\n2 mois offerts !")
                if st.button("S'abonner (Annuel)", use_container_width=True):
                    url = create_checkout_session("Annuel")
                    if url: st.markdown(f'<meta http-equiv="refresh" content="0;URL={url}">', unsafe_allow_html=True)
    
    show_legal_info()
    st.stop()

# ==============================================================================
# PARTIE 2 : LE MOTEUR V4 (INTELLIGENCE HYBRIDE & CLOUD)
# ==============================================================================

# Vérification Connexion (Inclut maintenant la logique Admin/User)
check_password()
apply_pro_design()
render_top_columns()

@st.cache_resource
def load_engine():
    """Charge le Cerveau Logique V4 (Règles YAML)"""
    return SocialRuleEngine()

@st.cache_resource
def load_ia_system():
    """Charge le Cerveau Créatif (Gemini + Pinecone CLOUD)"""
    api_key = os.getenv("GOOGLE_API_KEY")
    pinecone_key = os.getenv("PINECONE_API_KEY")
    
    # 1. Modèle d'Embedding
    embeddings = GoogleGenerativeAIEmbeddings(model="models/text-embedding-004", google_api_key=api_key)
    
    # 2. Connexion à PINECONE (Cloud)
    vectorstore = PineconeVectorStore.from_existing_index(
        index_name="expert-social",
        embedding=embeddings
    )
    
    # 3. LLM (Gemini 2.0)
    llm = ChatGoogleGenerativeAI(model="gemini-2.0-flash-exp", temperature=0, google_api_key=api_key)
    
    return vectorstore, llm

# Init Moteurs
engine = load_engine()
vectorstore, llm = load_ia_system()

def build_context(query):
    """Construction contexte IA avec priorité aux documents"""
    # Recherche dans le CLOUD Pinecone
    # --- MODIFICATION CRITIQUE : K=20 pour éviter la vision en tunnel ---
    raw_docs = vectorstore.similarity_search(query, k=20)
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
       Ensuite, liste les sources EN TEXTE BRUT (SANS MARQUEURS MARKDOWN, SANS GRAS, SANS ITALIQUE).
       Format attendu pour le footer : Sources utilisées : Code du Travail (Art. L.XXX), BOSS (Fiche Y)...
    
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
        markers = ["?", "comment", "pourquoi", "est-ce", "quand", "quel", "quelle", "un salarié", "mon salarié", "l'employeur", "peut-on"]
        is_conversational = (
            "?" in query  # Ponctuation explicite
            or any(m in query.lower() for m in markers)  # Marqueurs de questions ou de mise en situation
            or len(query.split()) > 7  # Sécurité
        )

        verdict = {"found": False}
        
        # On n'active le Moteur de Règles QUE si ce n'est PAS une conversation/analyse
        if not is_conversational:
            verdict = engine.get_formatted_answer(keywords=query)
        
        if verdict["found"]:
            # Réponse Certifiée par Règle
            full_response = f"{verdict['text']}\n\n--- \n<sub>*Source certifiée : {verdict['source']}*</sub>"
            message_placeholder.markdown(full_response, unsafe_allow_html=True)
            
        else:
            # --- ETAPE 2 : IA GENERATIVE (GEMINI + PINECONE) ---
            with st.spinner("🔍 Analyse juridique et recherche des articles..."):
                context = build_context(query)
                gemini_response = get_gemini_response(query, context)
                full_response = gemini_response
                message_placeholder.markdown(full_response, unsafe_allow_html=True)

    st.session_state.messages.append({"role": "assistant", "content": full_response})

# Pied de page (Legal)
show_legal_info()
st.markdown("<div style='text-align:center; color:#888; font-size:11px; margin-top:30px;'>© 2026 socialexpertfrance.fr</div>", unsafe_allow_html=True)
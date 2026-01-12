import streamlit as st
import sys
import os
import time
import uuid
import base64
import requests
import stripe
import pypdf  # AJOUTÉ POUR LIRE LES FICHIERS UPLOADÉS
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
# PARTIE 0 : MODULE DE VEILLE BOSS (STRICTEMENT CELUI FOURNI)
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
    # CSS EXACT + CSS UPLOAD DISCRET + TRADUCTION BOUTON
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
        
        /* --- CSS UPLOAD DISCRET & TRADUIT --- */
        .stFileUploader section {
            background-color: transparent !important;
            border: none !important;
            padding: 0 !important;
            min-height: 0 !important;
        }
        .stFileUploader [data-testid="stFileUploaderDropzoneInstructions"] {
            display: none !important;
        }
        .stFileUploader div[data-testid="stFileUploaderInterface"] {
            padding: 0 !important;
            margin: 0 !important;
        }
        
        /* REECRITURE DU TEXTE DU BOUTON (HACK CSS) */
        .stFileUploader button {
            border: 1px solid #ccc !important;
            background-color: white !important;
            color: transparent !important; /* On cache le texte 'Browse files' */
            padding: 0.25rem 0.75rem !important;
            font-size: 14px !important;
            margin-top: 3px !important;
            position: relative;
            width: 160px !important; /* Largeur fixe pour accueillir le texte français */
        }
        
        /* On écrit le nouveau texte par-dessus */
        .stFileUploader button::after {
            content: "Charger un document pour analyse";
            color: #333 !important;
            position: absolute;
            left: 0; top: 0;
            width: 100%; height: 100%;
            display: flex;
            justify-content: center;
            align-items: center;
            font-weight: 500;
        }
        
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
        
        /* --- OPTIMISATION MOBILE --- */
        @media (max-width: 768px) {
            .block-container { padding-top: 0.2rem !important; }
            iframe[title="st.iframe"] + br, hr + br, .stMarkdown br { display: none; }
            .assurance-text { margin-bottom: 2px !important; line-height: 1.1 !important; font-size: 10px !important; }
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
    ("Confidentialité Garantie :", " Aucun cookie déposéVos données sont traitées exclusivement en mémoire vive (RAM) et ne sont jamais stockées, ni utilisées pour entraîner des modèles d'IA.")
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
    Le site <em>socialexpertfrance.fr</em> est édité par la Direction Expert Social Pro.<br>
    Contact : support@socialexpertfrance.fr<br><br>
    <strong>PROPRIÉTÉ INTELLECTUELLE :</strong><br>
    L'ensemble de ce site relève de la législation française et internationale sur le droit d'auteur.
    Toute reproduction même partielle est interdite sans autorisation.<br><br>
    <strong>RESPONSABILITÉ :</strong><br>
    Les réponses sont fournies à titre indicatif et ne remplacent pas une consultation juridique.
</div>
""", unsafe_allow_html=True)
            
    with col_r:
        with st.expander("Politique de Confidentialité (RGPD)"):
            st.markdown("""
<div style='font-size: 11px; color: #444; line-height: 1.4;'>
    <strong>CONFIDENTIALITÉ TOTALE :</strong><br>
    1. <strong>Aucun Stockage :</strong> Traitement volatil en RAM. Données détruites après la réponse. Aucun cookie n'est déposé<br>
    2. <strong>Pas d'Entraînement IA :</strong> Vos données ne servent jamais à entraîner les modèles.<br>
    3. <strong>Sécurité Stripe :</strong> Aucune donnée bancaire ne transite par nos serverurs.<br><br>
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
                # Récupération des mots de passe
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

# Vérification Connexion
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
    """Construction contexte IA"""
    raw_docs = vectorstore.similarity_search(query, k=20)
    context_text = ""
    for d in raw_docs:
        raw_src = d.metadata.get('source', 'Source Inconnue')
        clean_name = os.path.basename(raw_src).replace('.pdf', '').replace('.txt', '').replace('.csv', '')
        
        if "REF" in clean_name: pretty_src = "Barème Officiel"
        elif "LEGAL" in clean_name: pretty_src = "Code du Travail"
        else: pretty_src = f"BOSS : {clean_name}"
        
        context_text += f"[DOCUMENT : {pretty_src}]\n{d.page_content}\n\n"
    return context_text

def get_gemini_response(query, context, user_doc_content=None):
    """Prompt Hybride : Gère BOSS + Document Utilisateur"""
    
    user_doc_section = f"\n--- DOCUMENT UTILISATEUR ---\n{user_doc_content}\n" if user_doc_content else ""

    prompt = ChatPromptTemplate.from_template("""
    Tu es l'Expert Social Pro 2026.
    
    MISSION :
    Réponds aux questions en t'appuyant EXCLUSIVEMENT sur les DOCUMENTS fournis.
    
    CONSIGNES D'AFFICHAGE STRICTES (ACCORD CLIENT) :
    1. CITATIONS DANS LE TEXTE : Utilise la balise HTML <sub> pour les citations précises.
       Format impératif : <sub>*[BOSS : Nom du document]*</sub> ou <sub>*[Document Utilisateur]*</sub>
       INTERDICTION FORMELLE : Ne jamais mentionner "DATA_CLEAN/" ou des extensions comme ".pdf".
    
    2. FOOTER RÉCAPITULATIF (OBLIGATOIRE) :
       À la toute fin de ta réponse, ajoute une ligne de séparation "---".
       Puis écris "**Sources utilisées :**" en gras.
       Liste chaque source ainsi : "* BOSS : [Nom du document]"
    
    CONTEXTE :
    {context}
    """ + user_doc_section + """
    QUESTION : 
    {question}
    """)
    chain = prompt | llm | StrOutputParser()
    return chain.invoke({"context": context, "question": query})

# ==============================================================================
# PARTIE 3 : L'INTERFACE UTILISATEUR (HEADER + CHAT)
# ==============================================================================

st.markdown("<hr>", unsafe_allow_html=True)

# Titre Principal et Boutons (MODIFICATION PLACEMENT UPLOAD)
# On donne un peu plus de place à droite pour les deux boutons
col_t, col_buttons = st.columns([3.5, 1.5]) 

with col_t: 
    st.markdown("<h1 style='color: #024c6f; margin:0;'>Expert Social Pro V4</h1>", unsafe_allow_html=True)

with col_buttons:
    # Sous-colonnes pour aligner : Upload | Nouvelle Session
    c_up, c_new = st.columns([1, 1])
    
    with c_up:
        # BOUTON UPLOAD (CSS le rend discret et traduit)
        uploaded_file = st.file_uploader("Upload", type=["pdf", "txt"], label_visibility="collapsed")
    
    with c_new:
        if st.button("Nouvelle session"):
            st.session_state.messages = []
            st.rerun()

# Traitement immédiat du document uploadé (pour le rendre dispo dans le chat)
user_doc_text = None
if uploaded_file:
    try:
        if uploaded_file.type == "application/pdf":
            reader = pypdf.PdfReader(uploaded_file)
            user_doc_text = "\n".join([p.extract_text() for p in reader.pages if p.extract_text()])
        else:
            user_doc_text = uploaded_file.read().decode("utf-8")
        st.toast(f"📎 {uploaded_file.name} analysé", icon="✅")
    except Exception as e:
        st.error(f"Erreur lecture fichier: {e}")

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
        if uploaded_file:
            st.markdown(f"<sub>📎 *Analyse incluant : {uploaded_file.name}*</sub>", unsafe_allow_html=True)

    with st.chat_message("assistant", avatar="avatar-logo.png"):
        message_placeholder = st.empty()
        full_response = ""
        
        # --- ETAPE 1 : ROUTEUR D'INTENTION ---
        markers = ["?", "comment", "pourquoi", "est-ce", "quand", "quel", "quelle", "un salarié", "mon salarié", "l'employeur", "peut-on"]
        is_conversational = (
            "?" in query 
            or any(m in query.lower() for m in markers) 
            or len(query.split()) > 7 
            or user_doc_text # SI DOC UPLOADÉ, ON FORCE L'IA
        )

        verdict = {"found": False}
        if not is_conversational and not user_doc_text:
            verdict = engine.get_formatted_answer(keywords=query)
        
        if verdict["found"]:
            full_response = f"{verdict['text']}\n\n---\n**Sources utilisées :**\n* {verdict['source']}"
            message_placeholder.markdown(full_response, unsafe_allow_html=True)
        else:
            # --- ETAPE 2 : IA GENERATIVE (GEMINI + PINECONE) ---
            wait_msg = "🔍 Analyse de votre document et des textes..." if user_doc_text else "🔍 Analyse juridique et recherche des articles..."
            with st.spinner(wait_msg):
                context = build_context(query)
                # On passe le doc utilisateur à la fonction
                gemini_response = get_gemini_response(query, context, user_doc_content=user_doc_text)
                full_response = gemini_response
                message_placeholder.markdown(full_response, unsafe_allow_html=True)

    st.session_state.messages.append({"role": "assistant", "content": full_response})

# Pied de page (Legal)
show_legal_info()
st.markdown("<div style='text-align:center; color:#888; font-size:11px; margin-top:30px;'>© 2026 socialexpertfrance.fr</div>", unsafe_allow_html=True)
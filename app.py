import streamlit as st
import sys
import os
import time
import uuid
import stripe
import pypdf  # Pour lecture des fichiers uploadés

# --- IMPORT MODULES UI & SERVICES ---
from ui.styles import apply_pro_design, render_top_columns, show_legal_info
from services.boss_watcher import check_boss_updates

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
# PARTIE 0 : FONCTIONS STRIPE & AUTH (EN ATTENTE D'EXTRACTION)
# ==============================================================================

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
        # -- SI ADMIN : VEILLE BOSS (Via le nouveau service) --
        if st.session_state.get("is_admin"):
             with st.expander("🔒 Espace Admin - Veille BOSS (RSS)", expanded=True):
                 
                 # === GESTION ALERTE VUE / MASQUÉE ===
                 if "boss_alert_seen" not in st.session_state:
                     st.session_state.boss_alert_seen = False
                     
                 if not st.session_state.boss_alert_seen:
                     # AFFICHE L'ALERTE (Appel au fichier services/boss_watcher.py)
                     st.markdown(check_boss_updates(), unsafe_allow_html=True)
                     
                     # BOUTON POUR MASQUER
                     c_dismiss, _ = st.columns([1.5, 3.5])
                     with c_dismiss:
                         if st.button("✅ Marquer comme vu / Masquer"):
                             st.session_state.boss_alert_seen = True
                             st.rerun()
                 else:
                     # MESSAGE COURT QUAND MASQUÉ
                     st.success("✅ Alerte lue")
                     if st.button("Réafficher la veille"):
                         st.session_state.boss_alert_seen = False
                         st.rerun()
                         
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

    # MODIFICATION : Structure inversée pour forcer le respect du format (Recency Bias)
    prompt = ChatPromptTemplate.from_template("""
    Tu es l'Expert Social Pro 2026.
    
    CONTEXTE :
    {context}
    """ + user_doc_section + """
    
    MISSION :
    Réponds à la question suivante en t'appuyant EXCLUSIVEMENT sur les documents ci-dessus.
    QUESTION : {question}
    
    CONSIGNES D'AFFICHAGE STRICTES :
    1. CITATIONS DANS LE TEXTE : Utilise la balise HTML <sub> pour les citations précises (ex: <sub>*[BOSS : Barème]*</sub>).
    
    2. FOOTER RÉCAPITULATIF (OBLIGATOIRE) :
       Tu DOIS terminer ta réponse EXACTEMENT par ce bloc (avec la ligne de séparation) :
       
       ---
       **Sources utilisées :**
       * BOSS : [Nom du document]
       * [Autre Source]
    """)
    chain = prompt | llm | StrOutputParser()
    response = chain.invoke({"context": context, "question": query})
    
    # SÉCURITÉ ANTI-ERRATIQUE : Si l'IA oublie le tiret de séparation, on le force.
    if "Sources utilisées :" in response and "---" not in response[-500:]:
        response = response.replace("**Sources utilisées :**", "\n\n---\n**Sources utilisées :**")
        
    return response

# ==============================================================================
# PARTIE 3 : L'INTERFACE UTILISATEUR (HEADER + CHAT)
# ==============================================================================

st.markdown("<hr>", unsafe_allow_html=True)

# Titre Principal et Boutons
col_t, col_buttons = st.columns([3, 2]) 

with col_t: 
    st.markdown("<h1 style='color: #024c6f; margin:0;'>Expert Social Pro V4</h1>", unsafe_allow_html=True)

with col_buttons:
    c_up, c_new = st.columns([1.6, 1])
    with c_up:
        uploaded_file = st.file_uploader("Upload", type=["pdf", "txt"], label_visibility="collapsed")
    with c_new:
        if st.button("Nouvelle session"):
            st.session_state.messages = []
            st.rerun()

# Traitement immédiat du document uploadé
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
            or user_doc_text 
        )

        verdict = {"found": False}
        if not is_conversational and not user_doc_text:
            verdict = engine.get_formatted_answer(keywords=query)
        
        if verdict["found"]:
            full_response = f"{verdict['text']}\n\n---\n**Sources utilisées :**\n* {verdict['source']}"
            message_placeholder.markdown(full_response, unsafe_allow_html=True)
        else:
            # --- ETAPE 2 : IA GENERATIVE (GEMINI + PINECONE) ---
            wait_msg = "🔍 Analyse de votre document et des textes..." if user_doc_text else "🔍 Analyse juridique et recherche des références..."
            with st.spinner(wait_msg):
                context = build_context(query)
                gemini_response = get_gemini_response(query, context, user_doc_content=user_doc_text)
                full_response = gemini_response
                message_placeholder.markdown(full_response, unsafe_allow_html=True)

    st.session_state.messages.append({"role": "assistant", "content": full_response})

show_legal_info()
st.markdown("<div style='text-align:center; color:#888; font-size:11px; margin-top:30px;'>© 2026 socialexpertfrance.fr</div>", unsafe_allow_html=True)
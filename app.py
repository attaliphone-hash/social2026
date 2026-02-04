import streamlit as st
import time
import os
import re
import datetime
from dotenv import load_dotenv

# Charge les variables d'environnement
load_dotenv()

# --- IMPORTS ARCHITECTURE ---
from core.config import Config
from core.auth_manager import AuthManager
from core.subscription_manager import SubscriptionManager
from services.ia_service import IAService
from services.document_service import DocumentService
from services.quota_service import QuotaService
from services.export_service import ExportService
from services.legal_watch import show_legal_watch_bar
from ui.styles import apply_pro_design
from ui.components import UIComponents
from utils.helpers import clean_source_name, logger, sanitize_user_input

# --- IMPORTS MOTEUR & IA ---
from rules.engine import SocialRuleEngine
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

# ==============================================================================
# 1. INITIALISATION
# ==============================================================================
st.set_page_config(
    page_title="Expert Social Pro 2026",
    page_icon="avatar-logo.png",
    layout="wide"
)

if "messages" not in st.session_state: st.session_state.messages = []
if "uploader_key" not in st.session_state: st.session_state.uploader_key = 0
if "user_info" not in st.session_state: st.session_state.user_info = None
if "services_ready" not in st.session_state:
    st.session_state.config = Config() 
    st.session_state.auth_manager = AuthManager()
    st.session_state.sub_manager = SubscriptionManager()
    st.session_state.ia_service = IAService()
    st.session_state.export_service = ExportService() 
    st.session_state.doc_service = DocumentService()
    st.session_state.quota_service = QuotaService()
    st.session_state.rule_engine = SocialRuleEngine()
    st.session_state.services_ready = True

apply_pro_design()

auth = st.session_state.auth_manager
ia = st.session_state.ia_service
docs_srv = st.session_state.doc_service 
quota = st.session_state.quota_service
engine = st.session_state.rule_engine
ui = UIComponents()

# ==============================================================================
# 2. LOGIN
# ==============================================================================
def check_password():
    if st.session_state.user_info: return True
    ui.render_top_arguments()
    ui.render_footer()
    st.markdown("<h1 style='color: #253E92;'>Social Expert France — Votre Copilote RH et Paie</h1>", unsafe_allow_html=True)
    
    t1, t2 = st.tabs(["🔐 Abonné", "🎫 J'ai un code découverte"])
    with t1:
        email = st.text_input("Email", key="login_email")
        pwd = st.text_input("Mot de passe", type="password", key="login_pwd")
        if st.button("Connexion", type="primary", use_container_width=True):
            user = auth.login(email, pwd)
            if user:
                st.session_state.user_info = user
                st.rerun()
            else:
                st.error("Erreur d'identification.")
    with t2:
        code = st.text_input("Code", type="password", key="login_code")
        if st.button("Valider", use_container_width=True):
            user = auth.login(code, None)
            if user:
                st.session_state.user_info = user
                st.rerun()
            else:
                st.error("Code invalide.")
    return False

if not check_password(): st.stop()

# ==============================================================================
# 3. APPLICATION PRINCIPALE
# ==============================================================================
ui.render_top_arguments()
ui.render_footer()

if st.session_state.user_info.get("role") == "ADMIN":
    show_legal_watch_bar()

col1, col2, _ = st.columns([1.5, 1.5, 4], gap="small")
with col1:
    st.markdown('<div class="fake-upload-btn">Charger un document</div>', unsafe_allow_html=True)
    uploaded_file = st.file_uploader("Upload", type=["pdf", "txt"], label_visibility="collapsed", key=f"uploader_{st.session_state.uploader_key}")
with col2:
    if st.button("Nouvelle session", use_container_width=True):
        st.session_state.messages = []
        st.session_state.uploader_key += 1
        st.rerun()

st.markdown("<h1 style='color:#253E92;'>SOCIAL EXPERT FRANCE - ESPACE ABONNÉ</h1>", unsafe_allow_html=True)

# Traitement Upload
user_doc_content = ""
if uploaded_file:
    with st.spinner("Lecture du document..."):
        user_doc_content = docs_srv.extract_text(uploaded_file)
        if user_doc_content: st.toast("Document analysé", icon="✅")

# ------------------------------------------------------------------------------
# AFFICHAGE DE L'HISTORIQUE (AVEC DEBUG PERSISTANT)
# ------------------------------------------------------------------------------
for msg in st.session_state.messages:
    avatar = "avatar-logo.png" if msg["role"] == "assistant" else "⚫"
    with st.chat_message(msg["role"], avatar=avatar):
        # 1. Le message
        st.markdown(msg["content"])
        
        # 2. Le Debugger (Si Admin et si présent dans le message)
        # C'est ici que ça s'affiche même après le rerun !
        if st.session_state.user_info.get("role") == "ADMIN" and "debug_data" in msg:
            with st.expander("▪️ SOURCES TECHNIQUES (PINECONE)", expanded=False):
                for src in msg["debug_data"]:
                    st.markdown(f"**📄 {src['name']}**")
                    st.caption(src['extract'][:200] + "...")

        # 3. Le Bouton PDF (Si assistant)
        if msg["role"] == "assistant" and "Désolé" not in msg["content"]:
            try:
                idx = st.session_state.messages.index(msg)
                q_text = st.session_state.messages[idx-1]["content"] if idx > 0 else "Consultation"
            except:
                q_text = "Consultation"
            
            # On vérifie juste si on peut générer
            pdf_data = st.session_state.export_service.generate_pdf(str(q_text), str(msg["content"]))
            
            if pdf_data:
                st.download_button(
                    label="📄 Télécharger le dossier PDF",
                    data=pdf_data,
                    file_name=f"Dossier_Social_{datetime.datetime.now().strftime('%H%M')}.pdf",
                    mime="application/pdf",
                    key=f"btn_pdf_{idx}"
                )

# ------------------------------------------------------------------------------
# INPUT & GÉNÉRATION
# ------------------------------------------------------------------------------
user_input = st.chat_input("Votre question juridique ou sociale...")

if user_input:
    # 1. SÉCURITÉ : SANITIZATION
    # On nettoie l'entrée avant toute utilisation
    user_input = sanitize_user_input(user_input, st.session_state.config.MAX_INPUT_LENGTH)
    
    if not user_input:
        st.warning("Message vide ou invalide.")
        st.stop()

    role = st.session_state.user_info.get("role", "GUEST")
    
    # 2. RATE LIMITING & QUOTA
    # check_quota gère le Toast "Doucement..." si clic trop rapide
    if not quota.check_quota(role):
        st.stop()
        
    st.session_state.messages.append({"role": "user", "content": user_input})
    with st.chat_message("user", avatar="⚫"):
        st.markdown(user_input)
    
    quota.increment()

    with st.chat_message("assistant", avatar="avatar-logo.png"):
        box = st.empty()
        
        # Moteurs
        matched = engine.match_rules(user_input)
        facts = engine.format_certified_facts(matched)
        
        # 3. UTILISATION DE LA CONFIG (Top K centralisé)
        docs = ia.search_documents(user_input, k=st.session_state.config.PINECONE_TOP_K)
        
        # Préparation du contexte + Sauvegarde des données de debug
        context_str = ""
        seen = []
        debug_data_list = [] # On va stocker les sources ici pour l'historique

        for d in docs:
            pname = d.metadata.get('clean_name', 'Source')
            if pname not in seen: 
                seen.append(pname)
                # On ajoute à la liste de debug
                debug_data_list.append({
                    "name": pname,
                    "extract": d.page_content
                })
            
            context_str += f"DOC: {pname}\n{d.page_content}\n\n"
        # Affichage TEMPORAIRE du debug (pendant que l'IA réfléchit)
        if st.session_state.user_info.get("role") == "ADMIN" and docs:
             with st.expander("🕵️‍♂️ SOURCES PINECONE (EN COURS)", expanded=True):
                 st.success(f"{len(docs)} documents trouvés.")

        template = """
Tu es l'Expert Social Pro 2026.

CONSIGNES DE FORME (MARKDOWN STRICT) :
1. N'utilise JAMAIS de HTML (pas de <div>, <br>, <h4>).
2. Utilise la syntaxe Markdown pour la structure :
   - Titres : ### TITRE
   - Gras : **Texte Important**
   - Listes : - Élément
3. Formatage Montants : 1 200,50 EUR (Espace millier, virgule décimale).

STRUCTURE DE RÉPONSE ATTENDUE :

### ANALYSE & RÈGLES
[Explique la règle juridique applicable. Cite les sources entre parenthèses.]

### DÉTAIL & CHIFFRES
[Pose le calcul clairement]
- Base : ...
- Taux : ...

### RÉSULTAT
**[Montant final en EUR]**

Sources utilisées : [Liste des documents]

---
CONTEXTE RAG :
{context}

FAITS CERTIFIÉS (Prioritaires) :
{certified_facts}

DOC UTILISATEUR :
{user_doc_section}

QUESTION : {question}
"""
        prompt = ChatPromptTemplate.from_template(template)
        chain = prompt | ia.get_llm() | StrOutputParser()
        
        full_response = ""
        try:
            for chunk in chain.stream({
                "context": context_str, 
                "question": user_input, 
                "certified_facts": facts,
                "user_doc_section": user_doc_content
            }):
                full_response += chunk
                box.markdown(full_response + "▌") 
            
            box.markdown(full_response)
            
            # SAUVEGARDE PERSISTANTE : On enregistre le message ET les debug_data
            st.session_state.messages.append({
                "role": "assistant", 
                "content": full_response,
                "debug_data": debug_data_list # ✅ C'EST ÇA QUI SAUVE L'AFFICHAGE
            })
            
            st.rerun()
            
        except Exception as e:
            logger.error(f"IA Error: {e}")
            box.error("Erreur de génération.")
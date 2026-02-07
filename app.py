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
    page_title="Social Expert France",
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
    st.markdown("<h1 style='color: #253E92;'>Social Expert France. Votre Copilote RH et Paie</h1>", unsafe_allow_html=True)
    
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

st.markdown("<h1 style='color:#253E92;'>Social Expert France. Espace Abonné</h1>", unsafe_allow_html=True)

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
                    label="📄 Télécharger la discussion",
                    data=pdf_data,
                    file_name=f"Dossier_Social_{datetime.datetime.now().strftime('%H%M')}.pdf",
                    mime="application/pdf",
                    key=f"btn_pdf_{idx}"
                )

# ------------------------------------------------------------------------------
# INPUT & GÉNÉRATION
# ------------------------------------------------------------------------------
user_input = st.chat_input("Posez votre question. Vous pouvez charger un document pour analyse (bouton plus haut). Ainsi que demander la rédaction d'un courrier pour l'administration.")

if user_input:
    # 1. SÉCURITÉ : SANITIZATION
    user_input = sanitize_user_input(user_input, st.session_state.config.MAX_INPUT_LENGTH)
    
    if not user_input:
        st.warning("Message vide ou invalide.")
        st.stop()

    role = st.session_state.user_info.get("role", "GUEST")
    
    # 2. RATE LIMITING & QUOTA
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
        debug_data_list = []

        for d in docs:
            pname = d.metadata.get('clean_name', 'Source')
            if pname not in seen: 
                seen.append(pname)
                debug_data_list.append({
                    "name": pname,
                    "extract": d.page_content
                })
            
            context_str += f"DOCUMENT : {pname}\n{d.page_content}\n\n"
        
        if st.session_state.user_info.get("role") == "ADMIN" and docs:
             with st.expander("🕵️‍♂️ SOURCES PINECONE (EN COURS)", expanded=True):
                 st.success(f"{len(docs)} documents trouvés.")

        # # --- EXPERT SOCIAL PRO 2026 - PROMPT AUDIT V3.8 (SÉCURITÉ MAXIMALE) ---
        template = """Tu es l'Expert Social Pro 2026, spécialiste de l'audit paie et du droit social français.

=== RÈGLE ABSOLUE N°1 : HIÉRARCHIE DES SOURCES ===
🚨 AVANT TOUTE RÉPONSE, LIS LES FAITS CERTIFIÉS CI-DESSOUS.
🚨 LES CHIFFRES DU YAML ÉCRASENT TA CONNAISSANCE INTERNE ET LE CONTEXTE RAG.

FAITS CERTIFIÉS (YAML - SOURCE PRIORITAIRE ABSOLUE) :
{certified_facts}

⚠️ EXEMPLE D'ARBITRAGE : Si le YAML indique "taux: 40%" et que tu penses "20%", tu UTILISES 40% (Barème officiel 2026).

=== RÈGLE ABSOLUE N°2 : MÉTHODE DE CALCUL AUDIT ===
A. INTERDICTIONS FORMELLES :
   ❌ Convertir les mois en années décimales (ex: écrire "2,75 ans" est INTERDIT).
   ❌ Donner un résultat sans montrer chaque étape intermédiaire.
   ❌ Arrondir les calculs intermédiaires à moins de 4 décimales.

B. MÉTHODE OBLIGATOIRE :
   ✅ Ancienneté fractionnaire : 12 ans et 9 mois = 12 + (9/12).
   ✅ Coefficients : Utilise 4 décimales avec arrondi rigoureux (ex: 1/3 = 0,3333 | 2,75/3 = 0,9167).
   ✅ EXCEPTION DE JUSTESSE (PRIORITAIRE) : Si le calcul tombe juste (ex: 4800 / 3 = 1600), utilise la valeur exacte SANS ajouter de décimales (ex: 1 600,00 EUR).
   ✅ Résultat final : 2 décimales avec les deux zéros (ex: 15 000,00 EUR).

C. EXEMPLE DE RÉFÉRENCE (PRÉCISION CHIRURGICALE) :
   - Salaire : 4 800,00 EUR | Tranche : 1/3
   - Justesse : 4 800 / 3 = 1 600 (Nombre entier)
   - Calcul Tranche 2 : (2 ans * 1 600) + (9/12 * 1 600) = 3 200 + 1 200 = 4 400,00 EUR.

=== RÈGLE ABSOLUE N°3 : FORMAT DE RÉPONSE ===
- Silence technique : Pas de politesses ("Bonjour", "Bien sûr").
- Markdown strict : ### Titres, **Gras**, - Listes.
- Nomenclature : BOSS -> (BOSS 2026 - [THÉMATIQUE]) | Code -> (Code du Travail Art. L1234-5) | YAML -> (Barème officiel 2026).

=== CONTEXTE DOCUMENTAIRE (PRIORITÉ 2) ===
{context}

=== DOCUMENT UTILISATEUR ===
{user_doc_section}

=== RAPPEL FINAL AVANT DE RÉPONDRE (VÉRIFICATION D'AUDIT) ===
✅ TAUX/MONTANTS -> YAML uniquement (ignore ta mémoire).
✅ ANCIENNETÉ -> Fractions (9/12), JAMAIS décimales (2,75).
✅ COÉFFICIENTS -> 4 décimales (0,9167) SAUF si division exacte (1600).
✅ CITATIONS -> Chaque chiffre doit avoir sa source entre parenthèses.

QUESTION : {question}

RÉPONDS STRICTEMENT SELON CE PLAN :
### ANALYSE & RÈGLES
### DÉTAIL & CHIFFRES
### RÉSULTAT
Sources utilisées :
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
            
            # SAUVEGARDE PERSISTANTE
            st.session_state.messages.append({
                "role": "assistant", 
                "content": full_response,
                "debug_data": debug_data_list
            })
            
            st.rerun()
            
        except Exception as e:
            logger.error(f"IA Error: {e}")
            box.error("Erreur de génération.")
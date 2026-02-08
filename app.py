"""
==============================================================================
SOCIAL EXPERT FRANCE - APPLICATION PRINCIPALE
VERSION : 4.0 (AUDIT & CORRECTIONS)
DATE : 08/02/2026
==============================================================================
"""

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
# 1. INITIALISATION & CONFIGURATION
# ==============================================================================
st.set_page_config(
    page_title="Social Expert France",
    page_icon="avatar-logo.png",
    layout="wide"
)

# Constantes de configuration
MAX_CONTEXT_CHARS = 10000  # ~2500 tokens pour Gemini

# Initialisation du session state
if "messages" not in st.session_state:
    st.session_state.messages = []
if "uploader_key" not in st.session_state:
    st.session_state.uploader_key = 0
if "user_info" not in st.session_state:
    st.session_state.user_info = None
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

# Raccourcis vers les services
auth = st.session_state.auth_manager
ia = st.session_state.ia_service
docs_srv = st.session_state.doc_service
quota = st.session_state.quota_service
engine = st.session_state.rule_engine
ui = UIComponents()


# ==============================================================================
# 2. AUTHENTIFICATION
# ==============================================================================
def check_password():
    """Gère l'authentification utilisateur."""
    if st.session_state.user_info:
        return True
    
    ui.render_top_arguments()
    ui.render_footer()
    st.markdown(
        "<h1 style='color: #253E92;'>Social Expert France. Votre Copilote RH et Paie</h1>",
        unsafe_allow_html=True
    )
    
    t1, t2 = st.tabs(["🔐 Abonné", "🎫 J'ai un code découverte"])
    
    with t1:
        email = st.text_input("Email", key="login_email")
        pwd = st.text_input("Mot de passe", type="password", key="login_pwd")
        if st.button("Connexion", type="primary", use_container_width=True):
            user = auth.login(email, pwd)
            if user:
                st.session_state.user_info = user
                logger.info(f"Connexion réussie: {email}")
                st.rerun()
            else:
                st.error("Erreur d'identification.")
                logger.warning(f"Échec connexion: {email}")
    
    with t2:
        code = st.text_input("Code", type="password", key="login_code")
        if st.button("Valider", use_container_width=True):
            user = auth.login(code, None)
            if user:
                st.session_state.user_info = user
                logger.info(f"Connexion code découverte réussie")
                st.rerun()
            else:
                st.error("Code invalide.")
    
    return False


if not check_password():
    st.stop()


# ==============================================================================
# 3. APPLICATION PRINCIPALE
# ==============================================================================
ui.render_top_arguments()
ui.render_footer()

# Barre admin
if st.session_state.user_info.get("role") == "ADMIN":
    show_legal_watch_bar()

# Boutons d'action
col1, col2, _ = st.columns([1.5, 1.5, 4], gap="small")
with col1:
    st.markdown('<div class="fake-upload-btn">Charger un document</div>', unsafe_allow_html=True)
    uploaded_file = st.file_uploader(
        "Upload",
        type=["pdf", "txt"],
        label_visibility="collapsed",
        key=f"uploader_{st.session_state.uploader_key}"
    )
with col2:
    if st.button("Nouvelle session", use_container_width=True):
        st.session_state.messages = []
        st.session_state.uploader_key += 1
        logger.info("Nouvelle session démarrée")
        st.rerun()

st.markdown(
    "<h1 style='color:#253E92;'>Social Expert France. Espace Abonné</h1>",
    unsafe_allow_html=True
)

# Traitement du document uploadé
user_doc_content = ""
if uploaded_file:
    with st.spinner("Lecture du document..."):
        user_doc_content = docs_srv.extract_text(uploaded_file)
        if user_doc_content:
            st.toast("Document analysé", icon="✅")
            logger.info(f"Document uploadé: {uploaded_file.name}")


# ==============================================================================
# 4. AFFICHAGE DE L'HISTORIQUE
# ==============================================================================
for msg in st.session_state.messages:
    avatar = "avatar-logo.png" if msg["role"] == "assistant" else "⚫"
    
    with st.chat_message(msg["role"], avatar=avatar):
        # 1. Affichage du message
        st.markdown(msg["content"])
        
        # 2. Debug Admin (sources Pinecone)
        if st.session_state.user_info.get("role") == "ADMIN" and "debug_data" in msg:
            with st.expander("▪️ SOURCES TECHNIQUES (PINECONE)", expanded=False):
                for src in msg["debug_data"]:
                    st.markdown(f"**📄 {src['name']}**")
                    st.caption(src['extract'][:200] + "...")
        
        # 3. Bouton PDF (si réponse assistant valide)
        if msg["role"] == "assistant" and "Désolé" not in msg["content"]:
            try:
                idx = st.session_state.messages.index(msg)
                q_text = st.session_state.messages[idx - 1]["content"] if idx > 0 else "Consultation"
            except (ValueError, IndexError) as e:
                logger.warning(f"PDF index error: {e}")
                q_text = "Consultation"
                idx = 0
            
            pdf_data = st.session_state.export_service.generate_pdf(
                str(q_text),
                str(msg["content"])
            )
            
            if pdf_data:
                st.download_button(
                    label="📄 Télécharger la discussion",
                    data=pdf_data,
                    file_name=f"Dossier_Social_{datetime.datetime.now().strftime('%H%M')}.pdf",
                    mime="application/pdf",
                    key=f"btn_pdf_{idx}"
                )


# ==============================================================================
# 5. INPUT UTILISATEUR & GÉNÉRATION IA
# ==============================================================================
user_input = st.chat_input(
    "Posez votre question. Vous pouvez charger un document pour analyse "
    "(bouton plus haut). Ainsi que demander la rédaction d'un courrier pour l'administration."
)

if user_input:
    # -------------------------------------------------------------------------
    # 5.1 SÉCURITÉ : Sanitization de l'input
    # -------------------------------------------------------------------------
    user_input = sanitize_user_input(user_input, st.session_state.config.MAX_INPUT_LENGTH)
    
    if not user_input:
        st.warning("Message vide ou invalide.")
        st.stop()
    
    role = st.session_state.user_info.get("role", "GUEST")
    
    # -------------------------------------------------------------------------
    # 5.2 RATE LIMITING & QUOTA
    # -------------------------------------------------------------------------
    if not quota.check_quota(role):
        st.stop()
    
    # Sauvegarde du message utilisateur
    st.session_state.messages.append({"role": "user", "content": user_input})
    with st.chat_message("user", avatar="⚫"):
        st.markdown(user_input)
    
    quota.increment()
    
    # -------------------------------------------------------------------------
    # 5.3 GÉNÉRATION DE LA RÉPONSE
    # -------------------------------------------------------------------------
    with st.chat_message("assistant", avatar="avatar-logo.png"):
        box = st.empty()
        
        # =================================================================
        # MOTEUR DE RÈGLES YAML (V4.0)
        # =================================================================
        matched = engine.match_rules(user_input)
        
        # Log si aucune règle spécifique matchée (les vitales sont toujours là)
        if len(matched) <= 6:  # Seulement les règles vitales
            logger.info(f"Peu de règles matchées pour: {user_input[:50]}...")
        
        facts = engine.format_certified_facts(matched)
        
        # =================================================================
        # RECHERCHE DOCUMENTAIRE PINECONE
        # =================================================================
        docs = ia.search_documents(user_input, k=st.session_state.config.PINECONE_TOP_K)
        
        # Préparation du contexte avec limitation de taille
        context_str = ""
        seen = []
        debug_data_list = []
        context_truncated = False
        
        for d in docs:
            # Vérifier la limite de contexte
            if len(context_str) > MAX_CONTEXT_CHARS:
                context_truncated = True
                logger.info(f"Contexte RAG tronqué à {MAX_CONTEXT_CHARS} caractères.")
                break
            
            pname = d.metadata.get('clean_name', 'Source')
            if pname not in seen:
                seen.append(pname)
                debug_data_list.append({
                    "name": pname,
                    "extract": d.page_content
                })
            
            context_str += f"DOCUMENT : {pname}\n{d.page_content}\n\n"
        
        # Debug Admin : affichage des sources en cours
        if st.session_state.user_info.get("role") == "ADMIN" and docs:
            with st.expander("🕵️‍♂️ SOURCES PINECONE (EN COURS)", expanded=True):
                st.success(f"{len(docs)} documents trouvés.")
                if context_truncated:
                    st.warning(f"⚠️ Contexte tronqué ({MAX_CONTEXT_CHARS} caractères max)")
        
        # =================================================================
        # PROMPT EXPERT SOCIAL PRO 2026 - VERSION 4.0
        # =================================================================
        template = """Tu es l'Expert Social Pro 2026, spécialiste de l'audit paie et du droit social français.

=== CONTEXTE TEMPOREL ===
📅 Date du jour : {current_date}
📅 Année de référence des barèmes : 2026

=== RÈGLE ABSOLUE N°1 : HIÉRARCHIE DES SOURCES ===
🚨 AVANT TOUTE RÉPONSE, LIS LES FAITS CERTIFIÉS CI-DESSOUS.
🚨 LES CHIFFRES DU YAML ÉCRASENT TA CONNAISSANCE INTERNE ET LE CONTEXTE RAG.

FAITS CERTIFIÉS (YAML - SOURCE PRIORITAIRE ABSOLUE) :
{certified_facts}

⚠️ EXEMPLES D'ARBITRAGE OBLIGATOIRES :
- Forfait social rupture conventionnelle = 40,0% (YAML), PAS 20% (taux standard).
- Télétravail 3 jours/semaine = 33,00 €/mois (11 € × 3), PAS un autre calcul.
- SMIC 2026 = 1 823,03 €/mois, PAS une ancienne valeur.
- Indemnité légale licenciement = 1/4 mois (0,2500) jusqu'à 10 ans, puis 1/3 (0,3333).

=== RÈGLE ABSOLUE N°2 : MÉTHODE DE CALCUL AUDIT ===
A. INTERDICTIONS FORMELLES :
   ❌ Convertir les mois en années décimales (ex: écrire "2,75 ans" est INTERDIT).
   ❌ Donner un résultat sans montrer chaque étape intermédiaire.
   ❌ Arrondir les calculs intermédiaires à moins de 4 décimales.
   ❌ Inventer des chiffres non présents dans les sources.

B. MÉTHODE OBLIGATOIRE :
   ✅ Ancienneté fractionnaire : 12 ans et 9 mois = 12 + (9/12).
   ✅ Coefficients : Utilise 4 décimales avec arrondi rigoureux (ex: 1/3 = 0,3333 | 2,75/3 = 0,9167).
   ✅ Résultat final : 2 décimales avec les deux zéros (ex: 15 000,00 EUR).

C. EXCEPTION DE JUSTESSE (PRIORITÉ MAXIMALE) :
   🎯 AVANT d'appliquer un coefficient (0,2500 ou 0,3333), VÉRIFIE si la division tombe juste :
   - 4800 ÷ 4 = 1200 (JUSTE) → Utilise 1 200,00 EUR, PAS 4800 × 0,2500
   - 4800 ÷ 3 = 1600 (JUSTE) → Utilise 1 600,00 EUR, PAS 4800 × 0,3333
   - 5000 ÷ 3 = 1666,6667 (PAS JUSTE) → Utilise 5000 × 0,3333 = 1 666,50 EUR
   
D. EXEMPLE DE RÉFÉRENCE (PRÉCISION CHIRURGICALE) :
   - Salaire : 4 800,00 EUR | Ancienneté : 12 ans et 9 mois
   - Tranche 1 (10 ans) : 4800 ÷ 4 = 1200 (JUSTE) → 10 × 1 200 = 12 000,00 EUR
   - Tranche 2 (2 ans 9 mois) : 4800 ÷ 3 = 1600 (JUSTE) → (2 + 9/12) × 1 600 = 2,75 × 1 600 = 4 400,00 EUR
   - TOTAL : 12 000,00 + 4 400,00 = 16 400,00 EUR

=== RÈGLE ABSOLUE N°3 : FORMAT DE RÉPONSE ===
- Silence technique : Pas de politesses ("Bonjour", "Bien sûr", "Je vous en prie").
- Markdown strict : ### Titres, **Gras**, - Listes.
- Nomenclature des sources (OBLIGATOIRE après chaque chiffre) :
  * BOSS -> (BOSS 2026 - [THÉMATIQUE])
  * Code du Travail -> (Code du Travail Art. L1234-5)
  * Code Sécurité Sociale -> (CSS Art. L136-8)
  * YAML -> (Barème officiel 2026)

=== CONTEXTE DOCUMENTAIRE (PRIORITÉ 2 - APRÈS YAML) ===
{context}

=== DOCUMENT UTILISATEUR (SI FOURNI) ===
{user_doc_section}

=== RAPPEL FINAL AVANT DE RÉPONDRE (VÉRIFICATION D'AUDIT) ===
✅ TAUX/MONTANTS -> YAML uniquement (ignore ta mémoire interne).
✅ ANCIENNETÉ -> Fractions (9/12), JAMAIS décimales (2,75).
✅ COEFFICIENTS -> 4 décimales (0,9167) SAUF si division exacte (1600).
✅ CITATIONS -> Chaque chiffre doit avoir sa source entre parenthèses.
✅ SI AUCUNE INFO DISPONIBLE -> Dis clairement "Cette information n'est pas dans mes sources."

QUESTION : {question}

RÉPONDS STRICTEMENT SELON CE PLAN :
### ANALYSE & RÈGLES
[Explique les règles applicables avec leurs sources]

### DÉTAIL & CHIFFRES
[Montre chaque étape de calcul si nécessaire]

### RÉSULTAT
[Donne la réponse finale claire et concise]

Sources utilisées : [Liste des sources entre parenthèses]
"""
        
        prompt = ChatPromptTemplate.from_template(template)
        chain = prompt | ia.get_llm() | StrOutputParser()
        
        full_response = ""
        
        try:
            # Streaming de la réponse
            for chunk in chain.stream({
                "context": context_str,
                "question": user_input,
                "certified_facts": facts,
                "user_doc_section": user_doc_content if user_doc_content else "(Aucun document fourni)",
                "current_date": datetime.datetime.now().strftime("%d/%m/%Y")
            }):
                full_response += chunk
                box.markdown(full_response + "▌")
            
            # Affichage final
            box.markdown(full_response)
            
            # Sauvegarde persistante avec données de debug
            st.session_state.messages.append({
                "role": "assistant",
                "content": full_response,
                "debug_data": debug_data_list
            })
            
            logger.info(f"Réponse générée ({len(full_response)} chars)")
            st.rerun()
        
        except Exception as e:
            logger.error(f"IA Error: {e}", exc_info=True)
            error_msg = (
                "Désolé, une erreur technique est survenue. "
                "Veuillez reformuler votre question ou réessayer dans quelques instants."
            )
            box.error(error_msg)
            
            # Sauvegarde de l'erreur dans l'historique
            st.session_state.messages.append({
                "role": "assistant",
                "content": error_msg,
                "debug_data": []
            })
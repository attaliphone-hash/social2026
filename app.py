import streamlit as st
import time
import os
import re
from dotenv import load_dotenv

# Charge les variables d'environnement
load_dotenv()

# --- IMPORTS ARCHITECTURE V2 ---
from core.config import Config
from core.auth_manager import AuthManager
from core.subscription_manager import SubscriptionManager
from services.ia_service import IAService
from services.document_service import DocumentService
from services.quota_service import QuotaService
from services.legal_watch import show_legal_watch_bar
from ui.styles import apply_pro_design
from ui.components import UIComponents

# ✅ Correction Audit : Import centralisé (Suppression de la duplication)
from utils.helpers import clean_source_name, logger

# --- IMPORTS MOTEUR & IA ---
from rules.engine import SocialRuleEngine
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

# ==============================================================================
# 1. INITIALISATION & CONFIGURATION
# ==============================================================================
st.set_page_config(
    page_title="Expert Social Pro 2026 - Le Copilote RH et Paie",
    page_icon="avatar-logo.png",
    layout="wide"
)

# Initialisation du Session State
if "messages" not in st.session_state: st.session_state.messages = []
if "uploader_key" not in st.session_state: st.session_state.uploader_key = 0
if "query_count" not in st.session_state: st.session_state.query_count = 0
if "user_info" not in st.session_state: st.session_state.user_info = None

if "services_ready" not in st.session_state:
    # ✅ Note : L'ordre d'initialisation suit la recommandation B de l'audit
    st.session_state.config = Config() 
    st.session_state.auth_manager = AuthManager()
    st.session_state.sub_manager = SubscriptionManager()
    st.session_state.ia_service = IAService()
    st.session_state.doc_service = DocumentService()
    st.session_state.quota_service = QuotaService()
    st.session_state.rule_engine = SocialRuleEngine()
    st.session_state.services_ready = True

apply_pro_design()

auth = st.session_state.auth_manager
sub = st.session_state.sub_manager
ia = st.session_state.ia_service
docs_srv = st.session_state.document_service # Ajusté selon le nom de classe standard
quota = st.session_state.quota_service
engine = st.session_state.rule_engine
ui = UIComponents()

# ==============================================================================
# 2. NETTOYAGE DES SOURCES (Désormais géré par utils/helpers.py)
# ==============================================================================
# ✅ Correction Audit : La fonction locale clean_source_name a été supprimée.
# Elle est maintenant importée de utils.helpers pour garantir une source unique.

# ==============================================================================
# 3. PAGE DE LOGIN
# ==============================================================================
def check_password():
    if st.session_state.user_info:
        return True

    ui.render_top_arguments()
    ui.render_footer()

    st.markdown("<h1 style='text-align: left; color: #253E92;'>SOCIAL EXPERT FRANCE — VOTRE COPILOTE RH & PAIE EN 2026.</h1>", unsafe_allow_html=True)
    
    t1, t2 = st.tabs(["🔐 Je suis abonné", "🎫 J'ai un code découverte"])
    
    with t1:
        email = st.text_input("Email", key="login_email")
        pwd = st.text_input("Mot de passe", type="password", key="login_pwd")
        if st.button("Connexion", use_container_width=True, type="primary"):
            user = auth.login(email, pwd)
            if user:
                st.session_state.user_info = user
                st.rerun()
            else:
                st.error("Identifiants incorrects.")
        
        st.markdown("---")
        st.subheader("PAS ENCORE ABONNÉ ?")
        ui.render_subscription_cards()

    with t2:
        code = st.text_input("Code", type="password", key="login_code")
        if st.button("Valider", use_container_width=True):
            user = auth.login(code, None) # password=None pour le mode code
            if user:
                st.session_state.user_info = user
                st.rerun()
            else:
                st.error("Code erroné.")
    return False

if not check_password():
    st.stop()

# ==============================================================================
# 4. DASHBOARD (ESPACE ABONNÉS)
# ==============================================================================

ui.render_top_arguments()
ui.render_footer()

if st.session_state.user_info.get("role") == "ADMIN":
    show_legal_watch_bar()

col_act1, col_act2, _ = st.columns([1.5, 1.5, 4], vertical_alignment="center", gap="small")
with col_act1:
    st.markdown('<div class="fake-upload-btn">Charger un document</div>', unsafe_allow_html=True)
    uploaded_file = st.file_uploader("Upload", type=["pdf", "txt"], label_visibility="collapsed", key=f"uploader_{st.session_state.uploader_key}")

with col_act2:
    if st.button("Nouvelle session", use_container_width=True):
        st.session_state.messages = []
        st.session_state.uploader_key += 1
        st.rerun()

st.markdown("<h1 style='color:#253E92; margin-top:10px;'>SOCIAL EXPERT FRANCE ESPACE ABONNÉS</h1>", unsafe_allow_html=True)

user_doc_content = ""
if uploaded_file:
    with st.spinner("Analyse du document en cours..."):
        user_doc_content = docs_srv.extract_text(uploaded_file)
        if user_doc_content:
            st.toast(f"📎 {uploaded_file.name} analysé avec succès", icon="✅")

for msg in st.session_state.messages:
    with st.chat_message(msg["role"], avatar=("avatar-logo.png" if msg["role"] == "assistant" else None)):
        st.markdown(msg["content"], unsafe_allow_html=True)

user_input = None
if "pending_prompt" in st.session_state:
    user_input = st.session_state.pending_prompt
    del st.session_state.pending_prompt
else:
    user_input = st.chat_input("Posez une question, chargez un document ou demandez une rédaction")

if user_input:
    role = st.session_state.user_info.get("role", "GUEST")
    if not quota.check_quota(role):
        st.warning("🛑 Limite de requêtes atteinte.")
        ui.render_subscription_cards()
        st.stop()
        
    st.session_state.messages.append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.markdown(user_input)
    
    quota.increment()

    with st.chat_message("assistant", avatar="avatar-logo.png"):
        box = st.empty()
        
        matched = engine.match_rules(user_input)
        facts = engine.format_certified_facts(matched)

        # ✅ 1. RECHERCHE
        docs = ia.search_documents(user_input, k=6)
        context_str = ""
        sources_seen = []
        
        for d in docs:
            # Récupération du label système propre déjà traité par helpers.py
            pretty_name = d.metadata.get('clean_name', 'Source Inconnue')
            
            if pretty_name not in sources_seen:
                sources_seen.append(pretty_name)
            
            context_str += f"DOCUMENT : {pretty_name}\n{d.page_content}\n\n"

        # ✅ 2. LE MOUCHARD ADMIN (DEBUG)
        if st.session_state.user_info.get("role") == "ADMIN":
            with st.expander("🕵️‍♂️ MODE ADMIN : VOIR LE CERVEAU (DEBUG)", expanded=False):
                if not docs:
                    st.error("❌ PINECONE RENVOIE 0 DOCUMENT !")
                else:
                    st.success(f"✅ {len(docs)} documents injectés dans le contexte.")
                    for i, d in enumerate(docs):
                        st.markdown(f"**📄 Doc {i+1} :** `{d.metadata.get('clean_name')}`")
                        st.caption(f"📝 Extrait : {d.page_content[:200]}...")
        
        # ==============================================================================

        template = """
Tu es l'Expert Social Pro 2026.

💎 RÈGLES DE FORME & VOCABULAIRE (CRITIQUE) :
1. Génère du **HTML BRUT** sans balises de code.
2. ⚠️ FORMATAGE MONÉTAIRE FR : Utilise TOUJOURS la virgule pour les décimales et un espace pour les milliers (ex: 1 950,00 €).
3. Affiche systématiquement 2 décimales pour tous les montants en Euros.
4. Pas de Markdown pour les titres.
5. ⛔ SILENCE TECHNIQUE OBLIGATOIRE.

---- 1. RÈGLES DE PRIORITÉ (LOGIQUE DE CASCADE) ---
A. DONNÉES CHIFFRÉES : Priorité 1 aux Faits Certifiés (YAML).
B. RAISONNEMENT JURIDIQUE : Priorité 2 aux Documents Contextuels (RAG).

--- 2. LOGIQUE MÉTIER & MATHÉMATIQUE ---
Calcul strict selon les protocoles certifiés.

--- 3. GESTION DES SOURCES (EXTRACTION CHIRURGICALE) ---
- **RÈGLE D'OR :** Ne crée JAMAIS une source générique si un article précis existe.
- **ALGORITHME DE SCAN ET SYNCHRONISATION :**
  1. **Priorité au Label Système :** Pour chaque document, utilise EXCLUSIVEMENT le nom nettoyé fourni après 'DOCUMENT :'.
  2. **Extraction de l'Article :** Cherche 'SOURCE :' ou 'Art. L...'.
  3. **Reconstruction Obligatoire :** {{Nom_Nettoyé_Système}} - {{Référence_Article}}.
- **INTERDICTION :** Ne retire JAMAIS la mention '2026'.

--- 4. CONTEXTE RAG ---
Faits Certifiés (Priorité 1) :
{certified_facts}

Documents Contextuels (Priorité 2) :
{context}

{user_doc_section}

--- 5. TEMPLATE DE RÉPONSE (HTML STYLYSÉ) ---
[Mode Rédaction : Texte Brut / Mode Standard : HTML]

👇 DÉBUT DU TEMPLATE HTML 👇
<h4 style="color: #024c6f; border-bottom: 1px solid #ddd;">Analyse & Règles</h4>
<ul>
    <li>[Règle juridique] <em style="color:#666;">(Source : [Art. extrait à l'étape 3])</em></li>
</ul>
<h4 style="color: #024c6f; border-bottom: 1px solid #ddd; margin-top:20px;">Détail & Chiffres</h4>
<div style="background-color: #f9f9f9; padding: 15px; border-radius: 5px;">
    <strong>Données clés :</strong> [Valeurs]<br>
    <strong>Calcul :</strong> [Étapes]
</div>
<div style="background-color: #f0f8ff; padding: 20px; border-left: 5px solid #024c6f; margin: 25px 0;">
    <h2 style="color: #024c6f; margin-top: 0;">🎯 RÉSULTAT</h2>
    <p style="font-size: 18px;"><strong>[Montant]</strong></p>
</div>
<div style="margin-top: 20px; border-top: 1px solid #ccc; font-size: 11px; color: #666;">
    <strong>Sources utilisées :</strong> [Lister précisément selon Section 3]<br>
    <em>Données certifiées conformes aux barèmes 2026.</em>
</div>

QUESTION : {question}
"""
        prompt = ChatPromptTemplate.from_template(template)
        # ✅ Utilisation systématique de gemini-2.0-flash
        chain = prompt | ia.get_llm() | StrOutputParser()
        
        full_response = ""
        try:
            for chunk in chain.stream({
                "context": context_str, 
                "question": user_input, 
                "certified_facts": facts,
                "user_doc_section": f"Document Utilisateur : {user_doc_content}" if user_doc_content else ""
            }):
                full_response += chunk
                box.markdown(full_response + "▌", unsafe_allow_html=True)
            
            box.markdown(full_response, unsafe_allow_html=True)
            st.session_state.messages.append({"role": "assistant", "content": full_response})
            
        except Exception as e:
            logger.error(f"Erreur Génération : {e}")
            box.error(f"Une erreur est survenue lors de la génération de la réponse : {e}")
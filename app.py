import streamlit as st
import time
import os
import re

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
    # 1. ON CRÉE LA CONFIG EN PREMIER (Crucial pour les autres services)
    st.session_state.config = Config() 
    
    # 2. PUIS ON LANCE LES MANAGERS
    st.session_state.auth_manager = AuthManager()
    st.session_state.sub_manager = SubscriptionManager()
    st.session_state.ia_service = IAService()
    st.session_state.doc_service = DocumentService()
    st.session_state.quota_service = QuotaService()
    st.session_state.rule_engine = SocialRuleEngine()
    
    st.session_state.services_ready = True

# Application du design
apply_pro_design()

# Raccourcis pour lisibilité
auth = st.session_state.auth_manager
sub = st.session_state.sub_manager
ia = st.session_state.ia_service
docs_srv = st.session_state.doc_service
quota = st.session_state.quota_service
engine = st.session_state.rule_engine
ui = UIComponents()

# ==============================================================================
# 2. NETTOYAGE DES SOURCES (Helper)
# ==============================================================================
def clean_source_name(filename, category="AUTRE"):
    """Transforme les noms techniques en noms lisibles pour l'utilisateur"""
    filename = os.path.basename(filename).replace('.pdf', '').replace('.txt', '')
    
    if "Code_Travail" in filename or "Code Travail" in filename:
        return "Code du Travail 2026"
    elif "Code_Secu" in filename or "Code Secu" in filename:
        return "Code de la Sécurité Sociale 2026"
    elif category == "REF" or filename.startswith("REF_"):
        return "Barèmes Officiels 2026"
    elif category == "DOC" or filename.startswith("DOC_"):
        return "BOSS 2026 et Jurisprudences"
    
    return filename.replace('_', ' ')

# ==============================================================================
# 3. PAGE DE LOGIN
# ==============================================================================
def check_password():
    if st.session_state.user_info:
        return True

    ui.render_top_arguments()
    ui.render_footer()

    st.markdown("<h1 style='text-align: left; color: #253E92;'>EXPERT SOCIAL PRO — VOTRE COPILOTE RH & PAIE EN 2026.</h1>", unsafe_allow_html=True)
    st.markdown("<h2 style='text-align: left; color: #253E92;'>Des règles officielles. Des calculs sans erreur. Des décisions que vous pouvez défendre.</h2>", unsafe_allow_html=True)
    st.markdown("<br>", unsafe_allow_html=True)

    t1, t2 = st.tabs(["🔐 Je suis abonné", "J'ai un code découverte"])
    
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
        st.write("Débloquez l'accès illimité et le mode Expert Social 2026.")
        ui.render_subscription_cards()

    with t2:
        code = st.text_input("Code", type="password", key="login_code")
        if st.button("Valider", use_container_width=True):
            user = auth.login(code, code)
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

# 1. ARGUMENTS
ui.render_top_arguments()

# 2. FOOTER
ui.render_footer()

# 3. VEILLE JURIDIQUE
show_legal_watch_bar()

# 4. ACTIONS (UPLOAD / NOUVELLE SESSION)
col_act1, col_act2, _ = st.columns([1.5, 1.5, 4], vertical_alignment="center", gap="small")
with col_act1:
    st.markdown('<div class="fake-upload-btn">Charger un document</div>', unsafe_allow_html=True)
    uploaded_file = st.file_uploader("Upload", type=["pdf", "txt"], label_visibility="collapsed", key=f"uploader_{st.session_state.uploader_key}")

with col_act2:
    if st.button("Nouvelle session", use_container_width=True):
        st.session_state.messages = []
        st.session_state.uploader_key += 1
        st.rerun()

# 5. TITRE ESPACE ABONNÉS
st.markdown("<h1 style='color:#253E92; margin-top:10px;'>EXPERT SOCIAL PRO ESPACE ABONNÉS</h1>", unsafe_allow_html=True)

# 6. ANALYSE DU DOCUMENT UPLOADÉ
user_doc_content = ""
if uploaded_file:
    with st.spinner("Analyse du document en cours..."):
        user_doc_content = docs_srv.extract_text(uploaded_file)
        if user_doc_content:
            st.toast(f"📎 {uploaded_file.name} analysé avec succès", icon="✅")

# 7. ONBOARDING (EXEMPLES)
if not st.session_state.messages:
    st.markdown("<br>", unsafe_allow_html=True)
    c1, c2, c3 = st.columns(3, gap="large")
    with c1:
        st.markdown("<div style='text-align: center; font-size: 12px;font-weight: bold; color: #2c3e50; margin-bottom: 5px;'>Exemple Apprentissage 2026</div>", unsafe_allow_html=True)
        st.markdown("<div style='text-align: center; font-size: 11px; color: #666; font-style: italic; min-height: 45px;'>\"Je veux embaucher un apprenti de 22 ans payé au SMIC. Quel est le coût exact et les exonérations en 2026 ?\"</div>", unsafe_allow_html=True)
        if st.button("Tester ce cas", key="btn_start_1", use_container_width=True):
            st.session_state.pending_prompt = "Je veux embaucher un apprenti de 22 ans payé au SMIC. Quel est le coût exact et les exonérations en 2026 ?"
            st.rerun()
    with c2:
        st.markdown("<div style='text-align: center; font-size: 12px;font-weight: bold; color: #2c3e50; margin-bottom: 5px;'>Exemple Licenciement</div>", unsafe_allow_html=True)
        st.markdown("<div style='text-align: center; font-size: 11px; color: #666; font-style: italic; min-height: 45px;'>\"Calcule l'indemnité de licenciement pour un cadre avec 12 ans et 5 mois d'ancienneté ayant un salaire de référence de 4500€.\"</div>", unsafe_allow_html=True)
        if st.button("Tester ce cas", key="btn_start_2", use_container_width=True):
            st.session_state.pending_prompt = "Calcule l'indemnité de licenciement pour un cadre avec 12 ans et 5 mois d'ancienneté ayant un salaire de référence de 4500€."
            st.rerun()
    with c3:
        st.markdown("<div style='text-align: center; font-size: 12px;font-weight: bold; color: #2c3e50; margin-bottom: 5px;'>Exemple Avantage Auto</div>", unsafe_allow_html=True)
        st.markdown("<div style='text-align: center; font-size: 11px; color: #666; font-style: italic; min-height: 45px;'>\"Comment calculer l'avantage voiture électrique en 2026 ?\"</div>", unsafe_allow_html=True)
        if st.button("Tester ce cas", key="btn_start_3", use_container_width=True):
            st.session_state.pending_prompt = "Comment calculer l'avantage en nature pour une voiture électrique de société en 2026 ?"
            st.rerun()
    st.markdown("---")

# 8. AFFICHAGE DES MESSAGES
for msg in st.session_state.messages:
    with st.chat_message(msg["role"], avatar=("avatar-logo.png" if msg["role"] == "assistant" else None)):
        st.markdown(msg["content"], unsafe_allow_html=True)

# 9. GESTION DE LA SAISIE
user_input = None
if "pending_prompt" in st.session_state:
    user_input = st.session_state.pending_prompt
    del st.session_state.pending_prompt
else:
    user_input = st.chat_input("Posez votre situation concrète (ex: règles, calcul paie...) et/ou chargez un document pour analyse")

if user_input:
    # Quota check
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
        
        # Moteur de règles : Extraction des faits (Correction : Utilisation de l'input brut pour le matching)
        matched = engine.match_rules(user_input)
        facts = engine.format_certified_facts(matched)

        # RAG : Recherche de documents
        docs = ia.search_documents(user_input, k=6)
        context_str = ""
        sources_seen = []
        for d in docs:
            raw_name = d.metadata.get('source', 'Inconnu')
            cat = d.metadata.get('category', 'AUTRE')
            pretty_name = clean_source_name(raw_name, cat)
            if pretty_name not in sources_seen:
                sources_seen.append(pretty_name)
            context_str += f"[SOURCE: {pretty_name}]\n{d.page_content}\n\n"



# --- LE CERVEAU V80 (PROMPT ARMOR / ANTI-LAXISME) ---
        template = """
Tu es l'Expert Social Pro 2026.

💎 RÈGLES DE FORME ÉLITE (CRITIQUE) :
1. Génère du **HTML BRUT** sans balises de code (jamais de ```html).
2. ⚠️ FORMATAGE MONÉTAIRE FR : Utilise TOUJOURS la virgule pour les décimales et un espace pour les milliers (ex: 1 950,00 €).
3. Affiche systématiquement 2 décimales pour tous les montants en Euros.
4. Pas de Markdown pour les titres (utilise uniquement <h4 style="...">).

--- 1. RÈGLES DE PRIORITÉ & INTELLIGENCE (DISCIPLINE SÉLECTIVE) ---

A. POUR LES DONNÉES CHIFFRÉES (Taux, Seuils, Montants) :
- **RÈGLE ABSOLUE :** Les "Faits Certifiés" (YAML) fournis ci-dessous sont la SEULE vérité.
- **INTERDICTION :** N'utilise JAMAIS ta mémoire pour générer un montant 2026 (ex: SMIC, Plafond SS, Taux) s'il n'est pas dans le YAML. Trouve la valeur dans le bloc YAML contextuel.

B. POUR LE RAISONNEMENT JURIDIQUE (Droit du travail) :
- **PRIORITÉ :** Utilise les documents contextuels (RAG) pour l'analyse.
- **AUTORISATION :** Si les documents ne couvrent pas un point de droit général, utilise tes connaissances juridiques internes (Code du travail).
- **MENTION :** Si tu utilises tes connaissances internes, précise : "Selon les principes généraux du droit du travail".

--- 2. LOGIQUE MÉTIER & MATHÉMATIQUE ---

A. CALCUL DU COÛT EMPLOYEUR (Règle d'Or) :
- Formule : (Salaire Brut + Cotisations Patronales) - Aides de l'État.
- INTERDICTION ABSOLUE de soustraire une aide directement du Salaire Brut.
- Apprentissage : Intégrer l'Aide Unique (valeur dans YAML) en déduction finale.

B. GESTION DES DONNÉES MANQUANTES :
- Si une donnée critique manque (ex: taux de cotisations patronales) :
  1. ⛔ INTERDICTION STRICTE : Ne simule AUCUN chiffre dans la section "Détail & Chiffres".
  2. SPÉCIFICITÉ APPRENTISSAGE : Mentionne l'exonération quasi-totale des cotisations.
  3. DANS LA ZONE DE SIMULATION (Bloc Beige) : Fais ton calcul avec un taux hypothétique (ex: Taux légal ou conventionnel estimé) en le mentionnant explicitement.

C. VIGILANCE MATHÉMATIQUE & PROTOCOLES :
- PROTOCOLES YAML : Applique STRICTEMENT les méthodes du PROTOCOLE_CALCUL_SOCIAL présent dans le YAML.
- INDEMNITÉ RUPTURE : Applique les paliers légaux (1/4 de mois <10 ans, 1/3 >10 ans) sauf si le YAML ou le RAG impose une CCN plus favorable.
- TEMPS DE TRAVAIL : Conversion décimale obligatoire (Minutes / 60).
- IJSS SÉCU : Diviseur 91,25 (sauf règle contraire explicite dans le YAML).

D. PRÉCISION JURIDIQUE (S'APPUYER SUR LE YAML) :
- Pour le SBI (Solde Bancaire Insaisissable) et l'Exonération Rupture (2 PASS), réfère-toi aux valeurs exactes présentes dans les Faits Certifiés (YAML).

--- 3. GESTION DES SOURCES ---
- Pour chaque information, cite la source.
- SI L'INFO VIENT DU YAML : Affiche la source indiquée dans le champ 'source' du YAML.
- SI LE CHAMP 'SOURCE' EST VIDE : Afficher "Barèmes Officiels 2026".

--- 4. CONTEXTE RAG ---
Faits Certifiés (YAML - Priorité 1) :
{certified_facts}

Documents Contextuels (RAG - Priorité 2) :
{context}

Document Utilisateur :
{user_doc_section}

--- 5. TEMPLATE DE RÉPONSE (HTML STYLYSÉ) ---

⛔ INTERDICTION ABSOLUE de mettre du texte hors balises ou des ```.

<h4 style="color: #024c6f; border-bottom: 1px solid #ddd;">Analyse & Règles</h4>
<ul>
    <li>[Règle juridique avec Citation précise]</li>
</ul>

<h4 style="color: #024c6f; border-bottom: 1px solid #ddd; margin-top:20px;">Détail & Chiffres</h4>
<div style="background-color: #f9f9f9; padding: 15px; border-radius: 5px; border: 1px solid #eee;">
    <strong>Données clés :</strong> [Valeurs officielles du YAML utilisées]<br>
    <strong>Calcul :</strong><br>
    <ul>
       <li>[Étape 1 : Formule claire]</li>
       <li>[Étape 2 : Application numérique stricte]</li>
    </ul>
</div>

<div style="background-color: #f0f8ff; padding: 20px; border-left: 5px solid #024c6f; margin: 25px 0;">
    <h2 style="color: #024c6f; margin-top: 0;">🎯 RÉSULTAT</h2>
    <p style="font-size: 18px;"><strong>[Montant Final Officiel]</strong></p>
    <p style="font-size: 14px; margin-top: 5px; color: #444;">[Conclusion contextuelle]</p>
</div>

[INSTRUCTION : INSÉRER LE BLOC SUIVANT UNIQUEMENT SI DES DONNÉES MANQUANTES ONT NÉCESSITÉ UNE SIMULATION]
<hr style="border: 0; border-top: 1px dashed #253E92; margin: 30px 0;">
<div style="background-color: #fdf6e3; padding: 20px; border-radius: 8px; border: 1px solid #e6dbb9;">
    <h4 style="color: #856404; margin-top: 0;">🔍 APPLICATION PRATIQUE (SIMULATION)</h4>
    <p style="font-size: 13px; color: #856404; font-style: italic;">
        Faute de données personnalisées complètes, voici une projection :
    </p>
    [Détail chiffré basé sur hypothèses clairement énoncées]
</div>

<div style="margin-top: 20px; border-top: 1px solid #ccc; padding-top: 10px; padding-bottom: 25px; font-size: 11px; color: #666; line-height: 1.5;">
    <strong>Sources utilisées :</strong> {sources_list}<br>
    <em>Données certifiées conformes aux barèmes 2026.</em><br>
    <span style="font-style: italic; color: #626267;">Vérifiez toujours votre Convention Collective.</span>
</div>

QUESTION : {question}
"""

        # --- PRÉPARATION DES SOURCES ---
        if facts and not sources_seen:
            display_sources = "Données officielles 2026"
        elif sources_seen:
            display_sources = ", ".join(sources_seen)
        else:
            display_sources = "Documentation officielle 2026"

        # Exécution de la chaîne IA
        prompt = ChatPromptTemplate.from_template(template)
        chain = prompt | ia.get_llm() | StrOutputParser()
        
        full_response = ""
        try:
            for chunk in chain.stream({
                "context": context_str, 
                "question": user_input, 
                "sources_list": display_sources, 
                "certified_facts": facts,
                "user_doc_section": f"Document Utilisateur : {user_doc_content}" if user_doc_content else ""
            }):
                full_response += chunk
                box.markdown(full_response + "▌", unsafe_allow_html=True)
            
            box.markdown(full_response, unsafe_allow_html=True)
            st.session_state.messages.append({"role": "assistant", "content": full_response})
            
        except Exception as e:
            box.error(f"Une erreur est survenue lors de la génération de la réponse : {e}")
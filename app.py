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

        # Préparation des valeurs dynamiques pour le prompt
        sbi_val = f"{engine.get_rule_value('SBI_2026', 'montant') or 645.50:,.2f} €".replace(",", "X").replace(".", ",").replace("X", " ")
        pass_val = f"{(engine.get_rule_value('PASS_2026', 'annuel') or 48060)*2:,.2f} €".replace(",", "X").replace(".", ",").replace("X", " ")

        # --- LE CERVEAU V75 (PROMPT ELITE) ---
        template = """
Tu es l'Expert Social Pro 2026.

💎 RÈGLES DE FORME ÉLITE (CRITIQUE) :
1. Génère du **HTML BRUT** sans balises de code.
2. ⚠️ FORMATAGE MONÉTAIRE FR : Utilise TOUJOURS la virgule pour les décimales et un espace pour les milliers (ex: 1 950,00 €).
3. Affiche systématiquement 2 décimales pour tous les montants en Euros.
4. Pas de Markdown pour les titres (utilise uniquement <h4 style="...">).

--- 1. SÉCURITÉ & DATA ---
- Utilise STRICTEMENT les valeurs fournies. ⛔ Ne jamais inventer de taux.

--- 2. LOGIQUE MÉTIER & MATHÉMATIQUE (CERVEAU V75) ---

A. CALCUL DU COÛT EMPLOYEUR (Règle d'Or) :
- Formule : (Salaire Brut + Cotisations Patronales) - Aides de l'État.
- INTERDICTION ABSOLUE de soustraire une aide directement du Salaire Brut. Le Brut est toujours dû au salarié.
- Apprentissage : Intégrer l'Aide Unique (6 000 €/an soit 500 €/mois) en déduction finale.

B. GESTION DES DONNÉES MANQUANTES :
- Si une donnée critique manque (ex: taux de cotisations patronales) :
  1. ⛔ INTERDICTION STRICTE : Ne simule AUCUN chiffre dans les sections "Détail & Chiffres" ou "RÉSULTAT". Utilise des formules textuelles.
  2. SPÉCIFICITÉ APPRENTISSAGE : Si la question porte sur un apprenti, précise TOUJOURS dans ton analyse que les cotisations patronales sont souvent proches de zéro (Exonération quasi-totale via la Réduction Générale) pour les salaires proches du SMIC.
  3. DANS LA ZONE DE SIMULATION : Fais ton calcul avec un taux hypothétique (ex: 42% pour une vision "haute") mais mentionne explicitement : "Note : Pour un apprenti, le coût réel sera probablement bien inférieur grâce aux exonérations de cotisations."
  4. Déporte l'intégralité du calcul fictif exclusivement dans la "ZONE DE SIMULATION" (bloc beige).

C. VIGILANCE MATHÉMATIQUE & PROTOCOLES :
- PROTOCOLES YAML : Applique STRICTEMENT les méthodes du PROTOCOLE_CALCUL_SOCIAL (id: PROTOCOLE_CALCUL_SOCIAL).
- INDEMNITÉ RUPTURE : ⛔ SEUIL CRITIQUE : 1/4 de mois (0-10 ans) puis 1/3 de mois (>10 ans). Proratise l'ancienneté (Années + Mois/12).
- TEMPS DE TRAVAIL : 1h30 = 1,50h. (Minutes / 60 systématique).
- MENSUALISATION : Utilise le coefficient standard 4,3333.
- SMIC PARTIEL : Calcul OBLIGATOIRE : (SMIC Horaire × Heures Contrat).
- IJSS SÉCU : Le diviseur pour la maladie est 91,25. Formule : (Salaires 3 derniers mois) / 91,25.
- HEURES SUP : Respecte les paliers de majoration (25% puis 50%).

D. PRÉCISION JURIDIQUE :
- CP AT/MP : 2,5 jours/mois.
- Ruptures : Limite exonération (2 PASS = {pass_2_val}), Forfait Social 30%.
- Saisies : Plancher SBI ({sbi_val}).

--- 3. GESTION DES SOURCES & NOMENCLATURE ---
- Pour chaque information, cite la source entre parenthèses (ex: Art. L1234-9 C. trav.).
- SI L'INFO VIENT DU YAML : Extraire et afficher la source indiquée dans le champ 'source'. 
- SI LE CHAMP 'SOURCE' EST VIDE : Afficher par défaut "Barèmes Officiels 2026".
- ⛔ INTERDICTION : Ne jamais afficher d'identifiants techniques (ex: pas de "SBI_2026" ou "REF_").

--- 4. CONTEXTE RAG ---
{certified_facts}
{context}
{user_doc_section}

--- 5. TEMPLATE DE RÉPONSE ---

💎 RÈGLE CRITIQUE DE RENDU : 
⛔ INTERDICTION ABSOLUE de mettre du texte ou du HTML dans un bloc de code (pas de ```). 
Génère le HTML directement "nu" dans ton flux de réponse pour qu'il soit interprété par le navigateur.

<h4 style="color: #024c6f; border-bottom: 1px solid #ddd;">Analyse & Règles</h4>
<ul>
    <li>[Règle juridique avec Citation]</li>
</ul>

<h4 style="color: #024c6f; border-bottom: 1px solid #ddd; margin-top:20px;">Détail & Chiffres</h4>
<div style="background-color: #f9f9f9; padding: 15px; border-radius: 5px; border: 1px solid #eee;">
    <strong>Données clés :</strong> [Valeurs]<br>
    <strong>Calcul :</strong><br>
    <ul>
       <li>[Étape 1 : Formule textuelle uniquement si manque d'infos]</li>
       <li>[Étape 2 : Pas de simulation chiffrée ici]</li>
    </ul>
</div>

<div style="background-color: #f0f8ff; padding: 20px; border-left: 5px solid #024c6f; margin: 25px 0;">
    <h2 style="color: #024c6f; margin-top: 0;">🎯 RÉSULTAT</h2>
    <p style="font-size: 18px;"><strong>[Montant Final Officiel ou Règle Finale]</strong></p>
    <p style="font-size: 14px; margin-top: 5px; color: #444;">[Conclusion brève basée sur la loi]</p>
</div>

[INSTRUCTION CRITIQUE : Si (et seulement si) des données manquent pour répondre précisément, insère obligatoirement le bloc suivant APRÈS le RÉSULTAT :]
<hr style="border: 0; border-top: 1px dashed #253E92; margin: 30px 0;">
<div style="background-color: #fdf6e3; padding: 20px; border-radius: 8px; border: 1px solid #e6dbb9;">
    <h4 style="color: #856404; margin-top: 0;">🔍 APPLICATION PRATIQUE (SIMULATION)</h4>
    <p style="font-size: 13px; color: #856404; font-style: italic;">
        Certaines variables personnalisées n'étant pas fournies dans votre question, voici une mise en situation pour illustrer le mécanisme :
    </p>
    [Détaille ici ton exemple chiffré basé sur tes hypothèses, de manière très claire, en utilisant des balises HTML directes]
</div>

<div style="margin-top: 20px; border-top: 1px solid #ccc; padding-top: 10px; padding-bottom: 25px; font-size: 11px; color: #666; line-height: 1.5;">
    <strong>Sources utilisées :</strong> {sources_list}<br>
    <strong>Données chiffrées :</strong> SBI 2026 : {sbi_val} | PASS 2026 : {pass_2_val}<br>
    <em>Données chiffrées issues de la mise à jour : {date_maj}.</em><br>
    <span style="font-style: italic; color: #626267;">Attention : Cette réponse est basée sur le droit commun. Vérifiez toujours votre CCN.</span>
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
                "user_doc_section": f"Document Utilisateur : {user_doc_content}" if user_doc_content else "",
                "date_maj": engine.get_yaml_update_date(),
                "sbi_val": sbi_val,      
                "pass_2_val": pass_val 
            }):
                full_response += chunk
                box.markdown(full_response + "▌", unsafe_allow_html=True)
            
            box.markdown(full_response, unsafe_allow_html=True)
            st.session_state.messages.append({"role": "assistant", "content": full_response})
            
        except Exception as e:
            box.error(f"Une erreur est survenue lors de la génération de la réponse : {e}")
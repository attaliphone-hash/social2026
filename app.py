import streamlit as st
import os
import pypdf
import stripe
import requests
import re
from bs4 import BeautifulSoup
from email.utils import parsedate_to_datetime
from datetime import datetime, timezone
from dotenv import load_dotenv
from supabase import create_client, Client

# --- IMPORTS UI ---
# J'ai retiré 'show_legal_info' car on utilise maintenant les popups
from ui.styles import apply_pro_design, render_top_columns, render_subscription_cards
from rules.engine import SocialRuleEngine
from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAIEmbeddings
from langchain_pinecone import PineconeVectorStore
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

# ✅ Stripe checkout (service)
from services.stripe_service import create_checkout_session

# --- 1. CHARGEMENT CONFIG & SECRETS ---
load_dotenv()
st.set_page_config(page_title="Expert Social Pro France", layout="wide")

# --- APPLICATION DU DESIGN PRO ---
apply_pro_design()

# Connexion Supabase
url = os.getenv("SUPABASE_URL")
key = os.getenv("SUPABASE_KEY")
supabase: Client = create_client(url, key)

# Configuration Stripe (Portal)
stripe.api_key = os.getenv("STRIPE_API_KEY")

# --- FONCTION PORTAIL CLIENT STRIPE ---
def manage_subscription_link(email):
    try:
        customers = stripe.Customer.list(email=email, limit=1)
        if customers and len(customers.data) > 0:
            customer_id = customers.data[0].id
            session = stripe.billing_portal.Session.create(
                customer=customer_id,
                return_url="https://socialexpertfrance.fr" 
            )
            return session.url
    except Exception as e:
        print(f"Erreur Stripe Portal: {e}")
    return None

# --- FONCTION ROBUSTE (Veille BOSS) - VERSION CSS NETTOYÉE ---
def get_boss_status_html():
    try:
        url = "https://boss.gouv.fr/portail/fil-rss-boss-rescrit/pagecontent/flux-actualites.rss"
        headers = {"User-Agent": "Mozilla/5.0"}
        
        response = requests.get(url, headers=headers, timeout=5)
        
        if response.status_code == 200:
            content = response.content.decode('utf-8')
            soup = BeautifulSoup(content, 'html.parser')
            latest_item = soup.find('item')
            
            if latest_item:
                title_tag = latest_item.find('title')
                title = title_tag.text.strip() if title_tag else "Actualité BOSS"
                
                link_match = re.search(r"<link>(.*?)</link>", str(latest_item))
                link = link_match.group(1).strip() if link_match else "https://boss.gouv.fr"
                
                date_tag = latest_item.find('pubdate') or latest_item.find('pubDate')
                
                # Construction du lien avec la classe CSS 'boss-link' (voir styles.py)
                html_link = f'<a href="{link}" target="_blank" class="boss-link">{title}</a>'
                
                if date_tag:
                    try:
                        pub_date_obj = parsedate_to_datetime(date_tag.text.strip())
                        now = datetime.now(timezone.utc)
                        days_old = (now - pub_date_obj).days
                        date_str = pub_date_obj.strftime("%d/%m/%Y")
                        
                        if days_old < 8:
                            # Utilisation de la classe CSS 'boss-red'
                            return f"""<div class="boss-alert-box boss-red">🚨 <strong>NOUVELLE MISE À JOUR BOSS ({date_str})</strong> : {html_link}</div>""", link
                        else:
                            # Utilisation de la classe CSS 'boss-green'
                            return f"""<div class="boss-alert-box boss-green">✅ <strong>Veille BOSS (R.A.S)</strong> : Dernière actu du {date_str} : {html_link}</div>""", link
                            
                    except:
                        pass 
                
                # Fallback générique
                return f"""<div class="boss-alert-box boss-red">📢 ALERTE BOSS : {html_link}</div>""", link
            
            return "<div class='boss-alert-box' style='background-color:#f0f2f6;'>✅ Veille BOSS : Aucune actualité détectée.</div>", ""
            
        return "", ""
    except Exception:
        return "", ""

def show_boss_alert():
    if "news_closed" not in st.session_state:
        st.session_state.news_closed = False

    if st.session_state.news_closed:
        return

    html_content, link = get_boss_status_html()
    
    if html_content:
        col_text, col_close = st.columns([0.95, 0.05])
        with col_text:
            st.markdown(html_content, unsafe_allow_html=True)
        with col_close:
            if st.button("✖️", key="btn_close_news", help="Masquer"):
                st.session_state.news_closed = True
                st.rerun()

# --- 2. AUTHENTIFICATION ---
def check_password():
    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False

    if st.session_state.authenticated:
        return True

    # Utilisation de H2 pour le login
    st.markdown("<h2>EXPERT SOCIAL PRO - ACCÈS</h2>", unsafe_allow_html=True)
    
    render_top_columns()
    st.markdown("---")

    tab1, tab2 = st.tabs(["🔐 Espace Client Abonnés", "Accès Découverte / Admin"])

    with tab1:
        st.caption("Connectez-vous pour accéder à votre espace abonné.")
        email = st.text_input("Email client", key="email_client")
        pwd = st.text_input("Mot de passe", type="password", key="pwd_client")
        
        if st.button("Se connecter au compte", use_container_width=True):
            try:
                supabase.auth.sign_in_with_password({"email": email, "password": pwd})
                st.session_state.authenticated = True
                st.session_state.user_email = email
                st.rerun()
            except Exception:
                st.error("Identifiants incorrects ou compte non activé.")
        
        st.markdown("---")
        st.write("✨ **Pas encore abonné ?** Choisissez votre formule :")
        
        # Affiche les cartes
        render_subscription_cards()
        
        if st.session_state.get("btn_sub_month"):
            url_checkout = create_checkout_session("Mensuel")
            if url_checkout:
                st.markdown(f'<meta http-equiv="refresh" content="0;URL={url_checkout}">', unsafe_allow_html=True)
            else:
                st.error("Impossible d'ouvrir le paiement mensuel (Stripe).")

        if st.session_state.get("btn_sub_year"):
            url_checkout = create_checkout_session("Annuel")
            if url_checkout:
                st.markdown(f'<meta http-equiv="refresh" content="0;URL={url_checkout}">', unsafe_allow_html=True)
            else:
                st.error("Impossible d'ouvrir le paiement annuel (Stripe).")

    with tab2:
        st.caption("Code d'accès personnel")
        access_code = st.text_input("Code d'accès", type="password", key="pwd_codes")
        if st.button("Valider le code", use_container_width=True):
            if access_code == os.getenv("ADMIN_PASSWORD"):
                st.session_state.authenticated = True
                st.session_state.user_email = "ADMINISTRATEUR"
                st.rerun()
            elif access_code == os.getenv("APP_PASSWORD"):
                st.session_state.authenticated = True
                st.session_state.user_email = "Utilisateur Promo"
                st.rerun()
            else:
                st.error("Code incorrect.")

    return False

if not check_password():
    st.stop()

# --- 3. CHARGEMENT MOTEUR & SYSTÈME IA ---
@st.cache_resource
def load_engine():
    return SocialRuleEngine()

@st.cache_resource
def load_ia_system():
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        raise ValueError("La clé GOOGLE_API_KEY est introuvable dans le fichier .env")
        
    embeddings = GoogleGenerativeAIEmbeddings(model="models/text-embedding-004", google_api_key=api_key)
    
    try:
        vectorstore = PineconeVectorStore.from_existing_index(index_name="expert-social", embedding=embeddings)
    except Exception as e:
        raise ConnectionError(f"Impossible de se connecter à Pinecone ('expert-social') : {e}")
        
    llm = ChatGoogleGenerativeAI(model="gemini-2.0-flash", temperature=0, google_api_key=api_key)
    return vectorstore, llm

# --- BLOC DE CHARGEMENT SÉCURISÉ ---
try:
    with st.spinner("Chargement du cerveau de l'IA..."):
        engine = load_engine()
        vectorstore, llm = load_ia_system()
except Exception as e:
    st.error(f"🔴 ERREUR CRITIQUE DE CHARGEMENT : {e}")
    st.info("Vérifiez vos clés API dans le fichier .env et votre connexion internet.")
    st.stop()

def clean_query_for_engine(q):
    stop_words = ["quel", "est", "le", "montant", "du", "de", "la", "les", "actuel", "en", "2026", "pour", "?", "l'"]
    words = q.lower().split()
    cleaned = [w for w in words if w not in stop_words]
    return " ".join(cleaned)

# --- CONTEXTE PINECONE ---
def build_context(query):
    raw_docs = vectorstore.similarity_search(query, k=25)
    context_text = ""
    sources_seen = []
    
    for d in raw_docs:
        raw_src = d.metadata.get('source', 'Source Inconnue')
        clean_name = os.path.basename(raw_src).replace('.pdf', '').replace('.txt', '').replace('.csv', '')
        
        if "REF" in clean_name: 
            pretty_src = "Barème Officiel"
        elif "LEGAL" in clean_name: 
            pretty_src = "Code du Travail"
        elif "BOSS" in clean_name: 
            pretty_src = "BOSS"
        else: 
            pretty_src = clean_name
        
        sources_seen.append(pretty_src)
        context_text += f"[DOCUMENT : {pretty_src}]\n{d.page_content}\n\n"
        
    uniq_sources = []
    for s in sources_seen:
        if s and s not in uniq_sources:
            uniq_sources.append(s)
            
    return context_text, uniq_sources

def get_gemini_response_stream(query, context, sources_list, certified_facts="", user_doc_content=None):
    user_doc_section = f"\n--- DOCUMENT UTILISATEUR ---\n{user_doc_content}\n" if user_doc_content else ""
    facts_section = f"\n--- FAITS CERTIFIÉS 2026 (à utiliser en priorité si pertinent) ---\n{certified_facts}\n" if certified_facts else ""
    
# ==================================================================================
    # PROMPT EXPERT SOCIAL 2026 - GOLDEN
    # ==================================================================================
    prompt = ChatPromptTemplate.from_template("""
Tu es l'Expert Social Pro 2026. Tu dois fournir une réponse d'une fiabilité absolue avec une présentation claire et aérée.

════════════════════════════════════════════
RÈGLE D'OR : HIÉRARCHIE DES SOURCES
════════════════════════════════════════════
Si plusieurs documents semblent contradictoires, tu dois respecter cet ordre de priorité ABSOLU :
1. **LES DOCUMENTS INTITULÉS "BARÈME OFFICIEL" ou "DONNÉES URSSAF"** : Ils contiennent les CHIFFRES, TAUX et PLAFONDS À JOUR (2026). Ils ont TOUJOURS raison sur les textes théoriques.
2. **LES DOCUMENTS "BOSS"** : Ils expliquent le fonctionnement théorique. Si le "Barème Officiel" donne un chiffre précis, ignore les mentions "en attente de décret" du BOSS.

MÉTHODOLOGIE INTERNE (NE PAS AFFICHER) :
1. ANALYSE : Cherche en priorité les valeurs dans les documents identifiés comme "Barème Officiel".
2. CALCUL MENTAL : Fais le calcul complet avec précision.
3. ARRONDIS INTELLIGENTS : 
   - Montants en EUROS (€) et DURÉES (Mois, Années) : Arrondis à 2 décimales (ex: 1250,50 € ou 3,39 mois).
   - Coefficients techniques de paie (ex: Fillon, Taux AT) : Garde 4 décimales (ex: 0,3981).
4. RÉDACTION : Utilise le format HTML ci-dessous. FORCE les listes avec <ul> et <li>.

════════════════════════════════════════════
INTERDICTIONS DE LANGAGE (STYLE PRO)
════════════════════════════════════════════
- Ne JAMAIS dire "J'ai consulté le fichier REF_...". Dis "Selon le Barème Officiel".
- Ne détaille pas tes étapes de recherche interne. Donne directement l'information qualifiée.

════════════════════════════════════════════
STRUCTURE DE LA RÉPONSE (À RESPECTER SCRUPULEUSEMENT)
════════════════════════════════════════════

<h4 style="color: #024c6f; margin-bottom: 5px; text-transform: uppercase; border-bottom: 1px solid #ddd; padding-bottom: 5px; font-family: sans-serif;">Analyse & Règles Applicables</h4>
<ul>
<li>Explique la règle clairement...</li>
<li>Cite le point de vigilance...</li>
</ul>

<h4 style="color: #024c6f; margin-bottom: 5px; margin-top: 20px; text-transform: uppercase; border-bottom: 1px solid #ddd; padding-bottom: 5px; font-family: sans-serif;">Détail du Calcul</h4>
<div style="margin-top: 10px; margin-bottom: 10px;">
<p>Voici le détail étape par étape :</p>
<ul>
<li><strong>Étape 1 :</strong> Détail du calcul...</li>
<li><strong>Étape 2 :</strong> Détail du calcul...</li>
<li><strong>Total :</strong> Résultat intermédiaire...</li>
</ul>
</div>

<div style="background-color: #f0f8ff; padding: 20px; border-radius: 8px; border-left: 5px solid #024c6f; margin-top: 25px; margin-bottom: 25px; box-shadow: 0 2px 4px rgba(0,0,0,0.05);">
    <h3 style="color: #024c6f; margin-top: 0; font-family: sans-serif; font-size: 18px;">🎯 CONCLUSION</h3>
    <p style="font-size: 18px; color: #111; margin-bottom: 5px; font-weight: 600;">
        Le montant / taux estimé est de : [INSÉRER RÉSULTAT FINAL]
    </p>
    <p style="font-size: 13px; color: #555; margin-top: 0;">
        <em>Basé sur les éléments fournis et les barèmes officiels.</em>
    </p>
</div>

<h4 style="color: #024c6f; margin-bottom: 5px; text-transform: uppercase; border-bottom: 1px solid #ddd; padding-bottom: 5px; font-family: sans-serif;">Références Juridiques</h4>
<p style="font-size: 12px; color: #666; font-style: italic; margin-bottom: 10px;">
     <strong>Note :</strong> Base de calcul : Code du travail et données URSSAF uniquement. Sous réserve des dispositions conventionnelles (CCN) ou contractuelles spécifiques à l'entreprise.
</p>
<ul>
<li>Source officielle...</li>
</ul>

---
DONNÉES CERTIFIÉES 2026 (YAML) :
{facts_section}

DOCUMENTS RETROUVÉS :
{context}
""" + user_doc_section + """
QUESTION :
{question}

SOURCES :
{sources_list}
""")

    # 👇 EXÉCUTION (Ne pas oublier !)
    chain = prompt | llm | StrOutputParser()
    return chain.stream({
        "context": context,
        "question": query,
        "sources_list": ", ".join(sources_list) if sources_list else "Aucune",
        "facts_section": facts_section
    })

# --- DÉFINITION DES POPUPS (MODALES) ---
@st.dialog("Mentions Légales")
def modal_mentions():
    st.markdown("""
    <div style='font-size: 13px; color: #333; line-height: 1.6;'>
        <strong>ÉDITEUR :</strong><br>
        Le site <em>socialexpertfrance.fr</em> est édité par la BUSINESS AGENT AI.<br>
        Contact : sylvain.attal@businessagent-ai.com<br><br>
        <strong>PROPRIÉTÉ INTELLECTUELLE :</strong><br>
        L'ensemble de ce site relève de la législation française et internationale sur le droit d'auteur.
        L'architecture, le code et le design sont la propriété exclusive de BUSINESS AGENT AI®. 
        La réutilisation des réponses générées est autorisée dans le cadre de vos missions professionnelles.<br><br>
        <strong>RESPONSABILITÉ :</strong><br>
        Les réponses sont fournies à titre indicatif et ne remplacent pas une consultation juridique. 
        L'utilisateur doit vérifier les réponses de l'IA qui n'engagent pas l'éditeur.
    </div>
    """, unsafe_allow_html=True)

@st.dialog("Politique de Confidentialité (RGPD)")
def modal_rgpd():
    st.markdown("""
    <div style='font-size: 13px; color: #333; line-height: 1.6;'>
        <strong>PROTECTION DES DONNÉES & COOKIES :</strong><br>
        1. <strong>Gestion des Cookies :</strong> Un unique cookie technique est déposé pour maintenir votre session active.<br>
        2. <strong>Absence de Traçage :</strong> Aucun cookie publicitaire ou traceur tiers n'est utilisé.<br>
        3. <strong>Données Volatiles :</strong> Le traitement est effectué en mémoire vive (RAM) et vos données ne servent jamais à entraîner les modèles d'IA.<br><br>
        <em>Conformité RGPD : Droit à l'oubli garanti par défaut.</em>
    </div>
    """, unsafe_allow_html=True)

# --- 4. INTERFACE DE CHAT ET SIDEBAR ---
user_email = st.session_state.get("user_email", "")
if user_email and user_email != "ADMINISTRATEUR" and user_email != "Utilisateur Promo":
    with st.sidebar:
        st.markdown("### 👤 Mon Compte")
        st.write(f"Connecté : {user_email}")
        
        if st.button("💳 Gérer mon abonnement", help="Factures, changement de carte, désabonnement"):
            portal_url = manage_subscription_link(user_email)
            if portal_url:
                st.link_button("👉 Accéder au portail Stripe", portal_url)
            else:
                st.info("Aucun abonnement actif trouvé.")
        
        # J'ai nettoyé les boutons juridiques d'ici pour les mettre en bas de page

st.markdown("<hr>", unsafe_allow_html=True)

if user_email == "ADMINISTRATEUR":
    show_boss_alert()

render_top_columns()
st.markdown("<br>", unsafe_allow_html=True)

if "uploader_key" not in st.session_state:
    st.session_state.uploader_key = 0

# --- TITRE PRINCIPAL (Pleine largeur) ---
st.markdown("<h1>EXPERT SOCIAL PRO ABONNÉS</h1>", unsafe_allow_html=True)

# --- ZONE DES BOUTONS (Juste en dessous) ---
# On crée 2 colonnes pour mettre l'Upload et le Reset côte à côte
c_up, c_new, _ = st.columns([2, 1, 3], vertical_alignment="bottom")

with c_up:
    uploaded_file = st.file_uploader(
        "Upload", 
        type=["pdf", "txt"], 
        label_visibility="collapsed",
        key=f"uploader_{st.session_state.uploader_key}"
    )

with c_new:
    if st.button("Nouvelle session"):
        st.session_state.messages = []
        st.session_state.uploader_key += 1
        st.rerun()

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

if "messages" not in st.session_state: 
    st.session_state.messages = []

for msg in st.session_state.messages:
    with st.chat_message(msg["role"], avatar=("avatar-logo.png" if msg["role"]=="assistant" else None)):
        st.markdown(msg["content"], unsafe_allow_html=True)

if query := st.chat_input("Votre question juridique ou chiffrée..."):
    st.session_state.messages.append({"role": "user", "content": query})
    with st.chat_message("user"):
        st.markdown(query)
    
    with st.chat_message("assistant", avatar="avatar-logo.png"):
        message_placeholder = st.empty()
        
        cleaned_q = clean_query_for_engine(query)
        matched = engine.match_rules(cleaned_q if cleaned_q else query, top_k=5, min_score=2)
        certified_facts = engine.format_certified_facts(matched)
        
        with st.spinner("Analyse en cours..."):
            context_text, sources_list = build_context(query)
            
            full_response = ""
            for chunk in get_gemini_response_stream(
                query=query, 
                context=context_text, 
                sources_list=sources_list,
                certified_facts=certified_facts,
                user_doc_content=user_doc_text
            ):
                full_response += chunk
                message_placeholder.markdown(full_response + "▌", unsafe_allow_html=True)
            
            if uploaded_file and "Document analysé" not in full_response:
                full_response += f"\n* 📄 Document analysé : {uploaded_file.name}"
            
            # ✅ LE PADDING EST BIEN ICI, HORS DU 'IF' ET ON A LA BOÎTE BLEUE
            full_response += "<br><br>"
            
            message_placeholder.markdown(full_response, unsafe_allow_html=True)
                
    st.session_state.messages.append({"role": "assistant", "content": full_response})

# --- ZONE JURIDIQUE (BOUTONS DISCRETS EN BAS) ---
st.markdown("<br><br>", unsafe_allow_html=True) # Un peu d'espace
col_leg1, col_leg2, _ = st.columns([1, 1, 2]) # Colonnes pour aligner à gauche

with col_leg1:
    if st.button("⚖️ Mentions Légales", key="footer_mentions", use_container_width=True):
        modal_mentions()

with col_leg2:
    if st.button("🔒 RGPD & Cookies", key="footer_rgpd", use_container_width=True):
        modal_rgpd()

# Footer avec classe CSS propre (géré dans styles.py)
st.markdown("<div class='footer-copyright'>© 2026 socialexpertfrance.fr</div>", unsafe_allow_html=True)
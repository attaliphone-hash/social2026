# ============================================================
# FICHIER : app.py (BASE BACKUP + UNIQUEMENT VEILLE MODIFIÉE)
# ============================================================
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
from services.stripe_service import verify_active_subscription  
# --- IMPORTS UI ---
from ui.styles import apply_pro_design, render_top_columns, render_subscription_cards
from rules.engine import SocialRuleEngine
from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAIEmbeddings
from langchain_pinecone import PineconeVectorStore
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

# ✅ Stripe checkout + Verification
from services.stripe_service import create_checkout_session, verify_active_subscription

# --- 1. CHARGEMENT CONFIG & SECRETS ---
load_dotenv()
st.set_page_config(page_title="Expert Social Pro France", layout="wide")

# --- APPLICATION DU DESIGN PRO ---
apply_pro_design()

# Connexion Supabase
url = os.getenv("SUPABASE_URL")
key = os.getenv("SUPABASE_KEY")
supabase: Client = create_client(url, key)

# Configuration Stripe
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

# ==============================================================================
# DEBUT : NOUVEAU MODULE VEILLE (3 SOURCES + FIX SCRAPING)
# ==============================================================================

# Dictionnaire pour traduire les dates "16 janvier 2026"
FRENCH_MONTHS = {
    "janvier": 1, "février": 2, "mars": 3, "avril": 4, "mai": 5, "juin": 6,
    "juillet": 7, "août": 8, "septembre": 9, "octobre": 10, "novembre": 11, "décembre": 12
}

def get_headers():
    return {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8"
    }

# --- SOURCE 1 : BOSS ---
def get_boss_status_html():
    target_url = "https://boss.gouv.fr/portail/accueil/actualites.html"
    try:
        url = "https://boss.gouv.fr/portail/fil-rss-boss-rescrit/pagecontent/flux-actualites.rss"
        response = requests.get(url, headers=get_headers(), timeout=6)
        
        if response.status_code == 200:
            content = response.content.decode('utf-8', errors='ignore')
            soup = BeautifulSoup(content, 'html.parser')
            item = soup.find('item')
            if item:
                title = item.find('title').text.strip()
                date_tag = item.find('pubdate') or item.find('pubDate')
                if date_tag:
                    dt = parsedate_to_datetime(date_tag.text.strip())
                    if dt.tzinfo is None: dt = dt.replace(tzinfo=timezone.utc)
                    days = (datetime.now(timezone.utc) - dt).days
                    date_str = dt.strftime("%d/%m")
                    if days < 8:
                        return f"<div style='background-color:#f8d7da; color:#721c24; padding:10px; border-radius:6px; border:1px solid #f5c6cb; margin-bottom:8px; font-size:13px;'>🚨 <strong>NOUVEAU BOSS ({date_str})</strong> : <a href='{target_url}' target='_blank' style='text-decoration:underline; font-weight:bold; color:inherit;'>{title}</a></div>"
                    else:
                        return f"<div style='background-color:#d4edda; color:#155724; padding:10px; border-radius:6px; border:1px solid #c3e6cb; margin-bottom:8px; font-size:13px; opacity:0.9;'>✅ <strong>Veille BOSS (R.A.S)</strong> : Dernière actu du {date_str} <a href='{target_url}' target='_blank' style='margin-left:5px; text-decoration:underline; color:inherit; font-size:11px;'>[Voir]</a></div>"
    except: pass
    return f"<div style='background-color:#f8f9fa; color:#555; padding:10px; border-radius:6px; border:1px solid #ddd; margin-bottom:8px; font-size:13px;'>ℹ️ <strong>Veille BOSS</strong> : Flux indisponible <a href='{target_url}' target='_blank' style='text-decoration:underline; color:inherit; font-weight:bold;'>[Accès direct]</a></div>"

# --- SOURCE 2 : SERVICE-PUBLIC (FIX SCRAPING HTML) ---
def get_service_public_status():
    target_url = "https://entreprendre.service-public.gouv.fr/actualites"
    try:
        response = requests.get(target_url, headers=get_headers(), timeout=8)
        if response.status_code == 200:
            soup = BeautifulSoup(response.content, 'html.parser')
            # On cherche la première "carte" (fr-card)
            card = soup.find('div', class_='fr-card')
            if card:
                title_tag = card.find(class_='fr-card__title')
                title = title_tag.text.strip() if title_tag else "Actualité"
                desc_tag = card.find(class_='fr-card__desc')
                pub_date = None
                if desc_tag:
                    text_date = desc_tag.text.lower().replace("publié le", "").strip()
                    parts = text_date.split() 
                    if len(parts) >= 3:
                        try:
                            day = int(parts[0])
                            month_str = parts[1]
                            year = int(parts[2])
                            if month_str in FRENCH_MONTHS:
                                month = FRENCH_MONTHS[month_str]
                                pub_date = datetime(year, month, day, tzinfo=timezone.utc)
                        except: pass
                if pub_date:
                    days = (datetime.now(timezone.utc) - pub_date).days
                    date_str = pub_date.strftime("%d/%m")
                    if days < 8:
                        return f"<div style='background-color:#f8d7da; color:#721c24; padding:10px; border-radius:6px; border:1px solid #f5c6cb; margin-bottom:8px; font-size:13px;'>🚨 <strong>NOUVEAU SERVICE-PUBLIC ({date_str})</strong> : <a href='{target_url}' target='_blank' style='text-decoration:underline; font-weight:bold; color:inherit;'>{title}</a></div>"
                    else:
                        return f"<div style='background-color:#d1ecf1; color:#0c5460; padding:10px; border-radius:6px; border:1px solid #bee5eb; margin-bottom:8px; font-size:13px; opacity:0.9;'>✅ <strong>Veille Service-Public (R.A.S)</strong> : Dernière actu du {date_str} <a href='{target_url}' target='_blank' style='margin-left:5px; text-decoration:underline; color:inherit; font-size:11px;'>[Voir]</a></div>"
    except: pass
    return f"<div style='background-color:#f8f9fa; color:#555; padding:10px; border-radius:6px; border:1px solid #ddd; margin-bottom:8px; font-size:13px;'>ℹ️ <strong>Veille Service-Public</strong> : Flux indisponible <a href='{target_url}' target='_blank' style='text-decoration:underline; color:inherit; font-weight:bold;'>[Accès direct]</a></div>"

# --- SOURCE 3 : NET-ENTREPRISES ---
def get_net_entreprises_status():
    target_url = "https://www.net-entreprises.fr/actualites/"
    try:
        url = "https://www.net-entreprises.fr/feed/"
        response = requests.get(url, headers=get_headers(), timeout=6)
        if response.status_code == 200:
            soup = BeautifulSoup(response.content, 'html.parser')
            item = soup.find('item')
            if item:
                title = item.find('title').text.strip()
                date_tag = item.find('pubdate') or item.find('pubDate')
                if date_tag:
                    dt = parsedate_to_datetime(date_tag.text.strip())
                    if dt.tzinfo is None: dt = dt.replace(tzinfo=timezone.utc)
                    days = (datetime.now(timezone.utc) - dt).days
                    date_str = dt.strftime("%d/%m")
                    if days < 8:
                        return f"<div style='background-color:#f8d7da; color:#721c24; padding:10px; border-radius:6px; border:1px solid #f5c6cb; margin-bottom:8px; font-size:13px;'>🚨 <strong>NOUVEAU NET-ENTREPRISES ({date_str})</strong> : <a href='{target_url}' target='_blank' style='text-decoration:underline; font-weight:bold; color:inherit;'>{title}</a></div>"
                    else:
                        return f"<div style='background-color:#fff3cd; color:#856404; padding:10px; border-radius:6px; border:1px solid #ffeeba; margin-bottom:8px; font-size:13px; opacity:0.9;'>✅ <strong>Veille Net-Entreprises (R.A.S)</strong> : Dernière actu du {date_str} <a href='{target_url}' target='_blank' style='margin-left:5px; text-decoration:underline; color:inherit; font-size:11px;'>[Voir]</a></div>"
    except: pass
    return f"<div style='background-color:#f8f9fa; color:#555; padding:10px; border-radius:6px; border:1px solid #ddd; margin-bottom:8px; font-size:13px;'>ℹ️ <strong>Veille Net-Entreprises</strong> : Flux indisponible <a href='{target_url}' target='_blank' style='text-decoration:underline; color:inherit; font-weight:bold;'>[Accès direct]</a></div>"

# --- FONCTION PRINCIPALE ---
def show_legal_watch_bar():
    if "news_closed" not in st.session_state: st.session_state.news_closed = False
    if st.session_state.news_closed: return

    c1, c2 = st.columns([0.95, 0.05])
    with c1:
        st.markdown(get_boss_status_html(), unsafe_allow_html=True)
        st.markdown(get_service_public_status(), unsafe_allow_html=True)
        st.markdown(get_net_entreprises_status(), unsafe_allow_html=True)
    with c2: 
        if st.button("✖️", key="btn_close_news", help="Masquer"): 
            st.session_state.news_closed = True
            st.rerun()

# ==============================================================================
# FIN NOUVEAU MODULE VEILLE
# ==============================================================================

# --- POPUPS ---
@st.dialog("Mentions Légales")
def modal_mentions():
    # On utilise st.html pour le contenu technique ou st.markdown avec des balises simples
    st.markdown(f"""
    <div style='font-size: 12px; color: #1e293b; font-family: sans-serif;'>
        <p>ÉDITEUR DU SITE<br>
        Le site <em>socialexpertfrance.fr</em> est édité par <strong>Sylvain Attal EI (BUSINESS AGENT AI)</strong>.<br>
        SIREN : 948253711 | Directeur : Sylvain ATTAL<br>
        Contact : sylvain.attal@businessagent-ai.com</p>
        HÉBERGEMENT
        Google Cloud EMEA Limited<br>
        70 Sir John Rogerson’s Quay, Dublin 2, Irlande</p>
        LIMITATION DE RESPONSABILITÉ (IA)<br>
        Les réponses sont générées par une Intelligence Artificielle (Gemini 2.0 Flash Exp). 
        Ces informations sont indicatives et <strong>ne remplacent pas une consultation juridique</strong> 
        auprès d'un professionnel du droit. L'éditeur ne saurait être tenu responsable des erreurs.</p>
        PROPRIÉTÉ<br>
        Code source et design : Propriété exclusive de BUSINESS AGENT AI®.</p>
    </div>
    """, unsafe_allow_html=True)

@st.dialog("Politique de Confidentialité")
def modal_rgpd():
    st.markdown(f"""
    <div style='font-size: 13px; color: #1e293b; font-family: sans-serif;'>
        <p><strong>PROTECTION DES DONNÉES :</strong></p>
        <ul>
            <li><strong>Cookies :</strong> Uniquement technique pour maintenir votre session.</li>
            <li><strong>Traçage :</strong> Aucun cookie publicitaire ou analytique tiers n'est déposé.</li>
            <li><strong>Données :</strong> Vos saisies sont traitées en mémoire vive et ne sont pas stockées ni utilisées pour l'entraînement de l'IA.</li>
        </ul>
    </div>
    """, unsafe_allow_html=True)
# --- 2. AUTHENTIFICATION ---
def check_password():
    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False

    if st.session_state.authenticated:
        return True

    # 1. ARGUMENTS EN HAUT
    render_top_columns()
    
    # 2. LIGNE COPYRIGHT AVEC STYLE HARMONISE
    st.markdown("""
        <style>
        .footer-text {
            font-family: 'Open Sans', sans-serif !important;
            font-size: 11px !important; 
            color: #7A7A7A !important;
        }
        div[data-testid="column"] button[kind="tertiary"] p {
            font-size: 11px !important;
            font-family: 'Open Sans', sans-serif !important;
            color: #7A7A7A !important;
        }
        div[data-testid="column"] button[kind="tertiary"] {
            padding: 0px !important;
            min-height: unset !important;
            line-height: 1 !important;
        }
        </style>
    """, unsafe_allow_html=True)
    
    st.markdown("<div style='margin-bottom: 10px;'></div>", unsafe_allow_html=True)
    c_line = st.columns([1.2, 0.8, 0.8, 3], vertical_alignment="center")
    with c_line[0]: st.markdown("<span class='footer-text'>© 2026 socialexpertfrance.fr</span>", unsafe_allow_html=True)
    with c_line[1]: 
        if st.button("Mentions Légales", key="top_m", type="tertiary"): modal_mentions()
    with c_line[2]: 
        if st.button("Confidentialité", key="top_r", type="tertiary"): modal_rgpd()

    st.markdown("<hr style='margin-top:5px; margin-bottom:15px'>", unsafe_allow_html=True)
    st.markdown("<h1>EXPERT SOCIAL PRO - ACCÈS</h1>", unsafe_allow_html=True)
    
    t1, t2 = st.tabs(["🔐 Abonnés", "Découverte"])
    with t1:
        email = st.text_input("Email", key="e")
        pwd = st.text_input("Mot de passe", type="password", key="p")
        if st.button("Connexion", use_container_width=True):
            try:
                supabase.auth.sign_in_with_password({"email": email, "password": pwd})
                st.session_state.authenticated = True
                st.session_state.user_email = email
                st.rerun()
            except: st.error("Erreur d'identification.")
        st.markdown("---")
        render_subscription_cards()
        if st.session_state.get("btn_sub_month"):
            u = create_checkout_session("Mensuel")
            if u: st.markdown(f'<meta http-equiv="refresh" content="0;URL={u}">', unsafe_allow_html=True)
        if st.session_state.get("btn_sub_year"):
            u = create_checkout_session("Annuel")
            if u: st.markdown(f'<meta http-equiv="refresh" content="0;URL={u}">', unsafe_allow_html=True)

    with t2:
        code = st.text_input("Code", type="password")
        if st.button("Valider", use_container_width=True):
            if code == os.getenv("ADMIN_PASSWORD"):
                st.session_state.authenticated = True; st.session_state.user_email = "ADMINISTRATEUR"; st.rerun()
            elif code == os.getenv("APP_PASSWORD"):
                st.session_state.authenticated = True; st.session_state.user_email = "Utilisateur Promo"; st.rerun()
            else: st.error("Code faux")
    return False

if not check_password(): st.stop()

# ============================================================
# 🔴 SÉCURITÉ STRIPE : VÉRIFICATION D'ABONNEMENT
# ============================================================
user_email = st.session_state.get("user_email")
ADMIN_EMAILS = ["ton.email@admin.com"] # AJOUTE TON EMAIL ICI

# On ne vérifie que si c'est un email classique (pas un code admin/promo)
if user_email and user_email not in ["ADMINISTRATEUR", "Utilisateur Promo"]:
    # Passe-droit pour ton email perso
    if user_email in ADMIN_EMAILS:
        is_subscribed = True
    else:
        with st.spinner("Vérification de votre abonnement..."):
            is_subscribed = verify_active_subscription(user_email)

    if not is_subscribed:
        st.error("⛔ Accès refusé : Aucun abonnement actif trouvé.")
        st.markdown("""
        <div style="background-color: #ffebee; padding: 20px; border-radius: 10px; border-left: 5px solid #f44336;">
            <h4>Votre abonnement est inactif ou expiré.</h4>
            <p>Pour accéder à l'Expert Social 2026, vous devez disposer d'un abonnement valide.</p>
        </div>
        """, unsafe_allow_html=True)
        
        col1, col2 = st.columns(2)
        with col1:
            # On propose l'abonnement mensuel par défaut
            checkout_url = create_checkout_session("Mensuel", user_email)
            if checkout_url:
                st.link_button("S'abonner (Mensuel)", checkout_url, type="primary")
        
        st.stop()
# ============================================================
# FIN SÉCURITÉ STRIPE
# ============================================================

# --- 3. CHARGEMENT MOTEUR & IA ---
@st.cache_resource
def load_engine():
    return SocialRuleEngine()

@st.cache_resource
def load_ia_system():
    api_key = os.getenv("GOOGLE_API_KEY")
    embeddings = GoogleGenerativeAIEmbeddings(model="models/text-embedding-004", google_api_key=api_key)
    try:
        vectorstore = PineconeVectorStore.from_existing_index(index_name="expert-social", embedding=embeddings)
    except Exception:
        raise ConnectionError("Erreur Pinecone")
    llm = ChatGoogleGenerativeAI(model="gemini-2.0-flash", temperature=0, google_api_key=api_key)
    return vectorstore, llm

try:
    with st.spinner("Chargement du cerveau de l'IA..."):
        engine = load_engine()
        vectorstore, llm = load_ia_system()
except Exception as e:
    st.error(f"Erreur IA : {e}")
    st.stop()

def clean_query_for_engine(q):
    stop_words = ["quel", "est", "le", "montant", "du", "de", "la", "les", "actuel", "en", "2026", "pour", "?", "l'"]
    words = q.lower().split()
    cleaned = [w for w in words if w not in stop_words]
    return " ".join(cleaned)

def build_context(query):
    raw_docs = vectorstore.similarity_search(query, k=25)
    context_text, sources_seen = "", []
    for d in raw_docs:
        raw_src = d.metadata.get('source', 'Inconnu')
        clean_name = os.path.basename(raw_src).replace('.pdf', '').replace('.txt', '').replace('.csv', '')
        if "REF" in clean_name: pretty_src = "Barème Officiel"
        elif "LEGAL" in clean_name: pretty_src = "Code du Travail"
        elif "BOSS" in clean_name: pretty_src = "BOSS"
        else: pretty_src = clean_name
        sources_seen.append(pretty_src)
        context_text += f"[DOCUMENT : {pretty_src}]\n{d.page_content}\n\n"
    return context_text, list(set(sources_seen))

def get_gemini_response_stream(query, context, sources_list, certified_facts="", user_doc_content=None):
    user_doc_section = f"\n--- DOCUMENT UTILISATEUR ---\n{user_doc_content}\n" if user_doc_content else ""
    facts_section = f"\n--- FAITS CERTIFIÉS 2026 ---\n{certified_facts}\n" if certified_facts else ""
    
# === PROMPT EXPERT SOCIAL PRO 2026 - FINAL RENDER (0€ + HTML PROPRE) ===
    prompt = ChatPromptTemplate.from_template("""
Tu es l'Expert Social Pro 2026.

RÈGLE DE FORME ABSOLUE (CRITIQUE) :
1. Tu dois générer du **HTML BRUT** destiné à être injecté directement dans une page web.
2. ⚠️ Ne mets JAMAIS de balises de code (pas de ```html, pas de ```).
3. Ne laisse jamais apparaître les balises <ul>, <li> ou <br> sous forme de texte visible dans le rendu final. Elles doivent servir au formatage.
4. Commence directement par la balise <h4>.

--- 1. LOGIQUE MÉTIER & CALCUL ---
- PRIORITÉ 1 : SCANNE LE YAML.
- MAPPING SMIC/FILLON : Utilise 'T_moins_50' (0.3981) ou 'T_plus_50' (0.4021) uniquement pour la Réduction Générale.

- RÈGLE "COÛT ZÉRO" (SMIC) :
  Si on demande le coût ou les charges pour un SMIC :
  1. Calcule l'exonération (ex: ~725€).
  2. Considère que : [Charges Dues] = [Exonération Calculée].
  3. Applique la formule : [Charges Dues] - [Exonération] = 0 €.
  4. Affiche "0,00 €" en résultat final.
  
  ⚠️ GESTION DES SOURCES (CRITIQUE) :
  Ne cite JAMAIS "Protocole", "Instruction" ou "Règle interne" comme source.
  Pour justifier le coût nul au SMIC, la source officielle est : **"BOSS / Urssaf"** (Dispositif Zéro Charges).

--- 2. CONTEXTE RAG ---
{certified_facts}
{context}
{user_doc_section}

--- 3. TEMPLATE DE RÉPONSE (A REMPLIR) ---

<h4 style="color: #024c6f; border-bottom: 1px solid #ddd;">Analyse & Règles</h4>
<ul>
    <li>[Insérer ici les règles juridiques et sources]</li>
</ul>

[CONSIGNE SOURCES] : Affiche "Code du travail", "BOSS", "Urssaf". Pas de noms de fichiers.

<h4 style="color: #024c6f; border-bottom: 1px solid #ddd; margin-top:20px;">
    [TITRE : "Calcul de l'Exonération" (si Fillon) OU "Calcul & Application" (si Autre)]
</h4>

<div style="background-color: #f9f9f9; padding: 15px; border-radius: 5px; border: 1px solid #eee;">
    <strong>Données utilisées :</strong> [Lister les données chiffrées]<br>
    <strong>Détail :</strong><br>
    
    [INSTRUCTION DE RENDU DU CALCUL] :
    - SI SMIC/FILLON : Génère une liste à puces HTML (<ul><li>) comparant les deux hypothèses (<50 et ≥50) avec les montants de réduction.
    - SI AUTRE CAS : Génère le détail du calcul étape par étape.
    
    [ATTENTION : Génère directement le code HTML des puces ici. Ne l'affiche pas en texte.]
</div>

<div style="background-color: #f0f8ff; padding: 20px; border-left: 5px solid #024c6f; margin: 25px 0;">
    <h2 style="color: #024c6f; margin-top: 0;">🎯 CONCLUSION</h2>
    <p style="font-size: 18px;"><strong>Résultat : [RÉSULTAT FINAL CALCULÉ]</strong></p>
    <p style="font-size: 14px; margin-top: 5px; color: #444;">[Phrase d'explication (ex: "Le coût est nul grâce à l'exonération...")]</p>
</div>

<div style="margin-top: 20px; border-top: 1px solid #ccc; padding-top: 10px; font-size: 11px; color: #666; line-height: 1.5;">
    <strong>Sources utilisées :</strong> {sources_list}<br>
    <em>Données chiffrées issues de la mise à jour : {date_maj}.</em><br>
    <span style="font-style: italic; color: #626267;">Attention : Cette réponse est basée sur le droit commun. Une convention collective (CCN) peut être plus favorable. Vérifiez toujours votre CCN.</span>
</div>

QUESTION : {question}
""")
    
    # 1. AJOUTE CETTE LIGNE JUSTE ICI (elle définit la variable manquante)
    date_ref = engine.get_yaml_update_date()

    # 2. ENSUITE TON BLOC DE RETOUR EXISTANT
    chain = prompt | llm | StrOutputParser()
    return chain.stream({
        "context": context, 
        "question": query, 
        "sources_list": ", ".join(sources_list) if sources_list else "Référentiel interne", 
        "certified_facts": facts_section,
        "user_doc_section": user_doc_section,
        "date_maj": date_ref
    })
# --- UI PRINCIPALE ---
user_email = st.session_state.get("user_email", "")
if user_email and user_email != "ADMINISTRATEUR" and user_email != "Utilisateur Promo":
    with st.sidebar:
        st.write(f"👤 {user_email}")
        if st.button("💳 Abonnement"): 
            l = manage_subscription_link(user_email)
            if l: st.link_button("Stripe", l)

# 1. ARGUMENTS
render_top_columns()

# 2. COPYRIGHT / LIENS (EN HAUT) AVEC STYLE HARMONISE
st.markdown("<div style='margin-bottom: 10px;'></div>", unsafe_allow_html=True)
c_line = st.columns([1.2, 0.8, 0.8, 3], vertical_alignment="center")
with c_line[0]: st.markdown("<span class='footer-text'>© 2026 socialexpertfrance.fr</span>", unsafe_allow_html=True)
with c_line[1]: 
    if st.button("Mentions Légales", key="top_mentions", type="tertiary"): modal_mentions()
with c_line[2]: 
    if st.button("Confidentialité", key="top_rgpd", type="tertiary"): modal_rgpd()

st.markdown("<hr style='margin-top:5px; margin-bottom:15px'>", unsafe_allow_html=True)

# ✅ ICI LA MODIFICATION : ON APPELLE LA NOUVELLE FONCTION DE VEILLE
if st.session_state.user_email == "ADMINISTRATEUR": show_legal_watch_bar()

if "uploader_key" not in st.session_state: st.session_state.uploader_key = 0

# 3. ACTIONS (GAUCHE - METHODE FANTÔME)
col_act1, col_act2, _ = st.columns([1.5, 1.5, 4], vertical_alignment="center", gap="small")

with col_act1:
    st.markdown('<div class="fake-upload-btn">Charger un document</div>', unsafe_allow_html=True)
    uploaded_file = st.file_uploader("Upload", type=["pdf", "txt"], label_visibility="collapsed", key=f"uploader_{st.session_state.uploader_key}")

with col_act2:
    if st.button("Nouvelle session", use_container_width=True):
        st.session_state.messages = []
        st.session_state.uploader_key += 1
        st.rerun()

# 4. TITRE
st.markdown("<h1>EXPERT SOCIAL PRO ESPACE ABONNÉS</h1>", unsafe_allow_html=True)

# LOGIQUE
user_text = None
if uploaded_file:
    try:
        if uploaded_file.type == "application/pdf":
            reader = pypdf.PdfReader(uploaded_file)
            user_text = "\n".join([p.extract_text() for p in reader.pages if p.extract_text()])
        else:
            user_text = uploaded_file.read().decode("utf-8")
        st.toast(f"📎 {uploaded_file.name}", icon="✅")
    except: st.error("Erreur lecture")

if "messages" not in st.session_state: st.session_state.messages = []
for m in st.session_state.messages:
    with st.chat_message(m["role"], avatar=("avatar-logo.png" if m["role"]=="assistant" else None)): st.markdown(m["content"], unsafe_allow_html=True)

if q := st.chat_input("Posez votre question (ou utilisez le bouton ci-dessus pour les documents à analyser)"):
    st.session_state.messages.append({"role": "user", "content": q})
    with st.chat_message("user"): st.markdown(q)
    with st.chat_message("assistant", avatar="avatar-logo.png"):
        ph = st.empty()
        cleaned_q = clean_query_for_engine(q)
        facts = engine.format_certified_facts(engine.match_rules(cleaned_q))
        ctx, srcs = build_context(q)
        full_resp = ""
        for chunk in get_gemini_response_stream(q, ctx, srcs, facts, user_text):
            full_resp += chunk
            ph.markdown(full_resp + "▌", unsafe_allow_html=True)
        if uploaded_file: full_resp += f"\n* 📄 Doc: {uploaded_file.name}"
        ph.markdown(full_resp + "<br><br>", unsafe_allow_html=True)
    st.session_state.messages.append({"role": "assistant", "content": full_resp})
# ============================================================
# FICHIER : app.py V34 (ONBOARDING & FRAMING)
# ============================================================
import streamlit as st
import os
import pypdf
import stripe
import requests
from bs4 import BeautifulSoup
from email.utils import parsedate_to_datetime
from datetime import datetime, timezone
import re
import unicodedata
from dotenv import load_dotenv
from supabase import create_client, Client
from utils.pdf_gen import create_pdf_report

# --- IMPORTS SERVICES ---
from services.stripe_service import verify_active_subscription, create_checkout_session

# --- IMPORTS UI ---
from ui.styles import apply_pro_design, render_top_columns, render_subscription_cards, render_footer

# --- IMPORTS IA ---
from rules.engine import SocialRuleEngine
from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAIEmbeddings
from langchain_pinecone import PineconeVectorStore
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

# --- 1. CHARGEMENT CONFIG & SECRETS ---
load_dotenv()

# ✅ CONFIGURATION DE LA PAGE AVEC TON AVATAR
st.set_page_config(
    page_title="Expert Social Pro 2026 - Le Copilote RH et Paie",
    page_icon="avatar-logo.png",
    layout="wide"
)

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
# MODULE VEILLE (BOSS / SERVICE-PUBLIC / NET-ENTREPRISES)
# ==============================================================================
FRENCH_MONTHS = {
    "janvier": 1, "février": 2, "mars": 3, "avril": 4, "mai": 5, "juin": 6,
    "juillet": 7, "août": 8, "septembre": 9, "octobre": 10, "novembre": 11, "décembre": 12
}

def get_headers():
    return {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "Accept-Language": "fr-FR,fr;q=0.9,en-US;q=0.8,en;q=0.7"
    }

def get_boss_status_html():
    target_url = "https://boss.gouv.fr/portail/accueil/actualites.html"
    try:
        url = "https://boss.gouv.fr/portail/fil-rss-boss-rescrit/pagecontent/flux-actualites.rss"
        response = requests.get(url, headers=get_headers(), timeout=12)
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
    except Exception as e:
        print(f"Erreur BOSS: {e}")
    return f"<div style='background-color:#f8f9fa; color:#555; padding:10px; border-radius:6px; border:1px solid #ddd; margin-bottom:8px; font-size:13px;'>ℹ️ <strong>Veille BOSS</strong> : Flux indisponible <a href='{target_url}' target='_blank' style='text-decoration:underline; color:inherit; font-weight:bold;'>[Accès direct]</a></div>"

def get_service_public_status():
    target_url = "https://entreprendre.service-public.gouv.fr/actualites"
    try:
        response = requests.get(target_url, headers=get_headers(), timeout=15)
        if response.status_code == 200:
            soup = BeautifulSoup(response.content, 'html.parser')
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
    except Exception as e:
        print(f"Erreur SP: {e}")
    return f"<div style='background-color:#f8f9fa; color:#555; padding:10px; border-radius:6px; border:1px solid #ddd; margin-bottom:8px; font-size:13px;'>ℹ️ <strong>Veille Service-Public</strong> : Flux indisponible <a href='{target_url}' target='_blank' style='text-decoration:underline; color:inherit; font-weight:bold;'>[Accès direct]</a></div>"

def get_net_entreprises_status():
    target_url = "https://www.net-entreprises.fr/actualites/"
    try:
        url = "https://www.net-entreprises.fr/feed/"
        response = requests.get(url, headers=get_headers(), timeout=12)
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
    except Exception as e:
        print(f"Erreur NetEnt: {e}")
    return f"<div style='background-color:#f8f9fa; color:#555; padding:10px; border-radius:6px; border:1px solid #ddd; margin-bottom:8px; font-size:13px;'>ℹ️ <strong>Veille Net-Entreprises</strong> : Flux indisponible <a href='{target_url}' target='_blank' style='text-decoration:underline; color:inherit; font-weight:bold;'>[Accès direct]</a></div>"

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

# --- 2. AUTHENTIFICATION ---
def check_password():
    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False

    if st.session_state.authenticated:
        return True

    # 1. ARGUMENTS EN HAUT
    render_top_columns()
    
    # 2. FOOTER
    render_footer()

    st.markdown("<h1>EXPERT SOCIAL PRO - ACCÈS</h1>", unsafe_allow_html=True)
    
    t1, t2 = st.tabs(["🔐 Je suis abonné", "J'ai un code découverte"])
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
        
        # --- SECTION ABONNEMENT ---
        st.subheader("PAS ENCORE ABONNÉ ?")
        st.write("Débloquez l'accès illimité et le mode Expert Social 2026.")
        render_subscription_cards()

    # --- ONGLET 2 : CODES D'ACCÈS ---
    with t2:
        code = st.text_input("Code", type="password")
        if st.button("Valider", use_container_width=True):
            if code == os.getenv("ADMIN_PASSWORD"):
                st.session_state.authenticated = True
                st.session_state.user_email = "ADMINISTRATEUR"
                st.rerun()
            elif code == os.getenv("APP_PASSWORD"):
                st.session_state.authenticated = True
                st.session_state.user_email = "Utilisateur Promo"
                st.rerun()
            elif code == os.getenv("CODE_PROMO_ANDRH"):
                st.session_state.authenticated = True
                st.session_state.user_email = "Membre ANDRH (Invité)"
                st.rerun()
            else: 
                st.error("Code faux")
    return False

if not check_password(): st.stop()

# ============================================================
# SÉCURITÉ STRIPE : VÉRIFICATION D'ABONNEMENT
# ============================================================
user_email = st.session_state.get("user_email")
ADMIN_EMAILS = ["ton.email@admin.com"] 

# On ne vérifie que si c'est un email classique (pas un code admin/promo/invité)
if user_email and user_email not in ["ADMINISTRATEUR", "Utilisateur Promo", "Membre ANDRH (Invité)"]:
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
            checkout_url = create_checkout_session("Mensuel", user_email)
            if checkout_url:
                st.link_button("S'abonner (Mensuel)", checkout_url, type="primary")
        
        st.stop()

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
    raw_docs = vectorstore.similarity_search(query, k=30)
    context_text, sources_seen = "", []
    
    for d in raw_docs:
        category = d.metadata.get('category', 'AUTRE')
        raw_src = d.metadata.get('source', 'Inconnu')
        
        if category == "REF":
            pretty_src = "Barèmes & Chiffres 2026"
        elif category == "DOC":
            pretty_src = "BOSS / Jurisprudence"
        elif category == "CODES":
            pretty_src = "Code du Travail / Sécu"
        else:
            pretty_src = os.path.basename(raw_src).replace('.pdf', '').replace('.txt', '')

        if pretty_src not in sources_seen:
            sources_seen.append(pretty_src)
            
        context_text += f"[DOCUMENT : {pretty_src}]\n{d.page_content}\n\n"
    
    return context_text, sources_seen

def get_gemini_response_stream(query, context, sources_list, certified_facts="", user_doc_content=None):
    user_doc_section = f"\n--- DOCUMENT UTILISATEUR ---\n{user_doc_content}\n" if user_doc_content else ""
    facts_section = f"\n--- FAITS CERTIFIÉS 2026 ---\n{certified_facts}\n" if certified_facts else ""
    
# === PROMPT IA ===
    prompt = ChatPromptTemplate.from_template("""
Tu es l'Expert Social Pro 2026.

RÈGLE DE FORME ABSOLUE (CRITIQUE) :
1. Tu dois générer du **HTML BRUT** destiné à être injecté directement dans une page web.
2. ⚠️ Ne mets JAMAIS de balises de code (pas de ```html, pas de ```).
3. INTERDICTION TOTALE du Markdown pour les titres (Pas de #, ##, ###, ####). Utilise uniquement <h4 style="...">.
4. Ne laisse jamais apparaître les balises <ul>, <li> ou <br> sous forme de texte visible. Elles doivent servir au formatage invisible.

--- 1. LOGIQUE MÉTIER & CALCUL ---
- RÈGLE ABSOLUE (DATA-DRIVEN) :
  Avant de lancer un calcul, SCANNE LE CONTEXTE (YAML/RAG).
  SI UNE VALEUR EST DÉJÀ PRÉSENTE (ex: "plafond_journalier", "montant_forfaitaire", "seuil"), UTILISE-LA TEL QUEL.
  ⛔ INTERDICTION DE RECALCULER une donnée si elle est fournie. Fais confiance au YAML (c'est la source de vérité 2026).

- MAPPING SMIC/FILLON : Utilise 'T_moins_50' (0.3981) ou 'T_plus_50' (0.4021) uniquement pour la Réduction Générale.

- RÈGLE "COÛT ZÉRO" (SMIC) :
  Si on demande le coût ou les charges pour un salaire égal au SMIC :
  1. Règle Juridique : Au niveau du SMIC, la Réduction Générale est maximale et égale au paramètre T.
  2. Calcul du Coefficient : Utilise STRICTEMENT Coefficient = T (soit T_moins_50 ou T_plus_50). Ne fais JAMAIS le calcul (1.6 * ...).
  3. Montant Exonération = Salaire Brut x T.
  4. Considère que [Charges Dues] = [Montant Exonération].
  5. Affiche "0,00 €" en résultat final (car Charges - Exonération = 0).
  
  ⚠️ GESTION DES SOURCES (CRITIQUE) :
  CITE TOUJOURS L'ARTICLE PRÉCIS (ex: Code du travail - Art. L1234-9, ou BOSS - Fiche Frais Pro).
  Ne dis JAMAIS juste "Code du Travail".
  Interdiction d'afficher les noms de fichiers techniques (REF_, DOC_, PDF).

--- 2. CONTEXTE RAG ---
{certified_facts}
{context}
{user_doc_section}

--- 3. TEMPLATE DE RÉPONSE (A REMPLIR) ---

<h4 style="color: #024c6f; border-bottom: 1px solid #ddd;">Analyse & Règles</h4>
<ul>
    <li>[Insérer ici les règles juridiques avec Article Précis]</li>
</ul>

<h4 style="color: #024c6f; border-bottom: 1px solid #ddd; margin-top:20px;">
    [TITRE : "Calcul de l'Exonération" (si Fillon) OU "Calcul & Application" (si Autre)]
</h4>

<div style="background-color: #f9f9f9; padding: 15px; border-radius: 5px; border: 1px solid #eee;">
    <strong>Données utilisées :</strong> [Lister les données chiffrées]<br>
    <strong>Détail :</strong><br>
    
    [INSTRUCTION DE RENDU DU CALCUL] :
    - Génère une liste à puces HTML (<ul><li>) sans indentation Markdown avant.
    - Détaille le calcul étape par étape.
</div>

<div style="background-color: #f0f8ff; padding: 20px; border-left: 5px solid #024c6f; margin: 25px 0;">
    <h2 style="color: #024c6f; margin-top: 0;">🎯 CONCLUSION</h2>
    <p style="font-size: 18px;"><strong>Résultat : [RÉSULTAT FINAL CALCULÉ]</strong></p>
    <p style="font-size: 14px; margin-top: 5px; color: #444;">[Phrase d'explication]</p>
</div>

<div style="margin-top: 20px; border-top: 1px solid #ccc; padding-top: 10px; padding-bottom: 25px; font-size: 11px; color: #666; line-height: 1.5;">
    <strong>Sources utilisées :</strong> {sources_list}<br>
    <em>Données chiffrées issues de la mise à jour : {date_maj}.</em><br>
    <span style="font-style: italic; color: #626267;">Attention : Cette réponse est basée sur le droit commun. Une convention collective (CCN) peut être plus favorable. Vérifiez toujours votre CCN.</span>
</div>

QUESTION : {question}
""")
    
    date_ref = engine.get_yaml_update_date()
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

# 2. FOOTER
render_footer()

# VEILLE JURIDIQUE
if st.session_state.user_email == "ADMINISTRATEUR": show_legal_watch_bar()

if "uploader_key" not in st.session_state: st.session_state.uploader_key = 0

# 3. ACTIONS (UPLOAD & RESET)
col_act1, col_act2, _ = st.columns([1.5, 1.5, 4], vertical_alignment="center", gap="small")

with col_act1:
    st.markdown('<div class="fake-upload-btn">Charger un document</div>', unsafe_allow_html=True)
    uploaded_file = st.file_uploader("Upload", type=["pdf", "txt"], label_visibility="collapsed", key=f"uploader_{st.session_state.uploader_key}")

with col_act2:
    if st.button("Nouvelle session", use_container_width=True):
        st.session_state.messages = []
        st.session_state.uploader_key += 1
        st.rerun()

# ============================================================
# 🛡️ DÉFINITION DES RÔLES & QUOTAS (AVANT L'AFFICHAGE)
# ============================================================
# 1. On définit les limites selon le profil
user_role = st.session_state.get("user_email", "Inconnu")

if user_role == "Membre ANDRH (Invité)":
    QUOTA_LIMIT = 30  # Limite pour le test ANDRH
elif user_role == "ADMINISTRATEUR":
    QUOTA_LIMIT = 9999 # Illimité pour toi
else:
    QUOTA_LIMIT = 20   # Sécurité standard

# 2. Initialisation du compteur
if "query_count" not in st.session_state:
    st.session_state.query_count = 0

# 4. TITRE
st.markdown("<h1>EXPERT SOCIAL PRO ESPACE ABONNÉS</h1>", unsafe_allow_html=True)

# --- INDICATEUR DE QUOTA RESTANT (V32 - Messages Pro/Neutres) ---
if user_role != "ADMINISTRATEUR":
    remaining = QUOTA_LIMIT - st.session_state.query_count
    
    # Cas 1 : C'est fini (0 question)
    if remaining <= 0:
        st.error("🛑 **Session terminée.** Veuillez vous reconnecter ou démarrer une nouvelle session pour continuer.")
    
    # Cas 2 : Il reste très peu (Zone Rouge)
    elif remaining <= 5:  
        st.warning(f"⚠️ **Attention :** Il ne vous reste que {remaining} question(s) dans cette session.")
    
    # Cas 3 : Il reste un peu (Zone Bleue)
    elif remaining <= 10:
        st.info(f"ℹ️ **Info Session :** {remaining} questions restantes.")
# -----------------------------------

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

# ✅ NOUVELLE SECTION ONBOARDING (STYLE "CARTES DISCRÈTES")
if len(st.session_state.messages) == 0:
    st.markdown("<br>", unsafe_allow_html=True) # Un peu d'espace
    st.markdown("<h5 style='text-align: center; color: #6c757d; margin-bottom: 25px;'>💡 Besoin d'inspiration ? Testez une situation réelle :</h5>", unsafe_allow_html=True)
    
    c1, c2, c3 = st.columns(3, gap="medium")
    
    # --- CARTE 1 : APPRENTI ---
    with c1:
        with st.container(border=True):
            st.markdown("###### 🎓 Apprentissage 2026")
            st.markdown("""<div style="font-size: 13px; color: #555; height: 60px; overflow: hidden;">
            "Je veux embaucher un apprenti de 22 ans. Quel est le coût exact et les exonérations en 2026 ?"
            </div>""", unsafe_allow_html=True)
            if st.button("👉 Tester ce cas", key="btn_start_1", use_container_width=True):
                st.session_state.messages.append({"role": "user", "content": "Je veux embaucher un apprenti de 22 ans. Quel est le coût exact et les exonérations en 2026 ?"})
                st.rerun()

    # --- CARTE 2 : LICENCIEMENT ---
    with c2:
        with st.container(border=True):
            st.markdown("###### ⚖️ Licenciement & Ancienneté")
            st.markdown("""<div style="font-size: 13px; color: #555; height: 60px; overflow: hidden;">
            "Calcule l'indemnité de licenciement pour un cadre avec 12 ans et 5 mois d'ancienneté (salaire 4500€)."
            </div>""", unsafe_allow_html=True)
            if st.button("👉 Tester ce cas", key="btn_start_2", use_container_width=True):
                st.session_state.messages.append({"role": "user", "content": "Calcule l'indemnité de licenciement pour un cadre avec 12 ans et 5 mois d'ancienneté (salaire 4500€)."})
                st.rerun()

    # --- CARTE 3 : VÉHICULE ÉLEC ---
    with c3:
        with st.container(border=True):
            st.markdown("###### 🚗 Avantage Véhicule Élec.")
            st.markdown("""<div style="font-size: 13px; color: #555; height: 60px; overflow: hidden;">
            "Comment calculer l'avantage en nature pour une voiture électrique de société en 2026 ?"
            </div>""", unsafe_allow_html=True)
            if st.button("👉 Tester ce cas", key="btn_start_3", use_container_width=True):
                st.session_state.messages.append({"role": "user", "content": "Comment calculer l'avantage en nature pour une voiture électrique de société en 2026 ?"})
                st.rerun()

    st.markdown("<br>", unsafe_allow_html=True)

for m in st.session_state.messages:
    with st.chat_message(m["role"], avatar=("avatar-logo.png" if m["role"]=="assistant" else None)): 
        st.markdown(m["content"], unsafe_allow_html=True)

# ============================================================
# 💬 BARRE DE SAISIE & TRAITEMENT (V32 - Quota UX Amélioré)
# ============================================================

# On vérifie si le quota est atteint
quota_reached = st.session_state.query_count >= QUOTA_LIMIT

# Si quota atteint, on affiche un message et on empêche la saisie
if quota_reached:
    st.warning(f"🛑 **Limite de session atteinte ({QUOTA_LIMIT} questions).**")
    st.info("💡 Pour continuer, veuillez démarrer une nouvelle session.")
    q = None 
else:
    # ✅ NOUVEAU TEXTE D'AIDE "MENTAL FRAMING" (Avec Rappel Document)
    q = st.chat_input("Posez votre situation concrète (ex: calcul paie...) ou utilisez le bouton plus haut pour analyser un document.")

if q:
    # On augmente le compteur quand une question est posée
    st.session_state.query_count += 1
    
    # Gestion du message utilisateur
    st.session_state.messages.append({"role": "user", "content": q})
    with st.chat_message("user"): st.markdown(q)
    
    # Gestion de la réponse IA
    with st.chat_message("assistant", avatar="avatar-logo.png"):
        ph = st.empty()
        
        # Préparation du contexte
        cleaned_q = clean_query_for_engine(q)

        # --- AJOUT KPI STATISTIQUES (LOGS GOOGLE CLOUD) ---
        print(f"[KPI_QUESTION] Utilisateur a demandé : {q}", flush=True) 
        # --------------------------------------------------

        facts = engine.format_certified_facts(engine.match_rules(cleaned_q))
        ctx, srcs = build_context(q)
        full_resp = ""
        
        # Fonction locale pour nettoyer le texte (Code blocks + Indentation parasite)
        def clean_text_for_display(text):
            # 1. On vire les balises de code Markdown
            text = text.replace("```html", "").replace("```", "")
            # 2. On supprime l'indentation (espaces) au début de chaque ligne
            lines = [line.lstrip() for line in text.splitlines()]
            return "\n".join(lines)

        # Boucle de génération (Streaming)
        for chunk in get_gemini_response_stream(q, ctx, srcs, facts, user_text):
            full_resp += chunk
            clean_resp = clean_text_for_display(full_resp)
            ph.markdown(f'<div class="ai-response">{clean_resp}▌</div>', unsafe_allow_html=True)
        
        # Nettoyage final et affichage
        final_clean_resp = clean_text_for_display(full_resp)
        
        # Ajout du document analysé si nécessaire
        if uploaded_file: 
            final_clean_resp += f'<br><p style="font-size:12px; color:gray;">📄 Document analysé : {uploaded_file.name}</p>'
        
        # Rendu final sans curseur
        ph.markdown(f'<div class="ai-response">{final_clean_resp}</div>', unsafe_allow_html=True)
        
        # Enregistrement dans l'historique
        st.session_state.messages.append({"role": "assistant", "content": final_clean_resp})

        # --- GÉNÉRATION ET TÉLÉCHARGEMENT PDF ---
        try:
            # 1. CRÉATION DU NOM DE FICHIER "ANTI-BLABLA"
            
            # Liste des mots inutiles (enrichie)
            stop_words = {
                # Salutations / Politesse
                "bonjour", "bonsoir", "salut", "hey", "cher", "chere", "merci", "svp", "stp", "plait",
                # Pronoms
                "je", "tu", "il", "elle", "nous", "vous", "ils", "elles", "on", "moi", "toi", "lui",
                # Verbes de demande / volonté
                "voudrais", "aimerais", "souhaite", "désire", "veux", "peux", "dois", "doit", "faut", "falloir",
                "savoir", "connaitre", "avoir", "demande", "question", "est-ce", "aller", "faire",
                # Articles et liaisons courts
                "le", "la", "les", "un", "une", "des", "du", "de", "d", "l",
                "et", "ou", "mais", "ou", "donc", "ni", "car", "a", "à", "en", "y", "dans", "par", "pour", "sur",
                # Relatifs
                "qui", "que", "quoi", "dont", "ou", "qu", "quel", "quelle", "quels", "quelles", "comment", "combien", "pourquoi",
                # Verbe Être / Avoir courants
                "est", "sont", "suis", "es", "ai", "as", "ont", "avez", "sommes", "etes"
            }

            # On normalise (enlève les accents)
            nfkd_form = unicodedata.normalize('NFKD', q)
            no_accent = "".join([c for c in nfkd_form if not unicodedata.combining(c)])
            
            # On ne garde que les lettres et chiffres
            clean_str = re.sub(r'[^a-zA-Z0-9\s]', '', no_accent)
            
            # On découpe en mots
            all_words = clean_str.split()
            
            # ON FILTRE : On ne garde que les mots utiles
            useful_words = [w for w in all_words if w.lower() not in stop_words][:8]
            
            # Sécurité : Si le filtre a tout supprimé, on remet les premiers mots bruts
            if not useful_words:
                useful_words = all_words[:8]

            short_title = "_".join(useful_words) 
            
            # Nom final
            final_filename = f"Reponse_{short_title}.pdf"

            # 2. GÉNÉRATION DU PDF
            pdf_bytes = create_pdf_report(q, full_resp, ", ".join(srcs))
            
            # 3. AFFICHAGE DU BOUTON
            st.download_button(
                label="📄 Télécharger le rapport (PDF)",
                data=pdf_bytes,
                file_name=final_filename,
                mime="application/pdf",
                key=f"pdf_btn_{st.session_state.query_count}"
            )
        except Exception as e:
            # On loggue pour nous (console Google)
            print(f"[ERREUR PDF] : {e}", flush=True) 
            # On avertit l'utilisateur (interface)
            st.error("⚠️ Une erreur technique empêche la génération de ce PDF spécifique. Essayez de reformuler légèrement la question.")
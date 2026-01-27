# ============================================================
# FICHIER : app.py V53 (FIX SERVICE-PUBLIC VIA RSS)
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

# ✅ CONFIGURATION DE LA PAGE
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
# MODULE VEILLE (V3 - BLINDAGE LIENS RSS & AFFICHAGE)
# ==============================================================================
def get_headers():
    return {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "Accept-Language": "fr-FR,fr;q=0.9,en-US;q=0.8,en;q=0.7",
        "Cache-Control": "no-cache",
        "Pragma": "no-cache"
    }

def parse_rss_date(date_str):
    try:
        dt = parsedate_to_datetime(date_str)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt
    except:
        return datetime.now(timezone.utc)

def format_feed_alert(source_name, title, link, pub_date, color_bg_alert="#f8d7da", color_text_alert="#721c24", color_bg_ok="#d4edda", color_text_ok="#155724"):
    days = (datetime.now(timezone.utc) - pub_date).days
    date_str = pub_date.strftime("%d/%m")
    
    if days < 3:
        return f"<div style='background-color:{color_bg_alert}; color:{color_text_alert}; padding:10px; border-radius:6px; border:1px solid {color_bg_alert}; margin-bottom:8px; font-size:13px;'>🚨 <strong>NOUVEAU {source_name} ({date_str})</strong> : <a href='{link}' target='_blank' style='text-decoration:underline; font-weight:bold; color:inherit;'>{title}</a></div>"
    else:
        return f"<div style='background-color:{color_bg_ok}; color:{color_text_ok}; padding:10px; border-radius:6px; border:1px solid {color_bg_ok}; margin-bottom:8px; font-size:13px; opacity:0.9;'>✅ <strong>Veille {source_name} (R.A.S)</strong> : Dernière actu du {date_str} <a href='{link}' target='_blank' style='margin-left:5px; text-decoration:underline; color:inherit; font-size:11px;'>[Voir]</a></div>"

def get_robust_link(item, default_url):
    """Récupère le lien coûte que coûte (Link, Guid ou Regex)."""
    # 1. Essai balise <link> standard
    try:
        link = item.find('link')
        if link and link.text.strip():
            return link.text.strip()
    except: pass

    # 2. Essai balise <guid> (Souvent le permalink dans le RSS)
    try:
        guid = item.find('guid')
        if guid and guid.text.strip() and "http" in guid.text:
            return guid.text.strip()
    except: pass

    # 3. Essai Regex Brutale (Dernier recours si le parser a vidé la balise)
    try:
        match = re.search(r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', str(item))
        if match:
            return match.group(0)
    except: pass

    return default_url

# --- BOSS ---
def get_boss_status_html():
    target_url = "https://boss.gouv.fr/portail/accueil/actualites.html"
    rss_url = "https://boss.gouv.fr/portail/fil-rss-boss-rescrit/pagecontent/flux-actualites.rss"
    try:
        response = requests.get(rss_url, headers=get_headers(), timeout=8)
        if response.status_code == 200:
            soup = BeautifulSoup(response.content, 'html.parser')
            item = soup.find('item')
            if item:
                title = item.find('title').text.strip()
                link = get_robust_link(item, target_url)
                date_tag = item.find('pubdate') or item.find('pubDate')
                pub_date = parse_rss_date(date_tag.text) if date_tag else datetime.now(timezone.utc)
                return format_feed_alert("BOSS", title, link, pub_date)
    except Exception as e:
        print(f"Erreur BOSS: {e}")
    return f"<div style='background-color:#f8f9fa; color:#555; padding:10px; border-radius:6px; border:1px solid #ddd; margin-bottom:8px; font-size:13px;'>ℹ️ <strong>Veille BOSS</strong> : Flux indisponible <a href='{target_url}' target='_blank' style='text-decoration:underline; color:inherit; font-weight:bold;'>[Accès direct]</a></div>"

# --- SERVICE PUBLIC ---
def get_service_public_status():
    target_url = "https://entreprendre.service-public.gouv.fr/actualites"
    rss_url = "https://www.service-public.fr/abonnements/rss/actu-actu-pro.rss"
    try:
        response = requests.get(rss_url, headers=get_headers(), timeout=8)
        if response.status_code == 200:
            soup = BeautifulSoup(response.content, 'html.parser')
            item = soup.find('item')
            if item:
                title = item.find('title').text.strip()
                # Utilisation de la fonction robuste pour éviter le lien vide
                link = get_robust_link(item, target_url)
                date_tag = item.find('pubdate') or item.find('pubDate')
                pub_date = parse_rss_date(date_tag.text) if date_tag else datetime.now(timezone.utc)
                return format_feed_alert("Service-Public", title, link, pub_date, color_bg_ok="#d1ecf1", color_text_ok="#0c5460")
    except Exception as e:
        print(f"Erreur SP: {e}")
    return f"<div style='background-color:#f8f9fa; color:#555; padding:10px; border-radius:6px; border:1px solid #ddd; margin-bottom:8px; font-size:13px;'>ℹ️ <strong>Veille Service-Public</strong> : Flux indisponible <a href='{target_url}' target='_blank' style='text-decoration:underline; color:inherit; font-weight:bold;'>[Accès direct]</a></div>"

# --- NET ENTREPRISES ---
def get_net_entreprises_status():
    target_url = "https://www.net-entreprises.fr/actualites/"
    rss_url = "https://www.net-entreprises.fr/feed/"
    try:
        response = requests.get(rss_url, headers=get_headers(), timeout=8)
        if response.status_code == 200:
            soup = BeautifulSoup(response.content, 'html.parser')
            item = soup.find('item')
            if item:
                title = item.find('title').text.strip()
                link = get_robust_link(item, target_url)
                date_tag = item.find('pubdate') or item.find('pubDate')
                pub_date = parse_rss_date(date_tag.text) if date_tag else datetime.now(timezone.utc)
                return format_feed_alert("Net-Entreprises", title, link, pub_date, color_bg_ok="#fff3cd", color_text_ok="#856404")
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

    render_top_columns()
    render_footer()

   # --- TITRE & SOUS-TITRE (Nouvelle Version) ---
    st.markdown("""
        <h1 style='text-align: center; color: #024c6f; margin-bottom: 8px;'>
            EXPERT SOCIAL PRO — VOTRE COPILOTE RH & PAIE EN 2026.
        </h1>
        <h2 style='text-align: center; text-transform: none !important; color: #2c3e50; font-family: "Open Sans", sans-serif; font-size: 16px; font-weight: 600; margin-bottom: 30px; line-height: 1.5;'>
            Des règles officielles. Des calculs sans erreur. Des décisions que vous pouvez défendre.
        </h2>
    """, unsafe_allow_html=True)
    
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
        
        st.subheader("PAS ENCORE ABONNÉ ?")
        st.write("Débloquez l'accès illimité et le mode Expert Social 2026.")
        render_subscription_cards()

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
# SÉCURITÉ STRIPE
# ============================================================
user_email = st.session_state.get("user_email")
ADMIN_EMAILS = ["ton.email@admin.com"] 

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
        filename = os.path.basename(raw_src).replace('.pdf', '').replace('.txt', '')
        
        # ✅ TRANSLATION PURE (RENOMMAGE INTELLIGENT)
        
        # 1. CIBLAGE SPÉCIFIQUE DES CODES (Pour virer "FULL")
        if "Code_Travail" in filename or "Code Travail" in filename:
            pretty_src = "Code du Travail 2026"
        elif "Code_Secu" in filename or "Code Secu" in filename:
            pretty_src = "Code de la Sécurité Sociale 2026"
            
        # 2. LES AUTRES CATÉGORIES
        elif category == "REF":
            pretty_src = "Barèmes Officiels 2026"
        elif category == "DOC":
            pretty_src = "BOSS 2026 et Jurisprudences"
        elif category == "CODES":
            # Pour les articles isolés s'il y en a
            pretty_src = filename.replace('_', ' ')
        else:
            pretty_src = filename.replace('_', ' ')

        # On évite les doublons
        if pretty_src not in sources_seen:
            sources_seen.append(pretty_src)
            
        context_text += f"[SOURCE : {pretty_src}]\n{d.page_content}\n\n"
    
    return context_text, sources_seen
# ==============================================================================
# FONCTION IA PRINCIPALE (VERSION V72 - CORRECTION FORMATAGE)
# ==============================================================================
def get_gemini_response_stream(query, context, sources_list, certified_facts="", user_doc_content=None):
    user_doc_section = f"\n--- DOCUMENT UTILISATEUR ---\n{user_doc_content}\n" if user_doc_content else ""
    facts_section = f"\n--- FAITS CERTIFIÉS 2026 ---\n{certified_facts}\n" if certified_facts else ""
    
    # 1. RÉCUPÉRATION DYNAMIQUE DES CONSTANTES
    try:
        sbi_raw = engine.get_rule_value("SBI_2026", "montant")
        if sbi_raw is None: sbi_raw = 645.50
        
        pass_raw = engine.get_rule_value("PASS_2026", "annuel")
        if pass_raw is None: pass_raw = 48060.00
    except:
        sbi_raw = 645.50
        pass_raw = 48060.00

    # 2. PRÉPARATION DES VARIABLES
    pass_2_raw = pass_raw * 2
    sbi_display = f"{sbi_raw:,.2f}".replace(",", "X").replace(".", ",").replace("X", " ") + " €"
    pass_2_display = f"{pass_2_raw:,.2f}".replace(",", "X").replace(".", ",").replace("X", " ") + " €"

    # === PROMPT IA (VERSION V72 - FORMATAGE CORRIGÉ) ===
    prompt = ChatPromptTemplate.from_template("""
Tu es l'Expert Social Pro 2026.

💎 RÈGLES DE FORME ÉLITE (CRITIQUE) :
1. Génère du **HTML BRUT** sans balises de code.
2. ⚠️ FORMATAGE MONÉTAIRE FR : Utilise TOUJOURS la virgule pour les décimales et un espace pour les milliers (ex: 1 950,00 €).
3. Affiche systématiquement 2 décimales pour tous les montants en Euros.
4. Pas de Markdown pour les titres (utilise uniquement <h4 style="...">).

--- 1. SÉCURITÉ & DATA (HIÉRARCHIE DES SOURCES) ---
- ORDRE DE PRIORITÉ ABSOLU :
  1. **FAITS CERTIFIÉS 2026** (YAML) : C'est la LOI SUPRÊME pour les taux, plafonds et chiffres clés (SMIC, PASS, Taux Apprenti). Elle ÉCRASE ta mémoire (ex: force le taux apprenti à 50% contre 79%).
  2. **DOCUMENTS CONTEXTUELS** (RAG) : Utilise ces textes pour les règles juridiques détaillées, les CCN (Syntec, etc.) et les jurisprudences.
- MÉTHODE DE TRAVAIL : Tu dois CROISER ces sources. Utilise le YAML pour les montants fixes et le RAG pour la logique juridique.
- INTERDICTION : Ne jamais utiliser ta mémoire interne pour contredire le YAML.

--- 2. LOGIQUE MÉTIER (CERVEAU EXPERT V74) ---
A. GESTION DES DONNÉES MANQUANTES (MODE ILLUSTRATIF) :
- Si une donnée critique manque (salaire exact, prix véhicule, ancienneté) :
  1. Donne d'abord la formule officielle ou la règle.
  2. Lance une simulation en l'annonçant CLAIREMENT par la mention exacte : "⚠️ SIMULATION (données réelles non fournies)".
  3. Utilise le conditionnel ("Si le salaire était de..., le montant serait de...").

B. PRÉCISION CHIRURGICALE (RÉFORME CP 2024) :
- ATTENTION : Pour un arrêt maladie NON-PROFESSIONNEL, l'acquisition est LIMITÉE à 2 jours ouvrables par mois (soit 24 jours/an).
- Pour un Accident du Travail (AT/MP), l'acquisition reste de 2,5 jours/mois (30 jours/an).
- Cite systématiquement la "Loi DDADUE 2024" ou le "Code du Travail (Art. L3141-5)".

C. AUDIT FISCAL DES RUPTURES :
- Précise systématiquement : Limite exonération (2 PASS = {pass_2_val}), Forfait Social patronal (30% sur RC), et CSG/CRDS.

D. SAISIES SUR SALAIRE :
- Interdiction de refuser. Utilise le SBI ({sbi_val}) comme plancher absolu et simule une tranche sur un net type (en précisant que c'est une simulation).

E. VIGILANCE MATHÉMATIQUE & FORMULES DE PAIE (CRITIQUE) :
- PRORATISATION SMIC : Calcul en deux temps OBLIGATOIRE.
  1. Valeur horaire : (1 823,03 / 35) ≈ 52,0866 €
  2. Multiplie ensuite par les heures du contrat.
  3. Exemple référence 24h : 52,0866 * 24 = 1 250,08 €.
- MENSUALISATION : Pour passer d'une valeur HEBDOMADAIRE à MENSUELLE, utilise le coefficient standard : **4,3333** (52 semaines / 12 mois).
- TEMPS DE TRAVAIL : ⛔ PIÈGE : 1h30 n'est pas 1,30h mais **1,50h**. Convertis toujours les minutes en centièmes (30 min = 0,50 ; 45 min = 0,75).
- IJSS SÉCU : Le diviseur pour la maladie est **91,25** (et non 90). Formule : (Salaires 3 derniers mois) / 91,25.

B. PRÉCISION CHIRURGICALE (RÉFORME CP 2024) :
- ATTENTION : Pour un arrêt maladie NON-PROFESSIONNEL, l'acquisition est LIMITÉE à 2 jours ouvrables par mois (soit 24 jours/an).
- Pour un Accident du Travail (AT/MP), l'acquisition reste de 2,5 jours/mois (30 jours/an).
- Cite systématiquement la "Loi DDADUE 2024" ou le "Code du Travail (Art. L3141-5)".

C. AUDIT FISCAL DES RUPTURES :
- Précise systématiquement : Limite exonération (2 PASS = {pass_2_val}), Forfait Social patronal (30% sur RC), et CSG/CRDS.

D. SAISIES SUR SALAIRE :
- Interdiction de refuser. Utilise le SBI ({sbi_val}) comme plancher absolu et simule une tranche sur un net type (en précisant que c'est une simulation).

--- 3. GESTION DES SOURCES (ABRÉVIATIONS JURIDIQUES) ---
- CITE LA SOURCE ENTRE PARENTHÈSES À LA FIN DE LA PHRASE CONCERNÉE.
- ⛔ INTERDICTION d'écrire "Source :" ou "Ref :".
- FORMATAGE EXPERT (Instructions strictes) : 
  * Code du Travail : Utilise le format (Art. [Insérer Numéro] C. trav.)
  * Code de la Sécurité Sociale : Utilise le format (Art. [Insérer Numéro] CSS)
  * Barèmes/BOSS : Utilise le nom court (ex: BOSS 2026, Barèmes Officiels).

--- 4. CONTEXTE RAG ---
{certified_facts}
{context}
{user_doc_section}

--- 5. TEMPLATE DE RÉPONSE ---

<h4 style="color: #024c6f; border-bottom: 1px solid #ddd;">Analyse & Règles</h4>
<ul>
    <li>[Règle juridique avec Citation courte entre parenthèses]</li>
</ul>

<h4 style="color: #024c6f; border-bottom: 1px solid #ddd; margin-top:20px;">Détail & Chiffres</h4>

<div style="background-color: #f9f9f9; padding: 15px; border-radius: 5px; border: 1px solid #eee;">
    <strong>Données clés :</strong> [Valeurs utilisées]<br>
    <strong>Calcul :</strong><br>
    <ul>
       <li>[Étape 1 : Calcul détaillé]</li>
       <li>[Étape 2 : Résultat au format 0 000,00 €]</li>
    </ul>
    <div style="margin-top: 15px; padding-top: 10px; border-top: 1px dashed #999; font-size: 13px; color: #444;">
        <strong>⚠️ Note :</strong> [Mention "SIMULATION (données réelles non fournies)" si applicable]
    </div>
</div>

<div style="background-color: #f0f8ff; padding: 20px; border-left: 5px solid #024c6f; margin: 25px 0;">
    <h2 style="color: #024c6f; margin-top: 0;">🎯 RÉSULTAT</h2>
    <p style="font-size: 18px;"><strong>[Montant Final au format 0 000,00 €]</strong></p>
    <p style="font-size: 14px; margin-top: 5px; color: #444;">[Conclusion courte et experte]</p>
</div>

<div style="margin-top: 20px; border-top: 1px solid #ccc; padding-top: 10px; padding-bottom: 25px; font-size: 11px; color: #666; line-height: 1.5;">
    <strong>Sources utilisées :</strong> {sources_list}<br>
    <em>Données chiffrées issues de la mise à jour : {date_maj}.</em><br>
    <span style="font-style: italic; color: #626267;">Attention : Cette réponse est basée sur le droit commun. Vérifiez toujours votre CCN.</span>
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
        "date_maj": date_ref,
        "sbi_val": sbi_display,      
        "pass_2_val": pass_2_display 
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

# 3. ACTIONS
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
# 🛡️ RÔLES & QUOTAS
# ============================================================
user_role = st.session_state.get("user_email", "Inconnu")

if user_role == "Membre ANDRH (Invité)":
    QUOTA_LIMIT = 20  
elif user_role == "ADMINISTRATEUR":
    QUOTA_LIMIT = 9999 
else:
    QUOTA_LIMIT = 20   

if "query_count" not in st.session_state:
    st.session_state.query_count = 0

st.markdown("<h1>EXPERT SOCIAL PRO ESPACE ABONNÉS</h1>", unsafe_allow_html=True)

if user_role != "ADMINISTRATEUR":
    remaining = QUOTA_LIMIT - st.session_state.query_count
    if remaining <= 0:
        st.error("🛑 **Session terminée.**")
    elif remaining <= 5:  
        st.warning(f"⚠️ **Attention :** Il ne vous reste que {remaining} question(s).")
    elif remaining <= 10:
        st.info(f"ℹ️ **Info Session :** {remaining} questions restantes.")

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

# ONBOARDING
user_role = st.session_state.get("user_email", "")
DISCOVERY_USERS = ["Utilisateur Promo", "Membre ANDRH (Invité)"]

if len(st.session_state.messages) == 0 and user_role in DISCOVERY_USERS:
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

for m in st.session_state.messages:
    with st.chat_message(m["role"], avatar=("avatar-logo.png" if m["role"]=="assistant" else None)): 
        st.markdown(m["content"], unsafe_allow_html=True)

# BARRE DE SAISIE
quota_reached = st.session_state.query_count >= QUOTA_LIMIT

if quota_reached:
    st.warning(f"🛑 **Limite de session atteinte ({QUOTA_LIMIT} questions).**")
    st.info("Pour continuer, envisagez de vous abonner.")
    q = None 
else:
    if "pending_prompt" in st.session_state and st.session_state.pending_prompt:
        q = st.session_state.pending_prompt
        del st.session_state.pending_prompt 
    else:
        q = st.chat_input("Posez votre situation concrète (ex: règles, calcul paie...) et/ou chargez un document grace au bouton plus haut")

if q:
    st.session_state.query_count += 1
    st.session_state.messages.append({"role": "user", "content": q})
    with st.chat_message("user"): st.markdown(q)
    
    with st.chat_message("assistant", avatar="avatar-logo.png"):
        ph = st.empty()
        cleaned_q = clean_query_for_engine(q)
        print(f"[KPI_QUESTION] Utilisateur a demandé : {q}", flush=True) 

        facts = engine.format_certified_facts(engine.match_rules(cleaned_q))
        ctx, srcs = build_context(q)
        full_resp = ""
        
        def clean_text_for_display(text):
            text = text.replace("```html", "").replace("```", "")
            lines = [line.lstrip() for line in text.splitlines()]
            return "\n".join(lines)

        for chunk in get_gemini_response_stream(q, ctx, srcs, facts, user_text):
            full_resp += chunk
            clean_resp = clean_text_for_display(full_resp)
            ph.markdown(f'<div class="ai-response">{clean_resp}▌</div>', unsafe_allow_html=True)
        
        final_clean_resp = clean_text_for_display(full_resp)
        if uploaded_file: 
            final_clean_resp += f'<br><p style="font-size:12px; color:gray;">📄 Document analysé : {uploaded_file.name}</p>'
        
        ph.markdown(f'<div class="ai-response">{final_clean_resp}</div>', unsafe_allow_html=True)
        st.session_state.messages.append({"role": "assistant", "content": final_clean_resp})

        # PDF GENERATION
        try:
            stop_words = {"bonjour", "merci", "je", "tu", "le", "la", "les", "un", "une", "des", "et", "ou", "est", "sont"}
            nfkd_form = unicodedata.normalize('NFKD', q)
            no_accent = "".join([c for c in nfkd_form if not unicodedata.combining(c)])
            clean_str = re.sub(r'[^a-zA-Z0-9\s]', '', no_accent)
            all_words = clean_str.split()
            useful_words = [w for w in all_words if w.lower() not in stop_words][:8]
            if not useful_words: useful_words = all_words[:8]
            short_title = "_".join(useful_words) 
            final_filename = f"Reponse_{short_title}.pdf"

            pdf_bytes = create_pdf_report(q, full_resp, ", ".join(srcs))
            
            st.download_button(
                label="📄 Télécharger le rapport (PDF)",
                data=pdf_bytes,
                file_name=final_filename,
                mime="application/pdf",
                key=f"pdf_btn_{st.session_state.query_count}"
            )
        except Exception as e:
            print(f"[ERREUR PDF] : {e}", flush=True) 
            st.error("⚠️ Erreur PDF.")
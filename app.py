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
from ui.styles import apply_pro_design, render_top_columns, render_subscription_cards
from rules.engine import SocialRuleEngine
from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAIEmbeddings
from langchain_pinecone import PineconeVectorStore
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

# ✅ Stripe checkout
from services.stripe_service import create_checkout_session

# --- 1. CONFIG ---
load_dotenv()
st.set_page_config(page_title="Expert Social Pro France", layout="wide")
apply_pro_design()

url = os.getenv("SUPABASE_URL")
key = os.getenv("SUPABASE_KEY")
supabase: Client = create_client(url, key)
stripe.api_key = os.getenv("STRIPE_API_KEY")

# --- FONCTIONS UTILITAIRES ---
def manage_subscription_link(email):
    try:
        customers = stripe.Customer.list(email=email, limit=1)
        if customers and len(customers.data) > 0:
            session = stripe.billing_portal.Session.create(
                customer=customers.data[0].id,
                return_url="https://socialexpertfrance.fr" 
            )
            return session.url
    except: pass
    return None

# ==============================================================================
# MODULE DE VEILLE JURIDIQUE "FAIL-SAFE" (AFFICHAGE GARANTI)
# ==============================================================================

def extract_date_from_text(text):
    """
    Tente de trouver une date dans un texte brut (RSS ou HTML) via Regex.
    Gère les formats : JJ/MM/AAAA, YYYY-MM-DD, JJ mois AAAA.
    """
    text = text.lower()
    MONTHS = {
        "janvier": 1, "fevrier": 2, "février": 2, "mars": 3, "avril": 4, "mai": 5, "juin": 6,
        "juillet": 7, "aout": 8, "août": 8, "septembre": 9, "octobre": 10, "novembre": 11, "decembre": 12, "décembre": 12
    }
    
    try:
        # 1. Format ISO (2026-01-17)
        match_iso = re.search(r"(\d{4})-(\d{2})-(\d{2})", text)
        if match_iso:
            return datetime(int(match_iso.group(1)), int(match_iso.group(2)), int(match_iso.group(3)), tzinfo=timezone.utc)

        # 2. Format Français (17 janvier 2026)
        match_fr = re.search(r"(\d{1,2})\s+(janvier|fevrier|février|mars|avril|mai|juin|juillet|aout|août|septembre|octobre|novembre|decembre|décembre)\s+(\d{4})", text)
        if match_fr:
            day = int(match_fr.group(1))
            month = MONTHS[match_fr.group(2)]
            year = int(match_fr.group(3))
            return datetime(year, month, day, tzinfo=timezone.utc)
            
        # 3. Format RSS Standard (17 Jan 2026)
        match_rss = re.search(r"(\d{1,2})\s+(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+(\d{4})", text, re.IGNORECASE)
        if match_rss:
             return parsedate_to_datetime(match_rss.group(0)).replace(tzinfo=timezone.utc)

    except: pass
    return None

def get_status_line(source_name, url, colors, check_mode="rss"):
    """
    Génère la ligne HTML pour une source donnée.
    check_mode : 'rss' (lit un flux XML) ou 'web' (tente de lire une page HTML).
    FORCE L'AFFICHAGE même si l'analyse échoue.
    """
    # Couleurs
    bg_col, border_col, txt_col = colors
    style_base = f"padding: 10px; border-radius: 6px; border: 1px solid {border_col}; margin-bottom: 8px; font-size: 13px;"
    
    # Valeurs par défaut (si échec)
    display_html = f"<div style='background-color:{bg_col}; color:{txt_col}; {style_base} opacity:0.9;'>ℹ️ <strong>Veille {source_name}</strong> : Accès direct aux actualités <a href='{url}' target='_blank' style='text-decoration:underline; font-weight:bold; color:inherit;'>(Ouvrir le site)</a></div>"
    
    try:
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"}
        
        # Pour l'URSSAF, on ne tente même plus de parser si ça échoue trop souvent, 
        # on affiche juste le lien si le check_mode est 'static'
        if check_mode == "static":
            return display_html

        response = requests.get(url, headers=headers, timeout=6)
        
        if response.status_code == 200:
            content = response.text
            
            # --- 1. RECHERCHE DE LA DATE (Sur tout le contenu brut, c'est plus fiable) ---
            # On coupe le contenu pour ne pas lire le footer (souvent des vieilles dates copyright)
            snippet = content[:5000] 
            found_date = extract_date_from_text(snippet)
            
            # --- 2. RECHERCHE DU TITRE (Si RSS) ---
            title = "Actualités récentes"
            if check_mode == "rss":
                soup = BeautifulSoup(content, 'html.parser')
                item = soup.find('item') or soup.find('entry')
                if item:
                    title_tag = item.find('title')
                    if title_tag: title = title_tag.text.strip()
                    # Si on trouve une date spécifique dans l'item, elle est prioritaire
                    item_date = extract_date_from_text(str(item))
                    if item_date: found_date = item_date

            # --- 3. CALCUL DU STATUT ---
            if found_date:
                now = datetime.now(timezone.utc)
                days_old = (now - found_date).days
                date_str = found_date.strftime("%d/%m")
                
                # ALERTE ROUGE (< 8 jours)
                if days_old < 8:
                    return f"<div style='background-color:#f8d7da; color:#721c24; {style_base}'>🚨 <strong>NOUVEAU {source_name} ({date_str})</strong> : <a href='{url}' target='_blank' style='text-decoration:underline; font-weight:bold; color:inherit;'>{title}</a></div>"
                
                # R.A.S (Vert/Bleu/Orange)
                else:
                    return f"<div style='background-color:{bg_col}; color:{txt_col}; {style_base} opacity:0.9;'>✅ <strong>Veille {source_name} (R.A.S)</strong> : Dernière actu du {date_str} <a href='{url}' target='_blank' style='color:inherit; font-size:11px; margin-left:5px; text-decoration:underline;'>(Voir)</a></div>"

    except Exception:
        pass # En cas d'erreur technique, on retourne le display_html par défaut (Ligne visible avec lien)

    return display_html

def show_legal_watch_bar():
    if "news_closed" not in st.session_state: st.session_state.news_closed = False
    if st.session_state.news_closed: return

    # 1. BOSS (RSS Standard - Vert)
    html_boss = get_status_line(
        "BOSS", 
        "https://boss.gouv.fr/portail/fil-rss-boss-rescrit/pagecontent/flux-actualites.rss",
        ("#d4edda", "#c3e6cb", "#155724"),
        check_mode="rss"
    )
    
    # 2. Service-Public (RSS Complexe - Bleu)
    html_social = get_status_line(
        "Social & Loi", 
        "https://rss.service-public.fr/rss/pro-social-sante.xml",
        ("#d1ecf1", "#bee5eb", "#0c5460"),
        check_mode="rss"
    )
    
    # 3. URSSAF (Page Web protégée - Orange)
    # On force l'affichage du lien direct vers la page actus. 
    # On tente un check 'web', mais si ça échoue, la fonction renverra le lien par défaut.
    html_urssaf = get_status_line(
        "URSSAF", 
        "https://www.urssaf.fr/accueil/actualites.html",
        ("#fff3cd", "#ffeeba", "#856404"),
        check_mode="web" 
    )

    full_html = html_boss + html_social + html_urssaf
    
    if full_html:
        c1, c2 = st.columns([0.95, 0.05])
        with c1: st.markdown(full_html, unsafe_allow_html=True)
        with c2: 
            if st.button("✖️", key="btn_close_news"): 
                st.session_state.news_closed = True
                st.rerun()

# --- POPUPS ---
@st.dialog("Mentions Légales")
def modal_mentions():
    st.markdown("<div style='font-size:13px; color:#333;'>ÉDITEUR : BUSINESS AGENT AI<br>Contact : sylvain.attal@businessagent-ai.com<br>PROPRIÉTÉ : Tous droits réservés.</div>", unsafe_allow_html=True)

@st.dialog("RGPD")
def modal_rgpd():
    st.markdown("<div style='font-size:13px; color:#333;'>Pas de cookies pub. Données en RAM uniquement.</div>", unsafe_allow_html=True)

# --- 2. AUTHENTIFICATION ---
def check_password():
    if "authenticated" not in st.session_state: st.session_state.authenticated = False
    if st.session_state.authenticated: return True

    render_top_columns() # ARGUMENTS EN HAUT
    
    # LIGNE COPYRIGHT
    st.markdown("<div style='margin-bottom: 10px;'></div>", unsafe_allow_html=True)
    c_line = st.columns([1.2, 0.8, 0.8, 3], vertical_alignment="center")
    with c_line[0]: st.markdown("<span class='footer-text'>© 2026 socialexpertfrance.fr</span>", unsafe_allow_html=True)
    with c_line[1]: 
        if st.button("Mentions Légales", key="login_m", type="tertiary"): modal_mentions()
    with c_line[2]: 
        if st.button("RGPD & Cookies", key="login_r", type="tertiary"): modal_rgpd()

    st.markdown("<hr style='margin-top:5px; margin-bottom:15px'>", unsafe_allow_html=True)
    st.markdown("<h2>EXPERT SOCIAL PRO - ACCÈS</h2>", unsafe_allow_html=True)
    
    t1, t2 = st.tabs(["🔐 Abonnés", "Découverte / Admin"])
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

# --- 3. MOTEUR ---
@st.cache_resource
def load_engine(): return SocialRuleEngine()

@st.cache_resource
def load_ia():
    api = os.getenv("GOOGLE_API_KEY")
    emb = GoogleGenerativeAIEmbeddings(model="models/text-embedding-004", google_api_key=api)
    vec = PineconeVectorStore.from_existing_index(index_name="expert-social", embedding=emb)
    llm = ChatGoogleGenerativeAI(model="gemini-2.0-flash", temperature=0, google_api_key=api)
    return vec, llm

try:
    with st.spinner("Chargement..."): engine = load_engine(); vectorstore, llm = load_ia()
except Exception as e: st.error(f"Erreur: {e}"); st.stop()

def clean_q(q):
    words = q.lower().split()
    return " ".join([w for w in words if w not in ["le", "la", "les", "du", "de", "un", "une", "est", "quel"]])

def build_ctx(q):
    docs = vectorstore.similarity_search(q, k=25)
    txt, srcs = "", []
    for d in docs:
        src = d.metadata.get('source', 'Inconnu')
        name = os.path.basename(src).replace('.pdf', '')
        if "REF" in name: pretty = "Barème Officiel"
        elif "LEGAL" in name: pretty = "Code du Travail"
        elif "BOSS" in name: pretty = "BOSS"
        else: pretty = name
        srcs.append(pretty)
        txt += f"[DOC: {pretty}]\n{d.page_content}\n\n"
    return txt, list(set(srcs))

def get_stream(q, ctx, srcs, facts, user_doc):
    u_sec = f"\n--- DOC UTILISATEUR ---\n{user_doc}\n" if user_doc else ""
    f_sec = f"\n--- FAITS 2026 ---\n{facts}\n" if facts else ""
    
    # === PROMPT OPTIMISÉ (RÈGLE D'ABORD) ===
    tpl = """Tu es l'Expert Social Pro 2026. Réponse fiable et aérée.
    
    STRUCTURE DE RÉPONSE:
    <h4 style="color:#024c6f; border-bottom:1px solid #ddd;">Analyse & Règles</h4>
    <ul>
        <li>
            <strong>ÉNONCÉ D'ABORD :</strong> Explique clairement la règle en premier.
            <br><em>(Source : Cite l'article ou le BOSS ici, à la fin)</em>
        </li>
    </ul>
    
    <h4 style="color:#024c6f; border-bottom:1px solid #ddd; margin-top:20px;">Calcul</h4>
    <ul><li>Détail étape par étape...</li></ul>
    
    <div style="background:#f0f8ff; padding:20px; border-left:5px solid #024c6f; margin:20px 0;">
        <h3 style="color:#024c6f; margin:0;">🎯 CONCLUSION DÉFINITIVE</h3>
        [RÉSULTAT]
    </div>
    
    CTX: {context} """ + u_sec + """
    FAITS: {facts_section}
    Q: {question}
    SRCS: {sources_list}"""
    
    prompt = ChatPromptTemplate.from_template(tpl)
    chain = prompt | llm | StrOutputParser()
    return chain.stream({"context": ctx, "question": q, "sources_list": ", ".join(srcs), "facts_section": f_sec})

# --- UI ABONNÉ ---
u_email = st.session_state.user_email
if u_email not in ["ADMINISTRATEUR", "Utilisateur Promo"]:
    with st.sidebar:
        st.write(f"👤 {u_email}")
        if st.button("💳 Gérer abo"):
            l = manage_subscription_link(u_email)
            if l: st.link_button("Stripe", l)

# 1. ARGUMENTS (Longs)
render_top_columns()

# 2. FOOTER HAUT
st.markdown("<div style='margin-bottom: 10px;'></div>", unsafe_allow_html=True)
c_line = st.columns([1.2, 0.8, 0.8, 3], vertical_alignment="center")
with c_line[0]: st.markdown("<span class='footer-text'>© 2026 socialexpertfrance.fr</span>", unsafe_allow_html=True)
with c_line[1]: 
    if st.button("Mentions Légales", key="top_m", type="tertiary"): modal_mentions()
with c_line[2]: 
    if st.button("RGPD & Cookies", key="top_r", type="tertiary"): modal_rgpd()

st.markdown("<hr style='margin-top:5px; margin-bottom:15px'>", unsafe_allow_html=True)

# 3. VEILLE MULTI-SOURCES (Visible uniquement par l'ADMIN pour l'instant)
if u_email == "ADMINISTRATEUR": 
    show_legal_watch_bar()

if "uploader_key" not in st.session_state: st.session_state.uploader_key = 0

# 4. ACTIONS (GAUCHE - METHODE FANTÔME)
col_a, col_b, _ = st.columns([1.5, 1.5, 4], vertical_alignment="center", gap="small")

with col_a:
    st.markdown('<div class="fake-upload-btn">Charger un document</div>', unsafe_allow_html=True)
    uploaded = st.file_uploader("Upload", type=["pdf", "txt"], label_visibility="collapsed", key=f"up_{st.session_state.uploader_key}")

with col_b:
    if st.button("Nouvelle session", use_container_width=True):
        st.session_state.messages = []
        st.session_state.uploader_key += 1
        st.rerun()

# 5. TITRE
st.markdown("<h1>EXPERT SOCIAL PRO ABONNÉS</h1>", unsafe_allow_html=True)

user_text = None
if uploaded:
    try:
        reader = pypdf.PdfReader(uploaded)
        user_text = "\n".join([p.extract_text() for p in reader.pages if p.extract_text()])
        st.toast(f"📎 {uploaded.name}", icon="✅")
    except: st.error("Erreur fichier")

if "messages" not in st.session_state: st.session_state.messages = []
for m in st.session_state.messages:
    with st.chat_message(m["role"], avatar=("avatar-logo.png" if m["role"]=="assistant" else None)): st.markdown(m["content"], unsafe_allow_html=True)

if q := st.chat_input("Votre question..."):
    st.session_state.messages.append({"role": "user", "content": q})
    with st.chat_message("user"): st.markdown(q)
    with st.chat_message("assistant", avatar="avatar-logo.png"):
        ph = st.empty()
        clean_q = clean_q(q)
        facts = engine.format_certified_facts(engine.match_rules(clean_q))
        ctx, srcs = build_ctx(q)
        full = ""
        for chunk in get_stream(q, ctx, srcs, facts, user_text):
            full += chunk
            ph.markdown(full + "▌", unsafe_allow_html=True)
        if uploaded: full += f"\n* 📄 Doc: {uploaded.name}"
        ph.markdown(full + "<br><br>", unsafe_allow_html=True)
    st.session_state.messages.append({"role": "assistant", "content": full})
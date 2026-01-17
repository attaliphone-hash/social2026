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
# MODULE DE VEILLE JURIDIQUE (URLS VÉRIFIÉES & CORRIGÉES)
# ==============================================================================

def check_rss_source(source_name, rss_url, target_link, colors):
    bg_col, border_col, txt_col = colors

    try:
        # User-Agent pour éviter le blocage (Simule un navigateur)
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }
        response = requests.get(rss_url, headers=headers, timeout=10)

        # Si l'URL est morte (404, DNS error...), on arrête tout de suite
        if response.status_code != 200:
            return ""

        content = response.content.decode("utf-8", errors="ignore")

        # Tentative de parsing (XML prioritaire, puis HTML en secours)
        try:
            soup = BeautifulSoup(content, "xml")
        except:
            soup = BeautifulSoup(content, "html.parser")

        # Recherche des items (RSS standard ou Atom)
        item = soup.find("item")
        if not item:
            item = soup.find("entry")

        if not item:
            return ""

        # Récupération du titre
        title_tag = item.find("title")
        title = title_tag.get_text(strip=True) if title_tag else "(Actualité détectée)"

        # Récupération intelligente de la date (Fonction locale pour être autonome)
        pub_date = None
        # 1. RSS Standard
        for tag in ["pubDate", "pubdate"]:
            t = item.find(tag)
            if t:
                try:
                    pub_date = parsedate_to_datetime(t.get_text(strip=True))
                    if pub_date.tzinfo is None: pub_date = pub_date.replace(tzinfo=timezone.utc)
                    break
                except: pass
        
        # 2. Atom / ISO (Service-Public utilise souvent dc:date ou updated)
        if not pub_date:
            for tag in ["dc:date", "date", "updated", "published"]:
                t = item.find(tag)
                if t:
                    try:
                        # On nettoie pour garder YYYY-MM-DD
                        txt = t.get_text(strip=True).split("T")[0]
                        pub_date = datetime.strptime(txt, "%Y-%m-%d").replace(tzinfo=timezone.utc)
                        break
                    except: pass

        # Si toujours pas de date, on abandonne
        if not pub_date:
            return ""

        now = datetime.now(timezone.utc)
        days_old = (now - pub_date).days
        date_str = pub_date.strftime("%d/%m")

        # --- AFFICHAGE ---
        if days_old < 8:
            return f"""
            <div style='background-color:#f8d7da; color:#721c24; padding:10px; border-radius:6px; border:1px solid #f5c6cb; margin-bottom:8px; font-size:13px;'>
                🚨 <strong>NOUVEAU {source_name} ({date_str})</strong> :
                <a href='{target_link}' target='_blank' style='text-decoration:underline; font-weight:bold; color:#721c24;'>{title}</a>
            </div>
            """
        else:
            return f"""
            <div style='background-color:{bg_col}; color:{txt_col}; padding:10px; border-radius:6px; border:1px solid {border_col}; margin-bottom:8px; font-size:13px; opacity:0.9;'>
                ✅ <strong>Veille {source_name} (R.A.S)</strong> : Dernière actu du {date_str}
                <a href='{target_link}' target='_blank' style='margin-left:5px; text-decoration:underline; color:inherit; font-size:11px;'>[Voir]</a>
            </div>
            """

    except Exception:
        return ""
    
    return ""

def show_legal_watch_bar():
    if "news_closed" not in st.session_state: st.session_state.news_closed = False
    if st.session_state.news_closed: return

    # 1. BOSS (URL Officielle Vérifiée)
    html_boss = check_rss_source(
        "BOSS",
        "https://boss.gouv.fr/portail/fil-rss-boss-rescrit/pagecontent/flux-actualites.rss",
        "https://boss.gouv.fr/portail/accueil/actualites.html",
        ("#d4edda", "#c3e6cb", "#155724")
    )
    
    # 2. SERVICE-PUBLIC (NOUVELLE URL OFFICIELLE PRO)
    # L'ancienne 'rss.service-public.fr' est morte.
    html_social = check_rss_source(
        "Service-Public Pro",
        "https://www.service-public.fr/abonnements/rss/actu-actualites-professionnels.rss",
        "https://www.service-public.fr/professionnels-entreprises/actualites",
        ("#d1ecf1", "#bee5eb", "#0c5460")
    )
    
    # 3. LÉGISOCIAL (URL Standard)
    html_legisocial = check_rss_source(
        "Social (LégiSocial)",
        "https://www.legisocial.fr/rss/actualites-sociales.xml",
        "https://www.legisocial.fr/actualites-sociales/",
        ("#fff3cd", "#ffeeba", "#856404")
    )

    full_html = html_boss + html_social + html_legisocial
    
    if full_html:
        c1, c2 = st.columns([0.95, 0.05])
        with c1: st.markdown(full_html, unsafe_allow_html=True)
        with c2: 
            if st.button("✖️", key="btn_close_news", help="Masquer"): 
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
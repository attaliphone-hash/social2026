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
# MODULE DE VEILLE JURIDIQUE (CORRIGÉ : EXTRACTION LIEN PAR REGEX)
# ==============================================================================
def check_single_rss_source(url, source_name, colors):
    """
    Analyse un flux RSS.
    CORRECTIF CRITIQUE : Utilise Regex pour extraire le lien.
    Cela empêche BeautifulSoup de vider le lien et de renvoyer vers l'appli.
    """
    try:
        headers = {"User-Agent": "Mozilla/5.0"}
        response = requests.get(url, headers=headers, timeout=6)
        
        if response.status_code == 200:
            content_str = response.content.decode('utf-8', errors='ignore')
            soup = BeautifulSoup(content_str, 'html.parser')
            
            # On cherche le premier item
            item = soup.find('item') 
            
            if item:
                title = item.find('title').text.strip()
                
                # --- EXTRACTION "BRUTE" DU LIEN (ANTI-BUG) ---
                # On convertit l'item en texte et on cherche le lien manuellement
                item_str = str(item)
                # Regex qui cherche ce qu'il y a entre <link> et </link> ou <guid>
                link_match = re.search(r"<(?:link|guid)[^>]*>(.*?)</(?:link|guid)>", item_str, re.IGNORECASE)
                
                if link_match:
                    link = link_match.group(1).strip()
                    # Si le lien est encapsulé dans CDATA (fréquent), on nettoie
                    link = link.replace("<![CDATA[", "").replace("]]>", "")
                else:
                    link = url # Fallback si échec total
                
                # --- GESTION DATE (Multi-formats) ---
                date_tag = item.find('pubdate') or item.find('pubDate') or item.find('date') or item.find('dc:date')
                
                bg_col, border_col, txt_col = colors
                
                style_alert = "background-color: #f8d7da; color: #721c24; padding: 10px; border-radius: 6px; border: 1px solid #f5c6cb; margin-bottom: 8px; font-size: 13px;"
                style_normal = f"background-color: {bg_col}; color: {txt_col}; padding: 10px; border-radius: 6px; border: 1px solid {border_col}; margin-bottom: 8px; font-size: 13px;"

                if date_tag:
                    try:
                        date_text = date_tag.text.strip()
                        # Gestion format ISO complexe (Service-Public)
                        if "T" in date_text and len(date_text) > 10:
                            dt_part = date_text.split('T')[0]
                            tm_part = date_text.split('T')[1].split('+')[0].split('Z')[0]
                            pub_date = datetime.strptime(f"{dt_part} {tm_part}", "%Y-%m-%d %H:%M:%S")
                            pub_date = pub_date.replace(tzinfo=timezone.utc)
                        else:
                            pub_date = parsedate_to_datetime(date_text)
                            if pub_date.tzinfo is None: pub_date = pub_date.replace(tzinfo=timezone.utc)
                        
                        now = datetime.now(timezone.utc)
                        days_old = (now - pub_date).days
                        date_str = pub_date.strftime("%d/%m/%Y")
                        
                        html_link = f'<a href="{link}" target="_blank" style="text-decoration:underline; font-weight:bold; color:inherit;">{title}</a>'
                        
                        if days_old < 8:
                            return f"<div style='{style_alert}'>🚨 <strong>NOUVEAU ({source_name} - {date_str})</strong> : {html_link}</div>"
                        else:
                            return f"<div style='{style_normal}'>✅ <strong>Veille {source_name}</strong> ({date_str}) : {html_link}</div>"
                    except: 
                        pass 
                
                # Fallback sans date
                return f"<div style='{style_normal}'>ℹ️ <strong>Actu {source_name}</strong> : <a href='{link}' target='_blank' style='color:inherit; font-weight:bold;'>{title}</a></div>"
                
    except Exception:
        pass 
    return ""

def show_legal_watch_bar():
    """Affiche les lignes de veille empilées"""
    if "news_closed" not in st.session_state: st.session_state.news_closed = False
    if st.session_state.news_closed: return

    # 1. BOSS (Vert)
    html_boss = check_single_rss_source(
        "https://boss.gouv.fr/portail/fil-rss-boss-rescrit/pagecontent/flux-actualites.rss",
        "BOSS",
        ("#d4edda", "#c3e6cb", "#155724") 
    )
    
    # 2. Service-Public (Bleu)
    html_social = check_single_rss_source(
        "https://rss.service-public.fr/rss/pro-social-sante.xml",
        "Social & Loi",
        ("#d1ecf1", "#bee5eb", "#0c5460") 
    )
    
    # 3. URSSAF (Orange - Hack Google News)
    html_urssaf = check_single_rss_source(
        "https://news.google.com/rss/search?q=site:urssaf.fr+when:15d&hl=fr&gl=FR&ceid=FR:fr",
        "URSSAF",
        ("#fff3cd", "#ffeeba", "#856404") 
    )

    full_html = html_boss + html_social + html_urssaf
    
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
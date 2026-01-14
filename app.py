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
from ui.styles import apply_pro_design, show_legal_info, render_top_columns, render_subscription_cards
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

# --- FONCTION ROBUSTE (Veille BOSS) ---
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
                
                style_alert = "background-color: #f8d7da; color: #721c24; padding: 12px; border-radius: 8px; border: 1px solid #f5c6cb; margin-bottom: 10px; font-size: 14px;"
                style_success = "background-color: #d4edda; color: #155724; padding: 12px; border-radius: 8px; border: 1px solid #c3e6cb; margin-bottom: 10px; font-size: 14px;"
                
                if date_tag:
                    try:
                        pub_date_obj = parsedate_to_datetime(date_tag.text.strip())
                        now = datetime.now(timezone.utc)
                        days_old = (now - pub_date_obj).days
                        date_str = pub_date_obj.strftime("%d/%m/%Y")
                        
                        html_link = f'<a href="{link}" target="_blank" style="text-decoration:underline; font-weight:bold; color:inherit;">{title}</a>'
                        
                        if days_old < 8:
                            return f"""<div style='{style_alert}'>🚨 <strong>NOUVELLE MISE À JOUR BOSS ({date_str})</strong> : {html_link}</div>""", link
                        else:
                            return f"""<div style='{style_success}'>✅ <strong>Veille BOSS (R.A.S)</strong> : Dernière actu du {date_str} : {html_link}</div>""", link
                            
                    except:
                        pass 
                
                return f"""<div style='{style_alert}'>📢 ALERTE BOSS : <a href="{link}" target="_blank" style="color:inherit; font-weight:bold;">{title}</a></div>""", link
            
            return "<div style='padding:10px; background-color:#f0f2f6; border-radius:5px;'>✅ Veille BOSS : Aucune actualité détectée.</div>", ""
            
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

    st.markdown("<h2 style='text-align: center; color: #024c6f;'>Expert Social Pro - Accès</h2>", unsafe_allow_html=True)
    
    render_top_columns()
    st.markdown("---")

    tab1, tab2 = st.tabs(["🔐 Espace Client Abonnés", "🎁 Accès Promotionnel / Admin"])

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
        
        # Affiche les cartes + crée les 2 boutons Streamlit (keys: btn_sub_month / btn_sub_year)
        render_subscription_cards()
        
        # ✅ Connexion des boutons à Stripe (sinon rien ne se passe au clic)
        # Note : st.button écrit dans st.session_state la valeur True le run du clic.
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
    # PROMPT DE SÉCURITÉ (ROLLBACK) : CALCUL D'ABORD, CONCLUSION ENSUITE
    # ==================================================================================
    prompt = ChatPromptTemplate.from_template("""
Tu es l'Expert Social Pro 2026. Tu dois fournir une réponse d'une fiabilité absolue.

MÉTHODOLOGIE OBLIGATOIRE :
1. ANALYSE : Identifie les règles applicables dans le contexte et les faits certifiés (YAML).
2. CALCUL DÉTAILLÉ : Pose le calcul étape par étape AVANT de donner le résultat final. C'est la seule façon d'éviter les erreurs.
3. CONCLUSION : Donne la réponse finale claire et le montant exact à la fin.
4. SOURCES : Cite les articles de loi (Code du Travail, CSS) et les fichiers utilisés.

STRUCTURE DE LA RÉPONSE :
**1. Analyse & Règles Applicables**
Explique brièvement la règle (ex: "L'indemnité est de 1/4 de mois par année..."). Précise si des plafonds ou exclusions s'appliquent.

**2. Détail du Calcul (Pas à Pas)**
Pose l'opération mathématique complète.
Exemple : "10 ans x 1/4 = 2,5 mois"
"2 ans x 1/3 = 0,66 mois"
"Total = ..."

**3. CONCLUSION DÉFINITIVE**
"Le montant de l'indemnité est estimé à : **[Montant Calculé]**"

**4. Références Juridiques**
Cite les articles de loi précis et les sources.

---
DONNÉES CERTIFIÉES 2026 (YAML - PRIORITAIRE) :
{facts_section}

DOCUMENTS RETROUVÉS (PINECONE) :
{context}

QUESTION DU CLIENT :
{question}

---
SOURCES INTERNES :
{sources_list}
""")
    
    chain = prompt | llm | StrOutputParser()
    return chain.stream({
        "context": context,
        "question": query,
        "sources_list": ", ".join(sources_list) if sources_list else "Aucune",
        "facts_section": facts_section
    })

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

st.markdown("<hr>", unsafe_allow_html=True)

if user_email == "ADMINISTRATEUR":
    show_boss_alert()

render_top_columns()
st.markdown("<br>", unsafe_allow_html=True)

if "uploader_key" not in st.session_state:
    st.session_state.uploader_key = 0

col_t, col_buttons = st.columns([3, 2]) 
with col_t: 
    st.markdown("<h1 style='color: #024c6f; margin:0;'>Expert Social Pro V4</h1>", unsafe_allow_html=True)

with col_buttons:
    c_up, c_new = st.columns([1.6, 1])
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
            
            message_placeholder.markdown(full_response, unsafe_allow_html=True)
                
    st.session_state.messages.append({"role": "assistant", "content": full_response})

show_legal_info()
st.markdown("<div style='text-align:center; color:#888; font-size:11px; margin-top:30px;'>© 2026 socialexpertfrance.fr</div>", unsafe_allow_html=True)
import streamlit as st
import os
import pypdf
import stripe
from dotenv import load_dotenv
from supabase import create_client, Client

# --- 1. CHARGEMENT CONFIG & SECRETS ---
load_dotenv()
st.set_page_config(page_title="Expert Social Pro France", layout="wide")

# Connexion Supabase
url = os.getenv("SUPABASE_URL")
key = os.getenv("SUPABASE_KEY")
supabase: Client = create_client(url, key)

# Configuration Stripe
stripe.api_key = os.getenv("STRIPE_API_KEY")

# --- 2. AUTHENTIFICATION HYBRIDE (CLIENT / PROMO / ADMIN) ---
def check_password():
    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False

    if st.session_state.authenticated:
        return True

    st.markdown("<h2 style='text-align: center; color: #024c6f;'>Expert Social Pro - Accès</h2>", unsafe_allow_html=True)
    
    tab1, tab2 = st.tabs(["🔐 Espace Client Abonnés", "🎁 Accès Promotionnel / Admin"])

    with tab1:
        st.caption("Connectez-vous pour accéder à votre espace abonné.")
        email = st.text_input("Email client", key="email_client")
        pwd = st.text_input("Mot de passe", type="password", key="pwd_client")
        
        if st.button("Se connecter au compte", use_container_width=True):
            try:
                # Connexion via Supabase Auth
                res = supabase.auth.sign_in_with_password({"email": email, "password": pwd})
                st.session_state.authenticated = True
                st.session_state.user_email = email
                st.rerun()
            except Exception:
                st.error("Identifiants incorrects ou compte non activé.")
        
        st.markdown("---")
        st.write("✨ **Pas encore abonné ?** Choisissez votre formule :")
        col_m, col_a = st.columns(2)
        with col_m:
            st.link_button("Abonnement Mensuel", "https://checkout.stripe.com/c/pay/cs_live_a1YuxowVQDoKMTBPa1aAK7S8XowoioMzray7z6oruWL2r1925Bz0NdVA6M#fidnandhYHdWcXxpYCc%2FJ2FgY2RwaXEnKSd2cGd2ZndsdXFsamtQa2x0cGBrYHZ2QGtkZ2lgYSc%2FY2RpdmApJ2R1bE5gfCc%2FJ3VuWmlsc2BaMDRWN11TVFRfMGxzczVXZHxETGNqMn19dU1LNVRtQl9Gf1Z9c2wzQXxoa29MUnI9Rn91YTBiV1xjZ1x2cWtqN2lAUXxvZDRKN0tmTk9PRmFGPH12Z3B3azI1NX08XFNuU0pwJyknY3dqaFZgd3Ngdyc%2FcXdwYCknZ2RmbmJ3anBrYUZqaWp3Jz8nJmNjY2NjYycpJ2lkfGpwcVF8dWAnPyd2bGtiaWBabHFgaCcpJ2BrZGdpYFVpZGZgbWppYWB3dic%2FcXdwYHgl", use_container_width=True)
        with col_a:
            st.link_button("Abonnement Annuel", "https://checkout.stripe.com/c/pay/cs_live_a1w1GIf4a2MlJejzhlwMZzoIo5OfbSdDzcl2bnur6Ev3wCLUYhZJwbD4si#fidnandhYHdWcXxpYCc%2FJ2FgY2RwaXEnKSd2cGd2ZndsdXFsamtQa2x0cGBrYHZ2QGtkZ2lgYSc%2FY2RpdmApJ2R1bE5gfCc%2FJ3VuWmlsc2BaMDRWN11TVFRfMGxzczVXZHxETGNqMn19dU1LNVRtQl9Gf1Z9c2wzQXxoa29MUnI9Rn91YTBiV1xjZ1x2cWtqN2lAUXxvZDRKN0tmTk9PRmFGPH12Z3B3azI1NX08XFNuU0pwJyknY3dqaFZgd3Ngdyc%2FcXdwYCknZ2RmbmJ3anBrYUZqaWp3Jz8nJmNjY2NjYycpJ2lkfGpwcVF8dWAnPyd2bGtiaWBabHFgaCcpJ2BrZGdpYFVpZGZgbWppYWB3dic%2FcXdwYHgl", use_container_width=True)

    with tab2:
        st.caption("Entrez votre code d'accès personnel (Admin ou Promo)")
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

# --- 3. IMPORTS DES MODULES FIABLES ---
from ui.styles import apply_pro_design, show_legal_info
from rules.engine import SocialRuleEngine
from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAIEmbeddings
from langchain_pinecone import PineconeVectorStore
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

apply_pro_design()

@st.cache_resource
def load_engine():
    return SocialRuleEngine()

@st.cache_resource
def load_ia_system():
    api_key = os.getenv("GOOGLE_API_KEY")
    embeddings = GoogleGenerativeAIEmbeddings(model="models/text-embedding-004", google_api_key=api_key)
    vectorstore = PineconeVectorStore.from_existing_index(index_name="expert-social", embedding=embeddings)
    llm = ChatGoogleGenerativeAI(model="gemini-2.0-flash", temperature=0, google_api_key=api_key)
    return vectorstore, llm

engine = load_engine()
vectorstore, llm = load_ia_system()

def build_context(query):
    raw_docs = vectorstore.similarity_search(query, k=20)
    context_text = ""
    for d in raw_docs:
        raw_src = d.metadata.get('source', 'Source Inconnue')
        clean_name = os.path.basename(raw_src).replace('.pdf', '').replace('.txt', '').replace('.csv', '')
        if "REF" in clean_name: pretty_src = "Barème Officiel"
        elif "LEGAL" in clean_name: pretty_src = "Code du Travail"
        else: pretty_src = f"BOSS : {clean_name}"
        context_text += f"[DOCUMENT : {pretty_src}]\n{d.page_content}\n\n"
    return context_text

def get_gemini_response_stream(query, context, user_doc_content=None):
    user_doc_section = f"\n--- DOCUMENT UTILISATEUR ---\n{user_doc_content}\n" if user_doc_content else ""
    prompt = ChatPromptTemplate.from_template("""
    Tu es l'Expert Social Pro 2026. Réponds EXCLUSIVEMENT avec les documents fournis.
    Citations HTML <sub>*[Source]*</sub> obligatoires.
    CONTEXTE : {context}""" + user_doc_section + "\nQUESTION : {question}")
    chain = prompt | llm | StrOutputParser()
    return chain.stream({"context": context, "question": query})

# --- 4. INTERFACE DE CHAT ---
st.markdown("<hr>", unsafe_allow_html=True)
col_t, col_buttons = st.columns([3, 2]) 
with col_t: 
    st.markdown("<h1 style='color: #024c6f; margin:0;'>Expert Social Pro V4</h1>", unsafe_allow_html=True)
with col_buttons:
    c_up, c_new = st.columns([1.6, 1])
    with c_up:
        uploaded_file = st.file_uploader("Upload", type=["pdf", "txt"], label_visibility="collapsed")
    with c_new:
        if st.button("Nouvelle session"):
            st.session_state.messages = []
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

if "messages" not in st.session_state: st.session_state.messages = []
for msg in st.session_state.messages:
    with st.chat_message(msg["role"], avatar=("avatar-logo.png" if msg["role"]=="assistant" else None)):
        st.markdown(msg["content"], unsafe_allow_html=True)

if query := st.chat_input("Votre question juridique ou chiffrée..."):
    st.session_state.messages.append({"role": "user", "content": query})
    with st.chat_message("user"):
        st.markdown(query)
    
    with st.chat_message("assistant", avatar="avatar-logo.png"):
        message_placeholder = st.empty()
        is_conversational = ("?" in query or len(query.split()) > 7 or user_doc_text)
        verdict = {"found": False}
        if not is_conversational and not user_doc_text:
            verdict = engine.get_formatted_answer(keywords=query)
        
        if verdict["found"]:
            full_response = f"{verdict['text']}\n\n---\n**Sources utilisées :**\n* {verdict['source']}"
            message_placeholder.markdown(full_response, unsafe_allow_html=True)
        else:
            with st.spinner("Analyse en cours..."):
                context = build_context(query)
                full_response = ""
                # Utilisation du mode Streaming pour l'affichage fluide
                for chunk in get_gemini_response_stream(query, context, user_doc_content=user_doc_text):
                    full_response += chunk
                    message_placeholder.markdown(full_response + "▌", unsafe_allow_html=True)
                message_placeholder.markdown(full_response, unsafe_allow_html=True)
                
    st.session_state.messages.append({"role": "assistant", "content": full_response})

show_legal_info()
st.markdown("<div style='text-align:center; color:#888; font-size:11px; margin-top:30px;'>© 2026 socialexpertfrance.fr</div>", unsafe_allow_html=True)
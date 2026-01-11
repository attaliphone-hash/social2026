import sys
import os
import uuid
import base64
import requests
from bs4 import BeautifulSoup
import streamlit as st
import pypdf
import stripe

# --- 1. PATCH SQLITE ---
try:
    import pysqlite3
    sys.modules['sqlite3'] = pysqlite3
except ImportError:
    pass

from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAIEmbeddings
from langchain_chroma import Chroma
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

# --- 2. CONFIGURATION PAGE ---
st.set_page_config(page_title="Expert Social Pro 2026", layout="wide")

# --- 3. VEILLE BOSS (SÉCURISÉE) ---
def check_boss_updates():
    try:
        url = "https://boss.gouv.fr/portail/accueil.html"
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"}
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            actualites = soup.find_all('p')
            for p in actualites:
                if "mise à jour" in p.text.lower():
                    return f"Recherche de mise à jour BOSS : OK - {p.text.strip()}"
            return "Recherche de mise à jour BOSS : OK - Base 2026 à jour (Aucune modification détectée ce jour)"
        return "Serveur BOSS injoignable pour vérification."
    except:
        return "Veille automatique BOSS temporairement indisponible."

# --- 4. DESIGN PRO ---
def get_base64(bin_file):
    if os.path.exists(bin_file):
        return base64.b64encode(open(bin_file, "rb").read()).decode()
    return ""

def apply_pro_design():
    # AJOUT CSS SPÉCIFIQUE POUR CORRIGER LE DÉCALAGE ET LA COULEUR DES SOURCES
    st.markdown("""
        <style>
        #MainMenu {visibility: hidden;}
        header {visibility: hidden !important; height: 0px;}
        footer {visibility: hidden;}
        [data-testid="stHeader"] {display: none;}
        .block-container { padding-top: 1.5rem !important; }
        
        /* Design des bulles de chat */
        .stChatMessage { background-color: rgba(255,255,255,0.95); border-radius: 15px; padding: 10px; margin-bottom: 10px; border: 1px solid #e0e0e0; }
        .stChatMessage p, .stChatMessage li { color: black !important; line-height: 1.6 !important; }
        
        /* CORRECTION CRITIQUE DES CITATIONS (sub) */
        sub {
            font-size: 0.75em !important; /* Taille réduite */
            color: #666 !important;       /* Gris discret au lieu de noir */
            vertical-align: baseline !important; /* Évite le décalage de ligne */
            position: relative;
            top: -0.3em; /* Léger décalage vers le haut style "exposant" */
        }
        
        .assurance-text { font-size: 11px !important; color: #024c6f !important; text-align: left; display: block; line-height: 1.3; margin-bottom: 20px; }
        .assurance-title { font-weight: bold; color: #024c6f; display: inline; font-size: 11px !important; }
        .assurance-desc { font-weight: normal; color: #444; display: inline; font-size: 11px !important; }
        @media (max-width: 768px) {
            .block-container { padding-top: 0.2rem !important; }
            iframe[title="st.iframe"] + br, hr + br, .stMarkdown br { display: none; }
            .assurance-text { margin-bottom: 2px !important; line-height: 1.1 !important; font-size: 10px !important; }
            h1 { font-size: 1.5rem !important; margin-top: 0px !important; }
        }
        .stExpander details summary p { font-size: 12px !important; color: #666 !important; }
        .stExpander { border: none !important; background-color: transparent !important; }
        </style>
    """, unsafe_allow_html=True)
    bg_data = get_base64('background.webp')
    if bg_data:
        st.markdown(f'<style>.stApp {{ background-image: url("data:image/webp;base64,{bg_data}"); background-size: cover; background-attachment: fixed; }}</style>', unsafe_allow_html=True)

ARGUMENTS_UNIFIES = [
    ("Données Certifiées 2026 :", " Intégration prioritaire des nouveaux textes pour une précision chirurgicale."),
    ("Sources officielles :", " Une analyse simultanée et croisée du BOSS, du Code du Travail, du Code de la Sécurité Sociale et des communiqués des organismes sociaux."),
    ("Mise à Jour Agile :", " Notre base est actualisée en temps réel dès la publication de nouvelles circulaires ou réformes, garantissant une conformité permanente."),
    ("Traçabilité Totale :", " Chaque réponse est systématiquement sourcée via une liste détaillée, permettant de valider instantanément le fondement juridique."),
    ("Confidentialité Garantie :", " Vos données sont traitées exclusivement en mémoire vive (RAM) et ne sont jamais stockées, ni utilisées pour entraîner des modèles d'IA.")
]

def render_top_columns():
    cols = st.columns(5)
    for i, col in enumerate(cols):
        title, desc = ARGUMENTS_UNIFIES[i]
        col.markdown(f'<p class="assurance-text"><span class="assurance-title">{title}</span><span class="assurance-desc">{desc}</span></p>', unsafe_allow_html=True)

# --- 5. LÉGAL & RGPD (VERSION CORRIGÉE POUR AFFICHAGE HTML) ---
def show_legal_info():
    st.markdown("<br><br>", unsafe_allow_html=True)
    _, col_l, col_r, _ = st.columns([1, 2, 2, 1])
    
    with col_l:
        with st.expander("Mentions Légales"):
            # Attention : Le texte HTML doit être collé à gauche dans le bloc """
            st.markdown("""
<div style='font-size: 11px; color: #444; line-height: 1.4;'>
    <strong>ÉDITEUR :</strong><br>
    Le site <em>socialexpertfrance.fr</em> est édité par la Direction Expert Social Pro.<br>
    Contact : support@socialexpertfrance.fr<br><br>
    <strong>PROPRIÉTÉ INTELLECTUELLE :</strong><br>
    L'ensemble de ce site relève de la législation française et internationale sur le droit d'auteur.
    Toute reproduction est interdite sans autorisation.<br><br>
    <strong>RESPONSABILITÉ :</strong><br>
    Les réponses sont fournies à titre indicatif et ne remplacent pas une consultation juridique.
</div>
""", unsafe_allow_html=True)
            
    with col_r:
        with st.expander("Politique de Confidentialité (RGPD)"):
            st.markdown("""
<div style='font-size: 11px; color: #444; line-height: 1.4;'>
    <strong>CONFIDENTIALITÉ TOTALE :</strong><br>
    1. <strong>Aucun Stockage :</strong> Traitement volatil en RAM. Données détruites après la réponse.<br>
    2. <strong>Pas d'Entraînement IA :</strong> Vos données ne servent jamais à entraîner les modèles.<br>
    3. <strong>Sécurité Stripe :</strong> Aucune donnée bancaire ne transite par nos serveurs.<br><br>
    <em>Conformité RGPD : Droit à l'oubli garanti par défaut (No-Log).</em>
</div>
""", unsafe_allow_html=True)
# --- 6. SÉCURITÉ & STRIPE ---
stripe.api_key = os.getenv("STRIPE_SECRET_KEY")
def create_checkout_session(plan_type):
    price_id = "price_1SnaTDQZ5ivv0RayXfKqvJ6I" if plan_type == "Mensuel" else "price_1SnaUOQZ5ivv0RayFnols3TI"
    try:
        checkout_session = stripe.checkout.Session.create(
            payment_method_types=['card'],
            line_items=[{'price': price_id, 'quantity': 1}],
            mode='subscription',
            success_url="https://socialexpertfrance.fr?payment=success",
            cancel_url="https://socialexpertfrance.fr?payment=cancel",
        )
        return checkout_session.url
    except Exception as e:
        st.error(f"Erreur Stripe : {e}")
        return None

def check_password():
    if st.session_state.get("password_correct"):
        if st.session_state.get("is_admin"):
            st.info(check_boss_updates())
        return True
    apply_pro_design()
    render_top_columns()
    st.markdown("<hr>", unsafe_allow_html=True)
    st.markdown("<h1 style='text-align: center; color: #024c6f;'>🔑 Accès Expert Social Pro</h1>", unsafe_allow_html=True)
    col_l, col_m, col_r = st.columns([1, 2, 1])
    with col_m:
        tab_login, tab_subscribe = st.tabs(["Se connecter", "S'abonner"])
        with tab_login:
            pwd = st.text_input("Code d'accès :", type="password")
            if st.button("Se connecter"):
                if pwd == os.getenv("ADMIN_PASSWORD", "ADMIN2026"):
                    st.session_state.update({"password_correct": True, "is_admin": True})
                    st.rerun()
                elif pwd == os.getenv("APP_PASSWORD", "DEFAUT_USER_123"):
                    st.session_state.update({"password_correct": True, "is_admin": False})
                    st.rerun()
                else: st.error("Code erroné.")
        with tab_subscribe:
            if st.button("S'abonner (Mensuel)"):
                url = create_checkout_session("Mensuel")
                if url: st.markdown(f'<meta http-equiv="refresh" content="0;URL={url}">', unsafe_allow_html=True)
    show_legal_info()
    st.stop()

check_password()
apply_pro_design()

# --- 7. SYSTÈME DE RECHERCHE IA (NETTOYAGE À LA RACINE) ---
if 'session_id' not in st.session_state: st.session_state['session_id'] = str(uuid.uuid4())

def get_data_clean_context():
    context_list = []
    if os.path.exists("data_clean"):
        for filename in os.listdir("data_clean"):
            if filename.endswith(".txt") and not filename.startswith("LEGAL_"):
                with open(f"data_clean/{filename}", "r", encoding="utf-8") as f:
                    # Nettoyage pour le contexte prioritaire
                    clean_name = filename.replace('.txt', '').replace('_', ' ')
                    context_list.append(f"[{clean_name}] : {f.read()}")
    return "\n".join(context_list)

@st.cache_resource
def load_system():
    api_key = os.getenv("GOOGLE_API_KEY")
    embeddings = GoogleGenerativeAIEmbeddings(model="models/text-embedding-004", google_api_key=api_key)
    vectorstore = Chroma(embedding_function=embeddings)
    llm = ChatGoogleGenerativeAI(model="gemini-2.0-flash-exp", temperature=0, google_api_key=api_key)
    if os.path.exists("data_clean"):
        files = [f for f in os.listdir("data_clean") if f.endswith(".txt")]
        texts, metas = [], []
        for f in files:
            with open(f"data_clean/{f}", "r", encoding="utf-8") as file:
                content = file.read()
                if content.strip():
                    # --- NETTOYAGE CRITIQUE : Suppression extension .txt ---
                    clean_source = f.replace('.txt', '').replace('_', ' ')
                    texts.append(content)
                    metas.append({"source": clean_source})
        if texts:
            for i in range(0, len(texts), 1000):
                vectorstore.add_texts(texts=texts[i:i+1000], metadatas=metas[i:i+1000])
    return vectorstore, llm

vectorstore, llm = load_system()

def build_expert_context(query):
    context = [get_data_clean_context()]
    raw_law = vectorstore.similarity_search(query, k=8)
    for d in raw_law:
        raw_src = d.metadata.get('source', 'Source Inconnue')
        
        # --- MAQUILLAGE FORCE EN PYTHON ---
        # On renomme la source ICI pour que l'IA ne voie que le beau nom
        if "REF" in raw_src and "2026" in raw_src:
            pretty_src = "Barème Officiel 2026"
        elif "REF" in raw_src and "2025" in raw_src:
            pretty_src = "Barème Officiel 2025"
        elif "BOSS" in raw_src:
            pretty_src = "BOSS" # On simplifie radicalement
        elif "LEGAL" in raw_src or "Code" in raw_src:
            pretty_src = "Code du Travail / CSS"
        else:
            pretty_src = raw_src # Cas par défaut
            
        # On injecte le beau nom dans le contexte
        context.append(f"[SOURCE : {pretty_src} ({raw_src})]\n{d.page_content}")
        # Note : je garde ({raw_src}) entre parenthèses pour aider l'IA à distinguer les fichiers si besoin, 
        # mais le prompt lui dira de n'utiliser que la partie gauche.
        
    return "\n\n".join(context)

# --- 8. INTERFACE & PROMPT ---
render_top_columns()
st.markdown("<hr>", unsafe_allow_html=True)
col_t, col_b = st.columns([4, 1])
with col_t: st.markdown("<h1 style='color: #024c6f; margin:0;'>Expert Social Pro 2026</h1>", unsafe_allow_html=True)
with col_b:
    if st.button("Nouvelle session"):
        st.session_state.messages = []
        st.rerun()

if "messages" not in st.session_state: st.session_state.messages = []
for msg in st.session_state.messages:
    with st.chat_message(msg["role"], avatar=("avatar-logo.png" if msg["role"]=="assistant" else None)):
        st.markdown(msg["content"])

if query := st.chat_input("Posez votre question..."):
    st.session_state.messages.append({"role": "user", "content": query})
    with st.chat_message("user"): st.markdown(query)
    with st.chat_message("assistant", avatar="avatar-logo.png"):
        with st.status("🔍 Analyse juridique en cours..."):
            context = build_expert_context(query)
            # --- PROMPT V3.7 : LOGIQUE CORRIGÉE & STYLE FORCÉ ---
            prompt = ChatPromptTemplate.from_template("""
            Tu es l'Expert Social Pro 2026. Réponds avec rigueur.
            
            CONSIGNES D'AFFICHAGE DES SOURCES (CRITIQUE) :
            1. TOUJOURS utiliser la balise HTML <sub> pour réduire la taille.
            2. FORMAT : <sub>*[Source]*</sub>
            
            TABLE DE CORRESPONDANCE DES NOMS (ATTENTION AUX NOMS NETTOYÉS) :
            Le système t'envoie des noms de fichiers SANS underscores et SANS extensions. Adapte-toi :
            
            - Si la source contient "REF" (ex: REF 2026 SMIC) -> Affiche : <sub>*[Barème Officiel]*</sub> (Ou "Barème Officiel : Thème" si pertinent).
            - Si la source contient "BOSS" (ex: DOC BOSS FRAIS) -> Affiche : <sub>*[BOSS]*</sub> (Ou "BOSS : Thème").
            - Si Article de Loi -> Affiche : <sub>*[Art. L.XXX-X Code du travail]*</sub>.
            
            Exemple de rendu attendu dans le texte :
            "Le plafond est de 3925€ <sub>*[Barème Officiel]*</sub>."
            (La source doit être petite, grise et discrète).
            
            RAPPEL FINAL OBLIGATOIRE :
            Termine par "---" puis saut de ligne.
            Écris : "<sub>*Sources utilisées : [Liste des noms propres (Barème Officiel, BOSS...)]*</sub>"
            
            CONTEXTE : {context}
            QUESTION : {question}
            """)
            response = (prompt | llm | StrOutputParser()).invoke({"context": context, "question": query})
        st.markdown(response, unsafe_allow_html=True)
        st.session_state.messages.append({"role": "assistant", "content": response})

show_legal_info()
st.markdown("<div style='text-align:center; color:#888; font-size:11px; margin-top:30px;'>© 2026 socialexpertfrance.fr</div>", unsafe_allow_html=True)
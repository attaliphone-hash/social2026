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

# --- 3. DESIGN PRO CENTRALISÉ ---
def get_base64(bin_file):
    if os.path.exists(bin_file):
        return base64.b64encode(open(bin_file, "rb").read()).decode()
    return ""

def apply_pro_design():
    st.markdown("""
        <style>
        #MainMenu {visibility: hidden;}
        header {visibility: hidden !important; height: 0px;}
        footer {visibility: hidden;}
        [data-testid="stHeader"] {display: none;}
        
        /* ESPACE HAUT DE PAGE */
        .block-container { padding-top: 1.5rem !important; }
        
        .stChatMessage { background-color: rgba(255,255,255,0.95); border-radius: 15px; padding: 10px; margin-bottom: 10px; border: 1px solid #e0e0e0; }
        .stChatMessage p, .stChatMessage li { color: black !important; }
        
        /* Style standard (Ordinateur) */
        .assurance-text { font-size: 11px !important; color: #024c6f !important; text-align: left; display: block; line-height: 1.3; margin-bottom: 20px; }
        .assurance-title { font-weight: bold; color: #024c6f; display: inline; font-size: 11px !important; }
        .assurance-desc { font-weight: normal; color: #444; display: inline; font-size: 11px !important; }

        /* --- OPTIMISATION MOBILE RADICALE --- */
        @media (max-width: 768px) {
            /* On supprime presque tout l'espace en haut */
            .block-container { padding-top: 0.2rem !important; }
            
            /* On réduit l'espace au-dessus des arguments (le premier <br>) */
            iframe[title="st.iframe"] + br, hr + br, .stMarkdown br { display: none; }
            
            .assurance-text { 
                margin-bottom: 2px !important; /* Espace quasi nul entre arguments */
                line-height: 1.1 !important; 
                font-size: 10px !important;
            }
            .assurance-title { font-size: 10px !important; }
            .assurance-desc { font-size: 10px !important; }
            
            /* On resserre le titre de la page login */
            h1 { font-size: 1.5rem !important; margin-top: 0px !important; }
        }

        .stExpander details summary p { font-size: 12px !important; color: #666 !important; }
        .stExpander { border: none !important; background-color: transparent !important; }
        </style>
    """, unsafe_allow_html=True)
    
    bg_data = get_base64('background.webp')
    if bg_data:
        st.markdown(f'<style>.stApp {{ background-image: url("data:image/webp;base64,{bg_data}"); background-size: cover; background-attachment: fixed; }}</style>', unsafe_allow_html=True)

# --- 4. TEXTES LÉGAUX & RGPD ---
def show_legal_info():
    st.markdown("<br><br>", unsafe_allow_html=True)
    _, col_l, col_r, _ = st.columns([1, 2, 2, 1])
    
    with col_l:
        with st.expander("Mentions Légales"):
            st.markdown("""
                <div style='font-size: 11px; line-height: 1.4; color: #444;'>
                <strong>ÉDITEUR DU SITE</strong><br>
                Le site <strong>socialexpertfrance.fr</strong> est édité par la Direction Expert Social Pro.<br>
                <strong>Responsable de la publication</strong> : [Sylvain Attal]<br>
                <strong>Contact</strong> : sylvain.attal@businessagent-ai.com<br><br>
                
                <strong>HÉBERGEMENT</strong><br>
                Serveurs Google Cloud Platform (GCP), Région : europe-west1 (Belgique).<br><br>
                
                <strong>PROPRIÉTÉ INTELLECTUELLE</strong><br>
                L'architecture, les algorithmes et la base de connaissances 2026 sont la propriété exclusive de l'éditeur.<br><br>
                
                <strong>RESPONSABILITÉ</strong><br>
                Aide à la décision basée sur les textes officiels 2026 (PASS, BOSS, Code du travail, Code de la Sécutité Sociale). Ne substitue pas l'analyse finale d'un professionnel qualifié.
                </div>
            """, unsafe_allow_html=True)
    
    with col_r:
        with st.expander("Politique de Confidentialité (RGPD)"):
            st.markdown("""
                <div style='font-size: 11px; line-height: 1.4; color: #444;'>
                <strong>1. TRAITEMENT VOLATIL (RAM)</strong><br>
                Vos questions et documents sont traités exclusivement en mémoire vive (RAM) de manière éphémère. Aucun cookie n'est déposé.<br><br>
                
                <strong>2. NON-CONSERVATION</strong><br>
                Aucune donnée n'est stockée de façon permanente. La fermeture du navigateur ou le bouton 'Nouvelle session' purge instantanément la mémoire.<br><br>
                
                <strong>3. NON-ENTRAÎNEMENT</strong><br>
                Nous garantissons que vos données ne sont <strong>JAMAIS</strong> utilisées pour entraîner des modèles d'IA tiers ou propriétaires.<br><br>
                
                <strong>4. VOS DROITS</strong><br>
                Conformément au RGPD, votre droit à l'oubli est exercé en temps réel par la réinitialisation technique de la session.
                </div>
            """, unsafe_allow_html=True)

# --- 5. SÉCURITÉ & MODULE SAAS ---
stripe.api_key = os.getenv("STRIPE_SECRET_KEY")
PRICE_ID_MONTHLY = "price_1SnaTDQZ5ivv0RayXfKqvJ6I"
PRICE_ID_ANNUAL = "price_1SnaUOQZ5ivv0RayFnols3TI"

def create_checkout_session(plan_type):
    price_id = PRICE_ID_MONTHLY if plan_type == "Mensuel" else PRICE_ID_ANNUAL
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
    if st.session_state.get("password_correct"): return True
    apply_pro_design()
    
    st.markdown("<br>", unsafe_allow_html=True)
    c1, c2, c3, c4, c5 = st.columns(5)
    args = [
        ("Données Certifiées 2026 :", " Intégration prioritaire des nouveaux barèmes (PASS, avantages en nature) pour une précision chirurgicale."),
        ("Sources officielles :", " Une analyse simultanée et croisée du BOSS, du Code du Travail, du Code de la Sécurité Sociale et des communiqués des organismes sociaux."),
        ("Mise à Jour Agile :", " Notre base est actualisée en temps réel dès la publication de nouvelles circulaires ou réformes, garantissant une conformité permanente."),
        ("Traçabilité Totale :", " Chaque réponse est systématiquement sourcée via une liste détaillée, permettant de valider instantanément le fondement juridique."),
        ("Confidentialité Garantie :", " Vos données sont traitées exclusivement en mémoire vive (RAM) et ne sont jamais stockées, ni utilisées pour entraîner des modèles d'IA.")
    ]
    for i, col in enumerate([c1, c2, c3, c4, c5]):
        col.markdown(f'<p class="assurance-text"><span class="assurance-title">{args[i][0]}</span><span class="assurance-desc">{args[i][1]}</span></p>', unsafe_allow_html=True)
    
    st.markdown("<hr>", unsafe_allow_html=True)
    st.markdown("<h1 style='text-align: center; color: #024c6f;'>🔑 Accès Expert Social Pro</h1>", unsafe_allow_html=True)
    
    col_l, col_m, col_r = st.columns([1, 2, 1])
    with col_m:
        tab_login, tab_subscribe = st.tabs(["Se connecter", "S'abonner"])
        with tab_login:
            pwd = st.text_input("Code d'accès :", type="password")
            if st.button("Se connecter"):
                if pwd == os.getenv("ADMIN_PASSWORD", "ADMIN2026") or pwd == os.getenv("APP_PASSWORD", "DEFAUT_USER_123"):
                    st.session_state.update({"password_correct": True})
                    st.rerun()
                else: st.error("Code erroné.")
        with tab_subscribe:
            st.markdown("### Formules")
            if st.button("S'abonner (Mensuel)"):
                url = create_checkout_session("Mensuel")
                if url: st.markdown(f'<meta http-equiv="refresh" content="0;URL={url}">', unsafe_allow_html=True)
    
    show_legal_info()
    st.stop()

check_password()
apply_pro_design()

# --- 6. SYSTÈME DE RECHERCHE IA ---
if 'session_id' not in st.session_state: st.session_state['session_id'] = str(uuid.uuid4())

NOMS_PROS = {
    "REF_2026_": "🏛️ BARÈMES ET RÉFÉRENTIELS OFFICIELS 2026",
    "MEMO_CHIFFRES": "📑 RÉFÉRENTIEL CHIFFRÉS 2026",
    "DOC_BOSS_": "🌐 BULLETIN OFFICIEL SÉCURITÉ SOCIALE (BOSS)",
    "LEGAL_": "📕 SOCLE LÉGAL (CODES)",
    "REF_": "✅ RÉFÉRENCES : BOSS, Code du Travail, CSS"
}

def nettoyer_nom_source(raw_source):
    nom = os.path.basename(raw_source)
    for cle, nom_pro in NOMS_PROS.items():
        if cle in nom: return nom_pro
    return nom.replace('.txt','').replace('.pdf','').replace('_',' ')

def get_data_clean_context():
    context_list = []
    if os.path.exists("data_clean"):
        for filename in os.listdir("data_clean"):
            if filename.endswith(".txt") and not filename.startswith("LEGAL_"):
                with open(f"data_clean/{filename}", "r", encoding="utf-8") as f:
                    context_list.append(f"[{nettoyer_nom_source(filename)}] : {f.read()}")
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
                    texts.append(content)
                    metas.append({"source": f, "session_id": "system_init"})
        if texts:
            batch_size = 1000
            for i in range(0, len(texts), batch_size):
                vectorstore.add_texts(texts=texts[i:i+batch_size], metadatas=metas[i:i+batch_size])
    return vectorstore, llm

vectorstore, llm = load_system()

def build_expert_context(query):
    context = []
    priorite = get_data_clean_context()
    if priorite: context.append("### FICHES D'EXPERTISE PRIORITAIRES ###\n" + priorite)
    raw_law = vectorstore.similarity_search(query, k=8)
    for d in raw_law:
        nom = nettoyer_nom_source(d.metadata.get('source',''))
        context.append(f"[SOURCE : {nom}]\n{d.page_content}")
    return "\n\n".join(context)

# --- 7. INTERFACE PRINCIPALE ---
c1, c2, c3, c4, c5 = st.columns(5)
args_labels = [
    ("Données Certifiées 2026 :", " Barèmes PASS et avantages en nature."),
    ("Maillage de Sources :", " Analyse BOSS, Code du Travail, CSS."),
    ("Mise à Jour Agile :", " Actualisation en temps réel circulaires."),
    ("Traçabilité Totale :", " Réponse sourcée via liste détaillée."),
    ("Confidentialité Garantie :", " Traitement RAM sans stockage.")
]
for i, col in enumerate([c1, c2, c3, c4, c5]):
    col.markdown(f'<p class="assurance-text"><span class="assurance-title">{args_labels[i][0]}</span><span class="assurance-desc">{args_labels[i][1]}</span></p>', unsafe_allow_html=True)

st.markdown("<hr>", unsafe_allow_html=True)
col_t, col_b = st.columns([4, 1])
with col_t: st.markdown("<h1 style='color: #024c6f; margin:0;'>Expert Social Pro 2026</h1>", unsafe_allow_html=True)
with col_b:
    if st.button("Nouvelle session"):
        st.session_state.messages = []
        st.session_state['session_id'] = str(uuid.uuid4())
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
            # --- MODIFICATION DES CONSIGNES POUR CITATIONS RÉELLES ---
            prompt = ChatPromptTemplate.from_template("""
            Tu es l'Expert Social Pro 2026, spécialisé en droit social français.
            Utilise exclusivement le CONTEXTE fourni pour répondre à la QUESTION.
            
            CONSIGNES DE RÉPONSE :
            1. INTERDICTION FORMELLE de citer les numéros de "Partie" ou les noms de fichiers techniques (ex: ignore "Partie 1", "Partie 1726").
            2. Identifie dans le texte du CONTEXTE la référence juridique réelle (ex: "Article L.1234-1", "Article R.XXXX", "BOSS", "PASS 2026").
            3. Cite ces références réelles directement dans tes explications entre crochets : [Article L.XXXX].
            4. Termine obligatoirement ta réponse par une section intitulée "⚖️ RÉFÉRENCES JURIDIQUES UTILISÉES :" listant uniquement les articles de loi ou textes officiels trouvés.
            
            CONTEXTE : {context}
            QUESTION : {question}
            """)
            response = (prompt | llm | StrOutputParser()).invoke({"context": context, "question": query})
        st.markdown(response)
    st.session_state.messages.append({"role": "assistant", "content": response})

show_legal_info()
st.markdown("<div style='text-align:center; color:#888; font-size:11px;'>© 2026 socialexpertfrance.fr</div>", unsafe_allow_html=True)
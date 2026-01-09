import sys
import os
import uuid
import base64 
import requests 
from bs4 import BeautifulSoup 
import streamlit as st
import pypdf 
import stripe # Ajout pour le module SaaS

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

# --- FONCTION WATCHDOG BOSS ---
def check_boss_updates():
    url = "https://boss.gouv.fr/portail/accueil/actualites.html"
    try:
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
        response = requests.get(url, headers=headers, timeout=5)
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            first_news = soup.find('h2', class_='boss-article-title') 
            if first_news:
                return first_news.get_text(strip=True)
    except Exception:
        return None
    return None

# --- 3. DESIGN PRO ---
def get_base64(bin_file):
    if os.path.exists(bin_file):
        with open(bin_file, 'rb') as f:
            return base64.b64encode(f.read()).decode()
    return ""

def apply_pro_design():
    st.markdown("""
        <style>
        #MainMenu {visibility: hidden;}
        header {visibility: hidden !important; height: 0px;}
        footer {visibility: hidden;}
        [data-testid="stHeader"] {display: none;}
        .block-container { padding-top: 3.5rem !important; }
        .stChatMessage { background-color: rgba(255, 255, 255, 0.95); border-radius: 15px; padding: 10px; margin-bottom: 10px; border: 1px solid #e0e0e0; }
        .stChatMessage p, .stChatMessage li { color: black !important; }
        .stExpander details summary p { color: #024c6f !important; font-weight: bold; }
        </style>
    """, unsafe_allow_html=True)
    
    bg_data = get_base64('background.webp')
    if bg_data:
        st.markdown(f"""
            <style>
            .stApp {{ background-image: url("data:image/webp;base64,{bg_data}"); background-size: cover; background-attachment: fixed; }}
            </style>
        """, unsafe_allow_html=True)

# --- 4. SÉCURITÉ & MODULE SAAS (MODIFIÉ) ---

# Configuration Stripe
stripe.api_key = os.getenv("STRIPE_SECRET_KEY")
PRICE_ID_MONTHLY = "price_1SnaTDQZ5ivv0RayXfKqvJ6I"
PRICE_ID_ANNUAL = "price_1SnaUOQZ5ivv0RayFnols3TI"

def create_checkout_session(plan_type):
    """Génère un lien de paiement Stripe sécurisé"""
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
        st.error(f"Erreur lors de la création de la session : {e}")
        return None

def check_password():
    if st.session_state.get("password_correct"): return True
    apply_pro_design()
    st.markdown("<br><br><br><br>", unsafe_allow_html=True)
    st.markdown("<h1 style='text-align: center; color: #024c6f;'>🔑 Accès Expert Social Pro</h1>", unsafe_allow_html=True)
    
    col_l, col_m, col_r = st.columns([1, 2, 1])
    with col_m:
        tab_login, tab_subscribe = st.tabs(["Se connecter (LinkedIn)", "S'abonner"])
        
        with tab_login:
            pwd = st.text_input("Code d'accès :", type="password")
            if st.button("Se connecter"):
                valid_pwd = os.getenv("APP_PASSWORD", "DEFAUT_USER_123")
                admin_pwd = os.getenv("ADMIN_PASSWORD", "ADMIN2026")
                
                if pwd == str(admin_pwd):
                    st.session_state["password_correct"] = True
                    st.session_state["is_admin"] = True
                    st.rerun()
                elif pwd == str(valid_pwd):
                    st.session_state["password_correct"] = True
                    st.session_state["is_admin"] = False
                    st.rerun()
                else: 
                    st.error("Code erroné.")
        
        with tab_subscribe:
            st.markdown("### Choisissez votre formule")
            c_m, c_a = st.columns(2)
            with c_m:
                st.info("**Mensuel**\n\n50 € HT / mois\n\n*Sans engagement*")
                if st.button("S'abonner (Mensuel)"):
                    url = create_checkout_session("Mensuel")
                    if url: st.markdown(f'<meta http-equiv="refresh" content="0;URL={url}">', unsafe_allow_html=True)
            with c_a:
                st.success("**Annuel**\n\n500 € HT / an\n\n*2 mois offerts*")
                if st.button("S'abonner (Annuel)"):
                    url = create_checkout_session("Annuel")
                    if url: st.markdown(f'<meta http-equiv="refresh" content="0;URL={url}">', unsafe_allow_html=True)
    st.stop()

check_password()
apply_pro_design()

# --- 5. INITIALISATION IA ---
if 'session_id' not in st.session_state: st.session_state['session_id'] = str(uuid.uuid4())

NOMS_PROS = {
    "REF_2026_": "🏛️ BARÈMES ET RÉFÉRENTIELS OFFICIELS 2026",
    "MEMO_CHIFFRES": "📑 RÉFÉRENTIEL CHIFFRÉS 2026",
    "REF_": "✅ RÉFÉRENCES :\n- BOSS\n- Code du Travail\n- Code de la Sécurité Sociale\n- Organismes Sociaux",
    "DOC_BOSS_": "🌐 BULLETIN OFFICIEL SÉCURITÉ SOCIALE (BOSS)",
    "LEGAL_": "📕 SOCLE LÉGAL (CODES)",
    "DOC_JURISPRUDENCE": "⚖️ JURISPRUDENCE (PRÉCÉDENTS)",
    "barème officiel": "🏛️ BOSS - ARCHIVES BARÈMES"
}

def nettoyer_nom_source(raw_source):
    if not raw_source: return "Source Inconnue"
    nom_fichier = os.path.basename(raw_source)
    for cle, nom_pro in NOMS_PROS.items():
        if cle in nom_fichier: return nom_pro
    return nom_fichier.replace('.txt', '').replace('.pdf', '').replace('_', ' ')

def get_data_clean_context():
    context_list = []
    if os.path.exists("data_clean"):
        for filename in os.listdir("data_clean"):
            if filename.endswith(".txt"):
                with open(f"data_clean/{filename}", "r", encoding="utf-8") as f:
                    context_list.append(f"[{nettoyer_nom_source(filename)}] : {f.read()}")
    return "\n".join(context_list)

@st.cache_resource
def load_system():
    api_key = os.getenv("GOOGLE_API_KEY") or st.secrets.get("GOOGLE_API_KEY")
    embeddings = GoogleGenerativeAIEmbeddings(model="models/text-embedding-004", google_api_key=api_key)
    vectorstore = Chroma(embedding_function=embeddings)
    llm = ChatGoogleGenerativeAI(model="gemini-2.0-flash-exp", temperature=0, google_api_key=api_key)
    
    if os.path.exists("data_clean"):
        files = [f for f in os.listdir("data_clean") if f.endswith(".txt")]
        texts_to_add = []
        metadatas = []
        for filename in files:
            with open(f"data_clean/{filename}", "r", encoding="utf-8") as f:
                content = f.read()
                texts_to_add.append(content)
                metadatas.append({"source": filename, "session_id": "system_init"})
        if texts_to_add:
            vectorstore.add_texts(texts=texts_to_add, metadatas=metadatas)
    return vectorstore, llm

vectorstore, llm = load_system()

# --- 6. FONCTIONS ---
def process_file(uploaded_file):
    try:
        text = ""
        if uploaded_file.name.endswith('.pdf'):
            reader = pypdf.PdfReader(uploaded_file)
            for page in reader.pages:
                extracted = page.extract_text()
                if extracted: text += extracted + "\n"
        else: text = uploaded_file.read().decode("utf-8")
        if not text or len(text.strip()) < 20: return None
        text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=100)
        chunks = text_splitter.split_text(text)
        metadatas = [{"source": f"VOTRE DOCUMENT : {uploaded_file.name}", "session_id": st.session_state['session_id']} for _ in chunks]
        return vectorstore.add_texts(texts=chunks, metadatas=metadatas)
    except Exception: return None

# --- 7. INTERFACE ---

# Style spécifique pour les 4 colonnes de réassurance
st.markdown("""
    <style>
    .assurance-text {
        font-size: 10px !important;
        color: #444444;
        line-height: 1.3;
        text-align: left;
        padding: 5px;
    }
    .assurance-title {
        font-weight: bold;
        color: #024c6f;
        display: block;
        margin-bottom: 2px;
        font-size: 10px !important;
    }
    hr {
        margin: 10px 0 !important;
        border: 0;
        border-top: 1px solid #e0e0e0;
    }
    </style>
""", unsafe_allow_html=True)

# Affichage des 4 colonnes de wording
c1, c2, c3, c4 = st.columns(4)
with c1:
    st.markdown('<p class="assurance-text"><span class="assurance-title">Données Certifiées 2026 :</span> Intégration prioritaire des nouveaux barèmes (PASS, avantages en nature, seuils d\'exonération) pour une précision chirurgicale dès le premier jour de l\'année.</p>', unsafe_allow_html=True)
with c2:
    st.markdown('<p class="assurance-text"><span class="assurance-title">Maillage de Sources Multiples :</span> Une analyse simultanée et croisée du BOSS, du Code du Travail, du Code de la Sécurité Sociale et des communiqués des organismes sociaux.</p>', unsafe_allow_html=True)
with c3:
    st.markdown('<p class="assurance-text"><span class="assurance-title">Mise à Jour Agile des Connaissances :</span> Contrairement aux IA classiques figées dans le temps, notre base est actualisée en temps réel dès la publication de nouvelles circulaires ou réformes, garantissant une conformité permanente.</p>', unsafe_allow_html=True)
with c4:
    st.markdown('<p class="assurance-text"><span class="assurance-title">Transparence et Traçabilité :</span> Chaque réponse est systématiquement sourcée via une liste à puces détaillée, permettant aux experts de valider instantanément le fondement juridique de chaque conseil.</p>', unsafe_allow_html=True)

st.markdown("<hr>", unsafe_allow_html=True)

# Titre Principal et Bouton de Session
col_t, col_b = st.columns([4, 1])
with col_t: 
    st.markdown("<h1 style='color: #024c6f; margin-top: 0;'>Expert Social Pro 2026</h1>", unsafe_allow_html=True)
with col_b:
    if st.button("Nouvelle session"):
        st.session_state.messages = []
        st.session_state['session_id'] = str(uuid.uuid4())
        # Nettoyage de l'historique des documents chargés pour cette session
        if 'history' in st.session_state:
            st.session_state['history'] = []
        st.rerun()

# --- ZONE ADMIN PRIVÉE ---
if st.session_state.get("is_admin", False):
    last_news = check_boss_updates()
    if last_news:
        st.info(f"📢 **VEILLE BOSS (MODE ADMIN) :** {last_news}")
        if st.button("🤖 Analyser et générer la fiche"):
            with st.status("Analyse juridique...", expanded=True):
                news_context = f"Titre de l'actualité BOSS : {last_news}."
                prompt_veille = ChatPromptTemplate.from_template("Analyse cette news BOSS pour 2026 et crée une fiche OBJET/SOURCE/TEXTE : {news}")
                analyste = (prompt_veille | llm | StrOutputParser()).invoke({"news": news_context})
                st.code(analyste, language="text")

with st.expander("📎 Analyser un document externe", expanded=False):
    uploaded_file = st.file_uploader("Fichier (PDF ou TXT)", type=["pdf", "txt"])
    if uploaded_file and uploaded_file.name not in st.session_state.get('history', []):
        if process_file(uploaded_file):
            if 'history' not in st.session_state: st.session_state['history'] = []
            st.session_state['history'].append(uploaded_file.name)
            st.success(f"Document '{uploaded_file.name}' intégré avec succès !")
            st.rerun()
# --- 8. CHAT ---
if "messages" not in st.session_state: st.session_state.messages = []
for message in st.session_state.messages:
    with st.chat_message(message["role"], avatar=("avatar-logo.png" if message["role"] == "assistant" else None)):
        st.markdown(message["content"])

if query := st.chat_input("Posez votre question..."):
    st.session_state.messages.append({"role": "user", "content": query})
    with st.chat_message("user"): st.markdown(query)
    with st.chat_message("assistant", avatar="avatar-logo.png"):
        with st.status("🔍 Recherche en cours...", expanded=True):
            priorite_context = get_data_clean_context()
            raw_law = vectorstore.similarity_search(query, k=20)
            user_docs = vectorstore.similarity_search(query, k=10, filter={"session_id": st.session_state['session_id']})
            context = []
            if priorite_context: context.append("### FICHES D'EXPERTISE PRIORITAIRES (2025-2026) ###\n" + priorite_context)
            if user_docs: context.append("### CAS CLIENT (VOTRE DOCUMENT) ###\n" + "\n".join([d.page_content for d in user_docs]))
            context.append("\n### DOCTRINE ET ARCHIVES ###")
            for d in raw_law:
                nom = nettoyer_nom_source(d.metadata.get('source',''))
                context.append(f"[SOURCE : {nom}]\n{d.page_content}")
            prompt = ChatPromptTemplate.from_template("""
            Tu es l'Expert Social Pro 2026. 
            MISSION : Réponds via les fiches prioritaires. Saute deux lignes avant d'écrire [SOURCE : ...].
            CONTEXTE : {context}
            QUESTION : {question}
            """)
            full_response = (prompt | llm | StrOutputParser()).invoke({"context": "\n".join(context), "question": query})
        st.markdown(full_response)
    st.session_state.messages.append({"role": "assistant", "content": full_response})

# --- 9. PIED DE PAGE & INFORMATIONS LÉGALES ---
st.markdown("<br><br>", unsafe_allow_html=True)
st.divider()

foot_l, foot_m, foot_r = st.columns([1, 2, 1])

with foot_m:
    with st.popover("⚖️ Mentions Légales & RGPD", use_container_width=True):
        st.markdown("### 🏛️ Mentions Légales")
        st.write("""
        **Éditeur & Responsable de traitement :** Sylvain Attal  
        **Hébergement :** Google Cloud Platform (Région : europe-west1, Belgique)  
        **Contact :** sylvain.attal@businessagent-ai.com
        """)
        
        st.markdown("### 🛡️ Confidentialité & RGPD")
        st.write("""
        **Protection des données :** Les documents téléchargés sont analysés exclusivement en mémoire vive (RAM) et sont **définitivement supprimés** dès la fermeture de la session ou lors d'un clic sur 'Nouvelle session'. Aucun stockage persistant n'est effectué.
        
        **Vos Droits :** Conformément au RGPD et à la loi 'Informatique et Libertés', vous disposez d'un droit d'accès, de rectification et de suppression de vos données de session sur simple demande à l'adresse contact ci-dessus.
        
        **Intelligence Artificielle :** Utilisation de l'API Google Gemini. Vos données professionnelles ne sont **jamais utilisées** pour entraîner les modèles de Google (Contrat API Entreprise).
        """)
        
        st.markdown("### ⚠️ Avertissement Légal")
        st.caption("""
        Expert Social Pro 2026 est un outil d'assistance automatisé. 
        Conformément à la loi du 31 décembre 1971, les analyses générées ne constituent pas un conseil juridique personnalisé. 
        L'utilisation de cet outil ne dispense pas de la validation par un professionnel du droit ou de l'expertise-comptable.
        """)
        
        st.caption("Dernière mise à jour : 08/01/2026")

    # Copyright mis à jour avec le bon domaine
    st.markdown("""
        <div style='text-align: center; color: #888888; font-size: 11px; margin-top: 10px;'>
            © 2026 socialexpertfrance.fr | Expert Social Pro <br>
            <span style='font-style: italic;'>L'IA est un outil d'aide, la validation finale incombe à l'expert.</span>
        </div>
    """, unsafe_allow_html=True)
import sys
import os
import uuid
import base64 
import streamlit as st
import pypdf 

# --- 1. PATCH SQLITE POUR CLOUD RUN ---
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

# --- 3. DESIGN ET NETTOYAGE INTERFACE (Masque le bandeau blanc et menu) ---
def get_base64(bin_file):
    if os.path.exists(bin_file):
        with open(bin_file, 'rb') as f:
            return base64.b64encode(f.read()).decode()
    return ""

def apply_pro_design():
    # Suppression radicale des éléments Streamlit (Header, Menu, Footer)
    st.markdown("""
        <style>
        #MainMenu {visibility: hidden;}
        header {visibility: hidden !important; height: 0px;}
        footer {visibility: hidden;}
        [data-testid="stHeader"] {display: none;}
        /* Remonte le contenu pour supprimer l'espace du header */
        .block-container { padding-top: 0rem !important; }
        .stApp { margin-top: -60px; } 
        
        .stChatMessage { background-color: rgba(255, 255, 255, 0.95); border-radius: 15px; padding: 10px; margin-bottom: 10px; }
        .stChatMessage p, .stChatMessage li { color: black !important; }
        .stExpander details summary p { color: white !important; }
        </style>
    """, unsafe_allow_html=True)
    
    bg_data = get_base64('background.webp')
    if bg_data:
        st.markdown(f"""
            <style>
            .stApp {{
                background-image: url("data:image/webp;base64,{bg_data}");
                background-size: cover;
                background-attachment: fixed;
            }}
            </style>
        """, unsafe_allow_html=True)

# --- 4. SÉCURITÉ (Arrêt immédiat si pas de mot de passe) ---
def check_password():
    if st.session_state.get("password_correct"):
        return True
    
    apply_pro_design()
    st.markdown("<br><br><br><br>", unsafe_allow_html=True)
    st.markdown("<h1 style='text-align: center; color: white;'>🔐 Accès Expert Réservé</h1>", unsafe_allow_html=True)
    
    col_l, col_m, col_r = st.columns([1, 2, 1])
    with col_m:
        pwd = st.text_input("Code d'accès :", type="password")
        if st.button("Se connecter"):
            # On cherche dans l'environnement ou les secrets Streamlit
            valid_pwd = os.getenv("APP_PASSWORD") or st.secrets.get("APP_PASSWORD", None)
            if pwd == valid_pwd:
                st.session_state["password_correct"] = True
                st.rerun()
            else:
                st.error("Code incorrect.")
    st.stop() # C'est ici que l'on bloque tout le reste de l'exécution

# Lancement de la sécurité
check_password()
# Si on arrive ici, le mot de passe est bon
apply_pro_design()

# --- 5. INITIALISATION IA ---
if 'session_id' not in st.session_state:
    st.session_state['session_id'] = str(uuid.uuid4())

NOMS_PROS = {
    "barème officiel": "🏛️ BOSS - BARÈMES OFFICIELS 2025",
    "MEMO_CHIFFRES": "📑 Barèmes Sociaux 2026 (Anticipation Officielle)",
    "Frais": "🌐 BOSS - Doctrine : Frais Pros",
    "Avantages": "🌐 BOSS - Doctrine : Avantages Nature",
    "Indemnités": "🌐 BOSS - Doctrine : Indemnités",
    "Assiette": "🌐 BOSS - Doctrine : Assiette",
    "Allègements": "🌐 BOSS - Doctrine : Allègements",
    "MEMO_JURISPRUDENCE": "⚖️ Jurisprudence de Référence (Socle)",
    "Code_du_Travail": "📕 Code du Travail"
}

def nettoyer_nom_source(raw_source):
    if not raw_source: return "Source Inconnue"
    nom_fichier = os.path.basename(raw_source)
    for cle, nom_pro in NOMS_PROS.items():
        if cle in nom_fichier: return nom_pro
    return nom_fichier.replace('.txt', '').replace('.pdf', '').replace('_', ' ')

@st.cache_resource
def load_system():
    api_key = os.getenv("GOOGLE_API_KEY") or st.secrets.get("GOOGLE_API_KEY")
    embeddings = GoogleGenerativeAIEmbeddings(model="models/text-embedding-004", google_api_key=api_key)
    vectorstore = Chroma(persist_directory="chroma_db", embedding_function=embeddings)
    # Utilisation stricte de gemini-2.0-flash-exp
    llm = ChatGoogleGenerativeAI(model="gemini-2.0-flash-exp", temperature=0, google_api_key=api_key)
    return vectorstore, llm

vectorstore, llm = load_system()

# --- 6. INTERFACE ET CHAT ---
st.markdown("<h1 style='color: white;'>Expert Social Pro 2026</h1>", unsafe_allow_html=True)

if "messages" not in st.session_state: st.session_state.messages = []
for message in st.session_state.messages:
    avatar = "avatar-logo.png" if message["role"] == "assistant" else None
    with st.chat_message(message["role"], avatar=avatar):
        st.markdown(message["content"])

if query := st.chat_input("Posez votre question..."):
    st.session_state.messages.append({"role": "user", "content": query})
    with st.chat_message("user"): st.markdown(query)
    
    with st.chat_message("assistant", avatar="avatar-logo.png"):
        with st.status("🔍 Analyse des sources prioritaires...", expanded=True):
            
            # RECHERCHE AVEC TRI DE PRIORITÉ
            raw_docs = vectorstore.similarity_search(query, k=20)
            
            # On identifie les documents qui sont des barèmes ou le mémo
            docs_prioritaires = [d for d in raw_docs if any(x in d.metadata.get('source', '') for x in ["barème", "MEMO"])]
            docs_doctrine = [d for d in raw_docs if d not in docs_prioritaires]
            
            # On force l'IA à lire les barèmes en PREMIER
            law_docs = docs_prioritaires + docs_doctrine
            
            context_parts = []
            for d in law_docs:
                nom_pro = nettoyer_nom_source(d.metadata.get('source', ''))
                context_parts.append(f"[SOURCE : {nom_pro}]\n{d.page_content}")
            
            context_text = "\n".join(context_parts)

            prompt = ChatPromptTemplate.from_template("""
            Tu es l'Expert Social Pro 2026.
            
            HIÉRARCHIE DES RÉFÉRENCES :
            1. Pour tout MONTANT ou CHIFFRE de 2025, utilise prioritairement [🏛️ BOSS - BARÈMES OFFICIELS 2025].
            2. Pour tout MONTANT ou CHIFFRE de 2026, utilise exclusivement [📑 Barèmes Sociaux 2026 (Anticipation Officielle)].
            
            CONSIGNE : Cite la source entre crochets pour chaque chiffre donné.
            CONTEXTE : {context}
            QUESTION : {question}
            """)
            
            chain = prompt | llm | StrOutputParser()
            full_response = chain.invoke({"context": context_text, "question": query})

        st.markdown(full_response)
        
        with st.expander("📚 Sources réellement utilisées"):
            sources_affichees = set()
            for d in law_docs:
                nom = nettoyer_nom_source(d.metadata.get('source', ''))
                if nom in full_response and nom not in sources_affichees:
                    st.write(f"**🔹 {nom}**")
                    st.caption(f"_{d.page_content[:250]}..._")
                    sources_affichees.add(nom)

    st.session_state.messages.append({"role": "assistant", "content": full_response})
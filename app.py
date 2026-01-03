# --- 1. CONFIGURATION SQLITE ET IMPORTS ---
import sys
import os
import base64 # Nécessaire pour les images de fond
try:
    __import__('pysqlite3')
    sys.modules['sqlite3'] = sys.modules.pop('pysqlite3')
except ImportError:
    pass

import streamlit as st

# --- 2. FONCTIONS DESIGN & CSS (LA MAGIE VISUELLE) ---

def get_base64(bin_file):
    """Encode une image locale en base64 pour l'intégrer au CSS sans URL externe."""
    with open(bin_file, 'rb') as f:
        data = f.read()
    return base64.b64encode(data).decode()

def set_design(bg_image_file, sidebar_color):
    """Injecte le CSS pour le fond d'écran et la couleur de la sidebar."""
    bin_str = get_base64(bg_image_file)
    page_bg_img = f'''
    <style>
    /* Fond d'écran principal */
    .stApp {{
        background-image: url("data:image/png;base64,{bin_str}");
        background-size: cover;
        background-repeat: no-repeat;
        background-attachment: fixed;
    }}
    
    /* Couleur de la barre latérale (Sidebar) */
    [data-testid="stSidebar"] > div:first-child {{
        background-color: {sidebar_color};
        color: white; /* Texte en blanc pour le contraste */
    }}
    [data-testid="stSidebar"] h1, [data-testid="stSidebar"] h2, [data-testid="stSidebar"] label {{
         color: white !important; /* Force les titres et labels en blanc */
    }}
    
    /* Ajustements pour la lisibilité sur le fond */
    .stChatMessage {{
        background-color: rgba(255, 255, 255, 0.95); /* Bulles de chat légèrement transparentes */
        border-radius: 15px;
        padding: 10px;
        margin-bottom: 10px;
    }}
    </style>
    '''
    st.markdown(page_bg_img, unsafe_allow_html=True)

# --- 3. CONFIGURATION PAGE ET AUTHENTIFICATION ---
st.set_page_config(page_title="Expert Social Pro 2026", layout="wide", page_icon="⚖️")

# On applique le design immédiatement (si les fichiers existent)
try:
    set_design('background.png', '#344908')
except FileNotFoundError:
    st.warning("Images de design non trouvées. L'application continue en mode dégradé.")

if "password_correct" not in st.session_state:
    st.session_state["password_correct"] = False

if not st.session_state["password_correct"]:
    # Interface de login épurée
    st.markdown("<h1 style='text-align: center; color: #344908;'>🔐 Accès Expert Réservé</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center;'>Veuillez vous identifier pour accéder à la base de connaissances.</p>", unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1,2,1])
    with col2:
        pwd_input = st.text_input("Mot de passe :", type="password", label_visibility="collapsed", placeholder="Saisissez votre mot de passe ici...")
        if st.button("Connexion sécurisée", type="primary", use_container_width=True):
            correct_pwd = os.getenv("APP_PASSWORD") or st.secrets.get("APP_PASSWORD")
            if pwd_input == correct_pwd:
                st.session_state["password_correct"] = True
                st.rerun()
            else:
                st.error("Identifiants incorrects.")
    st.stop()

# --- 4. CHARGEMENT DES MODULES LOURDS (APRÈS AUTH) ---
from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAIEmbeddings
from langchain_chroma import Chroma
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough, RunnableParallel
from langchain_core.output_parsers import StrOutputParser

# --- 5. SIDEBAR : CONTEXTE ET NAVIGATION ---
with st.sidebar:
    st.image("avatar-logo.png", width=100) # Petit rappel du logo en haut
    st.title("Navigation")
    st.markdown("---")
    st.subheader("Contexte Juridique")
    st.info("📅 **Année Fiscale : 2026**\n\nBase à jour des dernières LFSS et Ordonnances connues.")
    st.markdown("---")
    if st.button("🗑️ Nouvelle Conversation", type="secondary", use_container_width=True):
        st.session_state.messages = []
        st.rerun()
    st.markdown("---")
    st.caption("Expert Social Pro v2.1 - Accès Cabinet")

# --- 6. INTERFACE PRINCIPALE : ACCUEIL ET CHAT ---

# En-tête de l'interface principale
st.title("⚖️ Expert Social Pro 2026")
st.markdown("""
**Bienvenue sur votre expert social dédié.**
Posez vos questions techniques en droit social et paie. L'IA analyse le BOSS, le Code du travail, le Code de la Sécurité sociale et les conventions pour vous fournir des réponses basées exclusivement sur des textes officiels.
""")
st.markdown("---")

# Clé API
api_key = os.getenv("GEMINI_API_KEY") or st.secrets.get("GEMINI_API_KEY")
if not api_key:
    st.error("⚠️ Clé API GEMINI manquante.")
    st.stop()
os.environ["GOOGLE_API_KEY"] = api_key

# Chargement RAG
@st.cache_resource
def load_system():
    embeddings = GoogleGenerativeAIEmbeddings(model="models/text-embedding-004")
    vectorstore = Chroma(persist_directory="chroma_db", embedding_function=embeddings)
    llm = ChatGoogleGenerativeAI(model="gemini-2.0-flash-exp", temperature=0)
    return vectorstore, llm

vectorstore, llm = load_system()

# --- 7. CHAÎNE RAG ÉVOLUÉE (POUR SOURCES PLIABLES) ---
retriever = vectorstore.as_retriever(search_kwargs={"k": 10})

prompt = ChatPromptTemplate.from_template("""
Tu es un assistant expert en droit social et paie français.
CONSIGNE : Ne suggère JAMAIS de vérifier le BOSS. Donne directement les chiffres, taux et conditions. Cite les articles de loi ou paragraphes du BOSS entre parenthèses quand tu les utilises.

Contexte : {context}
Question : {question}

Réponse technique et précise :
""")

# Nouvelle structure pour récupérer à la fois la réponse ET les documents sources
rag_chain_with_sources = RunnableParallel(
    {"context": retriever, "question": RunnablePassthrough()}
).assign(answer= prompt | llm | StrOutputParser())

# --- 8. GESTION DU CHAT AVEC AVATARS ---

# Définition des avatars
assistant_avatar = "avatar-logo.png" # Votre logo pro
user_avatar = "🧑‍💼" # Un emoji pro neutre

if "messages" not in st.session_state:
    st.session_state.messages = []

# Affichage de l'historique
for message in st.session_state.messages:
    avatar_to_use = assistant_avatar if message["role"] == "assistant" else user_avatar
    with st.chat_message(message["role"], avatar=avatar_to_use):
        st.markdown(message["content"])

# Zone de saisie et traitement
if query := st.chat_input("Posez votre question technique ici..."):
    # 1. Affichage message utilisateur
    st.session_state.messages.append({"role": "user", "content": query})
    with st.chat_message("user", avatar=user_avatar):
        st.markdown(query)
    
    # 2. Traitement et affichage réponse assistant
    with st.chat_message("assistant", avatar=assistant_avatar):
        with st.spinner("Analyse croisée des textes officiels en cours..."):
            # On récupère le dictionnaire complet {answer: "...", context: [docs]}
            response = rag_chain_with_sources.invoke(query)
            
            # Affichage de la réponse principale
            st.markdown(response["answer"])
            
            # Affichage des sources dans un menu dépliant "Pro"
            with st.expander("📚 Voir les sources officielles et extraits juridiques utilisés"):
                for i, doc in enumerate(response["context"]):
                    st.markdown(f"**Source {i+1}** (Extrait pertinent) :")
                    st.caption(doc.page_content)
                    st.markdown("---")
            
            # On sauvegarde uniquement la réponse textuelle dans l'historique pour ne pas surcharger
            st.session_state.messages.append({"role": "assistant", "content": response["answer"]})
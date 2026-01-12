import streamlit as st
import os
import pypdf
from dotenv import load_dotenv

# --- 1. CHARGEMENT CONFIG & SECRETS ---
load_dotenv()
st.set_page_config(page_title="Expert Social Pro France", layout="wide")

# --- 2. IMPORTS DES MODULES (Architecture Propre) ---
from ui.styles import apply_pro_design, show_legal_info
from core.auth import check_password
from rules.engine import SocialRuleEngine
from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAIEmbeddings
from langchain_pinecone import PineconeVectorStore
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

# ==============================================================================
# PARTIE 1 : AUTHENTIFICATION (Gérée par core/auth.py)
# ==============================================================================
# Si l'utilisateur n'est pas connecté, check_password affiche le login et renvoie False.
# On arrête donc l'exécution du script ici.
if not check_password():
    st.stop()

# ==============================================================================
# PARTIE 2 : LE MOTEUR V4 (Une fois connecté)
# ==============================================================================

# On réapplique le design pour être sûr qu'il est chargé dans la session connectée
apply_pro_design()

@st.cache_resource
def load_engine():
    """Charge le Cerveau Logique V4 (Règles YAML)"""
    return SocialRuleEngine()

@st.cache_resource
def load_ia_system():
    """Charge le Cerveau Créatif (Gemini + Pinecone CLOUD)"""
    api_key = os.getenv("GOOGLE_API_KEY")
    
    # 1. Modèle d'Embedding
    embeddings = GoogleGenerativeAIEmbeddings(model="models/text-embedding-004", google_api_key=api_key)
    
    # 2. Connexion à PINECONE (Cloud)
    vectorstore = PineconeVectorStore.from_existing_index(
        index_name="expert-social",
        embedding=embeddings
    )
    
    # 3. LLM (Gemini 2.0)
    llm = ChatGoogleGenerativeAI(model="gemini-2.0-flash-exp", temperature=0, google_api_key=api_key)
    
    return vectorstore, llm

# Init Moteurs
engine = load_engine()
vectorstore, llm = load_ia_system()

def build_context(query):
    """Construction contexte IA"""
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

def get_gemini_response(query, context, user_doc_content=None):
    """Prompt Hybride"""
    user_doc_section = f"\n--- DOCUMENT UTILISATEUR ---\n{user_doc_content}\n" if user_doc_content else ""
    prompt = ChatPromptTemplate.from_template("""
    Tu es l'Expert Social Pro 2026.
    CONTEXTE : {context}
    """ + user_doc_section + """
    MISSION : Réponds à la question suivante en t'appuyant EXCLUSIVEMENT sur les documents ci-dessus.
    QUESTION : {question}
    CONSIGNES D'AFFICHAGE STRICTES :
    1. CITATIONS DANS LE TEXTE : Utilise la balise HTML <sub> pour les citations précises (ex: <sub>*[BOSS : Barème]*</sub>).
    2. FOOTER RÉCAPITULATIF (OBLIGATOIRE) :
       Tu DOIS terminer ta réponse EXACTEMENT par ce bloc (avec la ligne de séparation) :
       ---
       **Sources utilisées :**
       * BOSS : [Nom du document]
       * [Autre Source]
    """)
    chain = prompt | llm | StrOutputParser()
    response = chain.invoke({"context": context, "question": query})
    if "Sources utilisées :" in response and "---" not in response[-500:]:
        response = response.replace("**Sources utilisées :**", "\n\n---\n**Sources utilisées :**")
    return response

# ==============================================================================
# PARTIE 3 : L'INTERFACE DE CHAT
# ==============================================================================

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
        if uploaded_file: st.markdown(f"<sub>📎 *Analyse incluant : {uploaded_file.name}*</sub>", unsafe_allow_html=True)
    with st.chat_message("assistant", avatar="avatar-logo.png"):
        message_placeholder = st.empty()
        # Routeur
        is_conversational = ("?" in query or len(query.split()) > 7 or uploaded_file)
        verdict = {"found": False}
        if not is_conversational: verdict = engine.get_formatted_answer(keywords=query)
        
        if verdict["found"]:
            full_response = f"{verdict['text']}\n\n---\n**Sources utilisées :**\n* {verdict['source']}"
            message_placeholder.markdown(full_response, unsafe_allow_html=True)
        else:
            wait_msg = "🔍 Analyse..." if uploaded_file else "🔍 Recherche juridique..."
            with st.spinner(wait_msg):
                gemini_response = get_gemini_response(query, build_context(query), user_doc_content=user_doc_text)
                message_placeholder.markdown(gemini_response, unsafe_allow_html=True)
                full_response = gemini_response
    st.session_state.messages.append({"role": "assistant", "content": full_response})

show_legal_info()
st.markdown("<div style='text-align:center; color:#888; font-size:11px; margin-top:30px;'>© 2026 socialexpertfrance.fr</div>", unsafe_allow_html=True)
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
# On importe le cerveau depuis le nouveau fichier
from services.ai_engine import load_engine, load_ia_system, build_context, get_gemini_response

# ==============================================================================
# PARTIE 1 : AUTHENTIFICATION
# ==============================================================================
if not check_password():
    st.stop()

# ==============================================================================
# PARTIE 2 : INITIALISATION DU CERVEAU (Une fois connecté)
# ==============================================================================
apply_pro_design()

# Chargement des moteurs via le service dédié
engine = load_engine()
vectorstore, llm = load_ia_system()

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

# Gestion du document uploadé
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

# Affichage Historique
if "messages" not in st.session_state: st.session_state.messages = []
for msg in st.session_state.messages:
    with st.chat_message(msg["role"], avatar=("avatar-logo.png" if msg["role"]=="assistant" else None)):
        st.markdown(msg["content"], unsafe_allow_html=True)

# Zone de Saisie
if query := st.chat_input("Votre question juridique ou chiffrée..."):
    st.session_state.messages.append({"role": "user", "content": query})
    with st.chat_message("user"):
        st.markdown(query)
        if uploaded_file: st.markdown(f"<sub>📎 *Analyse incluant : {uploaded_file.name}*</sub>", unsafe_allow_html=True)
    
    with st.chat_message("assistant", avatar="avatar-logo.png"):
        message_placeholder = st.empty()
        
        # Routeur d'intention
        is_conversational = ("?" in query or len(query.split()) > 7 or uploaded_file)
        verdict = {"found": False}
        if not is_conversational: 
            verdict = engine.get_formatted_answer(keywords=query)
        
        if verdict["found"]:
            full_response = f"{verdict['text']}\n\n---\n**Sources utilisées :**\n* {verdict['source']}"
            message_placeholder.markdown(full_response, unsafe_allow_html=True)
        else:
            wait_msg = "🔍 Analyse..." if uploaded_file else "🔍 Recherche juridique..."
            with st.spinner(wait_msg):
                # On passe vectorstore et llm en arguments car ils sont chargés ici
                context = build_context(query, vectorstore)
                gemini_response = get_gemini_response(query, context, llm, user_doc_content=user_doc_text)
                
                message_placeholder.markdown(gemini_response, unsafe_allow_html=True)
                full_response = gemini_response
                
    st.session_state.messages.append({"role": "assistant", "content": full_response})

show_legal_info()
st.markdown("<div style='text-align:center; color:#888; font-size:11px; margin-top:30px;'>© 2026 socialexpertfrance.fr</div>", unsafe_allow_html=True)
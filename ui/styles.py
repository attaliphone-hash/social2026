import streamlit as st
import os
import base64

def get_base64(bin_file):
    if os.path.exists(bin_file):
        return base64.b64encode(open(bin_file, "rb").read()).decode()
    return ""

def apply_pro_design():
    st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Open+Sans:wght@400;600&display=swap');

#MainMenu, header, footer {visibility: hidden;}
[data-testid="stHeader"] {display: none;}
.block-container { padding-top: 1rem !important; padding-bottom: 5rem !important;}

/* TITRES */
h1 {
    font-family: 'Baskerville', 'Georgia', serif !important;
    color: #253E92 !important;
    font-weight: 700 !important;
}

/* BOUTON UPLOAD */
.fake-upload-btn {
    font-family: 'Open Sans', sans-serif;
    font-size: 12px;
    height: 40px;
    background-color: white;
    border: 1px solid #ccc;
    border-radius: 4px;
    color: #333;
    display: flex;
    align-items: center;
    justify-content: center;
}
[data-testid="stFileUploader"] {
    margin-top: -42px !important;
    opacity: 0 !important;
    z-index: 99 !important;
    height: 40px !important;
}

/* --- TWEAKS CHAT MESSAGES (NOUVEAU) --- */

/* 1. La Bulle globale */
.stChatMessage { 
    background-color: rgba(255,255,255,0.95); 
    border-radius: 12px; 
    border: 1px solid #f0f0f0; 
    box-shadow: 0 2px 5px rgba(0,0,0,0.02);
}

/* 2. Le Contenu Texte (Padding & Aération) */
[data-testid="stChatMessageContent"] {
    padding-top: 1rem !important;    /* Espace en haut */
    padding-bottom: 1rem !important; /* Espace en bas */
    padding-right: 2.5rem !important;/* GROS espace à droite (demande utilisateur) */
    padding-left: 1.5rem !important; /* Espace à gauche (vs Avatar) */
}

/* 3. Correction Avatar vs Titre (Alignement) */
/* On remonte le premier titre H3 pour qu'il s'aligne avec les yeux de l'avatar */
[data-testid="stChatMessageContent"] h3:first-of-type {
    margin-top: -5px !important; 
    padding-top: 0 !important;
}

/* Input Zone */
div[data-testid="stChatInput"] button {
    color: #eda146 !important;
}
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
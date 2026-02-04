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
/* 🚫 PLUS D'IMPORTS GOOGLE FONTS (Performance & GDPR) */

/* 1. CONFIGURATION GÉNÉRALE STREAMLIT */
#MainMenu, header, footer {visibility: hidden;}
[data-testid="stHeader"] {display: none;}
.block-container { padding-top: 1rem !important; padding-bottom: 5rem !important;}

/* 2. TYPOGRAPHIE SYSTÈME (NATIVE) */
/* Corps de texte : Polices natives ultra-lisibles (SF Pro sur Mac, Segoe sur Windows) */
html, body, [class*="css"] {
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif !important;
}

/* Titres : Style "Juridique / Prestigieux" (Georgia est installée partout) */
h1, h2, h3 {
    font-family: Georgia, 'Times New Roman', Times, serif !important;
    color: #253E92 !important;
    font-weight: 700 !important;
}

/* 3. BOUTON UPLOAD PERSONNALISÉ */
.fake-upload-btn {
    font-family: inherit !important; /* On hérite de la police système */
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

/* 4. MESSAGES DE CHAT (DESIGN "NOTION") */

/* La Bulle globale */
.stChatMessage { 
    background-color: rgba(255,255,255,0.95); 
    border-radius: 12px; 
    border: 1px solid #f0f0f0; 
    box-shadow: 0 2px 5px rgba(0,0,0,0.02);
}

/* Le Contenu Texte (Padding & Aération) */
[data-testid="stChatMessageContent"] {
    padding-top: 1rem !important;
    padding-bottom: 1rem !important;
    padding-right: 2.5rem !important; /* Espace à droite pour respirer */
    padding-left: 1.5rem !important;
}

/* Correction Alignement Avatar vs Titre */
/* Remonte légèrement le titre "Analyse" pour l'aligner avec les yeux de l'avatar */
[data-testid="stChatMessageContent"] h3:first-of-type {
    margin-top: -5px !important; 
    padding-top: 0 !important;
}

/* 5. ZONE DE SAISIE */
div[data-testid="stChatInput"] button {
    color: #eda146 !important; /* Couleur du bouton envoyer */
}
</style>
""", unsafe_allow_html=True)

    # Gestion de l'image de fond (si présente)
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
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
/* 🚫 PLUS D'IMPORTS GOOGLE FONTS */

/* 1. CONFIGURATION GÉNÉRALE STREAMLIT */
#MainMenu, header, footer {visibility: hidden;}
[data-testid="stHeader"] {display: none;}
.block-container { padding-top: 1rem !important; padding-bottom: 5rem !important;}

/* 2. TYPOGRAPHIE : CORPS DE TEXTE (SYSTÈME) */
html, body, [class*="css"] {
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif !important;
    font-size: 16px !important;
    line-height: 1.6 !important;
}

/* 3. TYPOGRAPHIE : TITRES (SÉPARÉS & CIBLÉS) */

/* H1 : Le Grand Titre Principal */
h1 {
    font-family: Georgia, 'Times New Roman', Times, serif !important;
    color: #253E92 !important;
    font-weight: 700 !important;
    font-size: 32px !important;
    padding-bottom: 10px !important;
}

/* H2 : Les Sous-Titres */
h2 {
    font-family: Georgia, 'Times New Roman', Times, serif !important;
    color: #253E92 !important;
    font-weight: 700 !important;
    font-size: 24px !important;
    margin-top: 20px !important;
}

/* --- H3 : CIBLAGE RENFORCÉ POUR LE CHAT --- */
/* On cible spécifiquement les h3 DANS le contenu du message pour être prioritaire */
[data-testid="stChatMessageContent"] h3 {
    font-family: Georgia, 'Times New Roman', Times, serif !important;
    color: #253E92 !important;
    font-weight: 600 !important; /* 500 est souvent trop fin sur Georgia, 600 est mieux */
    font-size: 18px !important; /* Votre demande (Petit titre) */
    
    /* ESPACEMENT FORCÉ */
    margin-top: 30px !important;    /* Augmenté à 30px pour bien voir la séparation */
    margin-bottom: 10px !important;
    line-height: 1.4 !important;
}

/* EXCEPTION : Le tout premier H3 (ANALYSE) doit coller en haut */
[data-testid="stChatMessageContent"] h3:first-of-type {
    margin-top: -5px !important; /* On annule la marge de 30px juste pour lui */
    padding-top: 0 !important;
}

/* 4. BOUTON UPLOAD */
.fake-upload-btn {
    font-family: inherit !important;
    font-size: 14px !important;
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

/* 5. MESSAGES DE CHAT */
.stChatMessage { 
    background-color: rgba(255,255,255,0.95); 
    border-radius: 12px; 
    border: 1px solid #f0f0f0; 
    box-shadow: 0 2px 5px rgba(0,0,0,0.02);
}

[data-testid="stChatMessageContent"] {
    padding-top: 1rem !important;
    padding-bottom: 1rem !important;
    padding-right: 2.5rem !important;
    padding-left: 1.5rem !important;
}

/* 6. INPUT ZONE */
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
import streamlit as st
import os
import base64

def get_base64(bin_file):
    """Permet de charger une image en fond d'écran via CSS"""
    if os.path.exists(bin_file):
        return base64.b64encode(open(bin_file, "rb").read()).decode()
    return ""

def apply_pro_design():
    """Applique le CSS global + Tweaks couleurs Chat (Texte pâle & Icône Orange)"""
    st.markdown("""
<style>
/* --- IMPORT DES POLICES --- */
@import url('https://fonts.googleapis.com/css2?family=Open+Sans:wght@400;600&display=swap');

/* --- NETTOYAGE INTERFACE STREAMLIT --- */
#MainMenu, header, footer {visibility: hidden;}
[data-testid="stHeader"] {display: none;}
.block-container { padding-top: 1rem !important; padding-bottom: 5rem !important;}

/* --- TYPOGRAPHIE --- */
h1 {
    font-family: 'Baskerville', 'Georgia', serif !important;
    color: #253E92 !important;
    font-size: 35px !important;
    font-weight: 700 !important;
    text-transform: none !important; 
    margin-top: 10px !important;
    margin-bottom: 10px !important; 
    text-align: left !important;
}
h2 {
    font-family: 'Open Sans', sans-serif!important;
    color: #253E92 !important;
    font-size: 20px !important;
    font-weight: 600 !important;
    text-transform: none !important; 
    margin-top: 10px !important;
    margin-bottom: 20px !important; 
    text-align: left !important;
}

/* --- BOUTONS STANDARD & UPLOAD --- */
.fake-upload-btn {
    font-family: 'Open Sans', sans-serif;
    font-size: 12px;
    height: 40px;
    width: 100%;
    background-color: white;
    border: 1px solid #ccc;
    border-radius: 4px;
    color: #333;
    display: flex;
    align-items: center;
    justify-content: center;
    pointer-events: none;
}
[data-testid="stFileUploader"] {
    margin-top: -42px !important;
    opacity: 0 !important;
    z-index: 99 !important;
    height: 40px !important;
}
[data-testid="stFileUploader"] section {
    height: 40px !important;
    min-height: 40px !important;
    padding: 0 !important;
}

/* --- BOUTONS DU FOOTER (ROUGE & GRIS) --- */
button[kind="primary"] {
    background-color: transparent !important;
    border: none !important;
    box-shadow: none !important;
    color: #d32f2f !important; /* Rouge vif */
    padding: 0px !important;
    text-decoration: underline !important;
    transition: all 0.2s ease;
}
button[kind="primary"] p {
    font-size: 11px !important;
    font-weight: 800 !important;
    text-transform: uppercase !important;
    padding-top: 3px !important;
}
button[kind="primary"]:hover {
    color: #b71c1c !important;
    text-decoration: underline !important;
    background-color: transparent !important;
}

button[kind="tertiary"] p {
    font-size: 11px !important;
    font-family: 'Open Sans', sans-serif !important;
    color: #7A7A7A !important;
}
button[kind="tertiary"] {
    padding: 0px !important;
    height: auto !important;
    min-height: 0px !important;
    border: none !important;
}

/* --- RESPONSIVE & MESSAGES --- */
@media (max-width: 768px) {
    [data-testid="column"] { margin-bottom: -15px !important; }
    div[data-testid="stVerticalBlock"] > div { gap: 0.5rem !important; }
}
.stChatMessage { background-color: rgba(255,255,255,0.95); border-radius: 15px; border: 1px solid #e0e0e0; }


/* --- 🎨 MODIFICATIONS COULEURS CHAT (CHIRURGICAL) --- */

/* 1. GESTION DU TEXTE */
div[data-testid="stChatInput"] textarea {
    color: #000000 !important; /* Le texte écrit par l'utilisateur reste bien NOIR */
}

/* Le texte "fantôme" (Placeholder) devient GRIS PÂLE */
div[data-testid="stChatInput"] textarea::placeholder {
    color: #b0b0b0 !important; /* Gris clair */
    opacity: 1 !important;
}

/* 2. GESTION DE L'ICÔNE D'ENVOI */
div[data-testid="stChatInput"] button {
    color: #eda146 !important; /* L'icône devient ORANGE */
    border: none !important;
    background: transparent !important;
}

/* Petit effet au survol (Orange un peu plus foncé) */
div[data-testid="stChatInput"] button:hover {
    color: #c98636 !important;
}

</style>
""", unsafe_allow_html=True)

    # Gestion de l'image de fond
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
    else:
        st.markdown("""
            <style>
            .stApp {
                background-image: url("https://www.transparenttextures.com/patterns/legal-pad.png");
                background-size: cover;
                background-color: #f0f2f6;
            }
            </style>
        """, unsafe_allow_html=True)
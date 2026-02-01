import streamlit as st
import os
import base64

def get_base64(bin_file):
    """Permet de charger une image en fond d'écran via CSS"""
    if os.path.exists(bin_file):
        return base64.b64encode(open(bin_file, "rb").read()).decode()
    return ""

def apply_pro_design():
    """Applique le CSS global (Baskerville, Boutons Rouges, Chat Style Carré Orange V6)"""
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

/* --- 💬 BARRE DE CHAT V6 (FORCE BRUTE) --- */

/* 1. CIBLAGE DU WRAPPER INTERNE (C'est lui qui porte la bordure) */
div[data-testid="stChatInput"] > div {
    border-radius: 12px !important;
    border: 2px solid #e0e0e0 !important; /* Bordure GRISE par défaut */
    background-color: white !important; /* Fond BLANC forcé */
    box-shadow: 0 4px 6px rgba(0,0,0,0.05) !important;
    align-items: center !important;
    padding-right: 5px !important;
}

/* 2. FOCUS SUR LE WRAPPER (La bordure devient ORANGE) */
div[data-testid="stChatInput"] > div:focus-within {
    border-color: #eda146 !important; /* ORANGE au focus */
    box-shadow: 0 4px 12px rgba(237, 161, 70, 0.2) !important;
}

/* 3. LE CHAMP TEXTE (Transparent pour laisser voir le blanc derrière) */
div[data-testid="stChatInput"] textarea {
    background-color: transparent !important;
    color: #333 !important;
    font-size: 16px !important;
    padding: 10px !important;
    border: none !important; /* Pas de bordure interne */
}

/* Placeholder pâle */
div[data-testid="stChatInput"] textarea::placeholder {
    color: #d0d0d0 !important;
    opacity: 1 !important;
}

/* 4. LE BOUTON CARRÉ ORANGE */
div[data-testid="stChatInput"] button {
    background-color: #eda146 !important; /* ORANGE */
    color: white !important;
    border-radius: 8px !important; /* Carré arrondi */
    width: 38px !important;
    height: 38px !important;
    border: none !important;
    outline: none !important;
    display: flex !important;
    align-items: center !important;
    justify-content: center !important;
    margin-left: 5px !important;
}

/* Suppression des effets parasites au clic */
div[data-testid="stChatInput"] button:focus,
div[data-testid="stChatInput"] button:active {
    background-color: #eda146 !important;
    color: white !important;
    border: none !important;
    outline: none !important;
    box-shadow: none !important;
}

/* 5. REMPLACEMENT ICÔNE PAR FLÈCHE */
div[data-testid="stChatInput"] button svg {
    display: none !important;
}

div[data-testid="stChatInput"] button::after {
    content: "↑" !important;
    color: white !important;
    font-size: 20px !important;
    font-weight: bold !important;
    line-height: 1 !important;
    padding-bottom: 2px !important;
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
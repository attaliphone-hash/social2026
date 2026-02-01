import streamlit as st
import os
import base64

def get_base64(bin_file):
    """Permet de charger une image en fond d'écran via CSS"""
    if os.path.exists(bin_file):
        return base64.b64encode(open(bin_file, "rb").read()).decode()
    return ""

def apply_pro_design():
    """Applique le CSS global (Baskerville, Boutons Rouges, Chat Style Capture User)"""
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

/* --- 💬 BARRE DE CHAT V4 (CONFORME CAPTURE USER) --- */

/* 1. La Zone Globale (La Capsule) */
div[data-testid="stChatInput"] {
    border-radius: 12px !important; /* Arrondi léger comme sur la capture */
    border: 1px solid #E0E0E0 !important;
    background-color: white !important;
    box-shadow: 0 2px 6px rgba(0,0,0,0.05) !important;
    padding: 3px !important;
    margin-bottom: 20px !important;
    align-items: center !important;
}

/* 2. Focus : Quand on clique dedans (Bordure ORANGE fine) */
div[data-testid="stChatInput"]:focus-within {
    border-color: #eda146 !important;
    box-shadow: 0 4px 10px rgba(237, 161, 70, 0.15) !important;
}

/* 3. Le Champ de texte */
div[data-testid="stChatInput"] textarea {
    background-color: transparent !important;
    color: #333 !important;
    font-size: 15px !important;
    padding-left: 10px !important;
}

/* Placeholder TRES PÂLE (Demande utilisateur) */
div[data-testid="stChatInput"] textarea::placeholder {
    color: #d0d0d0 !important; /* Gris très clair */
    opacity: 1 !important;
}

/* 4. LE BOUTON (CARRÉ ARRONDIS ORANGE) */
div[data-testid="stChatInput"] button {
    background-color: #eda146 !important; /* Orange User */
    color: white !important;
    border-radius: 8px !important; /* Le "Squircle" de la capture */
    width: 32px !important;
    height: 32px !important;
    border: none !important;
    outline: none !important;
    box-shadow: none !important; /* Supprime le liseré carré moche */
    margin-right: 0px !important;
    display: flex !important;
    align-items: center !important;
    justify-content: center !important;
}

/* Suppression FORCEE des bordures focus natives */
div[data-testid="stChatInput"] button:focus, 
div[data-testid="stChatInput"] button:active {
    box-shadow: none !important;
    outline: none !important;
    border: none !important;
    background-color: #eda146 !important;
}

/* 5. L'ICÔNE : ON REMPLACE LE SVG PAR UNE VRAIE FLÈCHE */

/* Étape A : On cache l'icône par défaut (souvent un avion) */
div[data-testid="stChatInput"] button svg {
    display: none !important;
}

/* Étape B : On injecte une flèche simple via CSS */
div[data-testid="stChatInput"] button::after {
    content: "↑" !important; /* Caractère flèche simple */
    color: white !important;
    font-size: 18px !important;
    font-weight: bold !important;
    line-height: 1 !important;
    margin-bottom: 2px !important; /* Ajustement centrage vertical */
}

/* Hover du bouton */
div[data-testid="stChatInput"] button:hover {
    background-color: #d68b35 !important;
}

</style>
""", unsafe_allow_html=True)

    # Gestion de l'image de fond
    bg_data = get_base64('background.webp')
    if bg_data:
        st.markdown(f'<style>.stApp {{ background-image: url("data:image/
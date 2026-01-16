import streamlit as st
import os
import base64

# ==============================================================================
# DONNÉES DE RÉASSURANCE
# ==============================================================================
ARGUMENTS_UNIFIES = [
    ("Données Certifiées 2026 :", " Intégration prioritaire des nouveaux textes."),
    ("Sources officielles :", " Analyse simultanée BOSS, Code du Travail, URSSAF."),
    ("Mise à Jour Agile :", " Base actualisée en temps réel dès publication."),
    ("Traçabilité Totale :", " Chaque réponse est systématiquement sourcée."),
    ("Confidentialité :", " Aucun cookie pub. Données traitées en RAM uniquement.")
]

def get_base64(bin_file):
    if os.path.exists(bin_file):
        return base64.b64encode(open(bin_file, "rb").read()).decode()
    return ""

def apply_pro_design():
    st.markdown("""
        <style>
        #MainMenu {visibility: hidden;}
        header {visibility: hidden !important; height: 0px;}
        footer {visibility: hidden;}
        [data-testid="stHeader"] {display: none;}
        .block-container { padding-top: 1rem !important; padding-bottom: 5rem !important;}

        /* --- 1. TITRE H1 (Remonté vers le haut et compact) --- */
        h1 {
            color: #000066 !important;
            font-family: 'Baskerville', 'Georgia', serif !important;
            font-weight: 800 !important;
            font-size: 35px !important;
            text-transform: uppercase !important; 
            margin-top: 5px !important; /* Espace réduit au dessus */
            padding-top: 0px !important;
            margin-bottom: 20px !important; 
            line-height: 1.0 !important;
        }

        /* --- 2. BOUTONS D'ACTION (Upload / Session) - Haut de page --- */
        /* On cible les boutons "Secondary" (classiques) pour qu'ils soient petits et discrets */
        button[data-testid="stBaseButton-secondary"] {
            background-color: rgba(255, 255, 255, 0.7) !important;
            border: 1px solid #ddd !important;
            color: #555 !important;
            font-size: 11px !important; /* Police petite */
            padding: 2px 8px !important;
            height: auto !important;
            min-height: 28px !important;
            box-shadow: none !important;
        }
        button[data-testid="stBaseButton-secondary"]:hover {
            background-color: white !important;
            border-color: #aaa !important;
            color: #000 !important;
        }

        /* Hack spécifique pour le bouton Upload pour qu'il ressemble aux autres */
        .stFileUploader button {
            background-color: rgba(255, 255, 255, 0.7) !important;
            border: 1px solid #ddd !important;
            color: transparent !important; /* On cache le texte anglais */
            padding: 2px 8px !important;
            font-size: 11px !important;
            height: auto !important;
            min-height: 28px !important;
        }
        .stFileUploader button::after {
            content: "Charger un document";
            color: #555 !important;
            position: absolute;
            left: 0; top: 0;
            width: 100%; height: 100%;
            display: flex; justify-content: center; align-items: center;
            font-size: 11px !important;
            font-weight: normal !important;
        }
        
        /* Nettoyage interface Upload */
        .stFileUploader section { background: transparent !important; border: none !important; padding: 0 !important; }
        .stFileUploader [data-testid="stFileUploaderDropzoneInstructions"] { display: none !important; }
        .stFileUploader div[data-testid="stFileUploaderInterface"] { margin: 0 !important; }


        /* --- 3. FOOTER INTEGRÉ (Gris, Petit, Fondu) --- */
        
        /* Le texte copyright "normal" */
        .footer-text {
            color: #888 !important;
            font-size: 11px !important;
            font-family: sans-serif !important;
            margin: 0 !important;
            padding: 0 !important;
            display: flex;
            align-items: center;
            height: 100%;
        }

        /* Transformation des boutons "Tertiary" en LIENS TEXTE GRIS */
        button[data-testid="stBaseButton-tertiary"] {
            background: transparent !important;
            border: none !important;
            box-shadow: none !important;
            color: #888 !important; /* MÊME COULEUR QUE LE COPYRIGHT */
            text-decoration: underline !important; 
            text-decoration-style: dotted !important;
            font-size: 11px !important; 
            padding: 0px 5px !important; 
            margin: 0px !important;
            height: auto !important;
            min-height: 0px !important;
            width: auto !important;
            line-height: 1 !important;
        }
        
        button[data-testid="stBaseButton-tertiary"]:hover {
            color: #444 !important; /* Devient plus sombre au survol */
            background: transparent !important;
            text-decoration-style: solid !important;
        }

        /* --- AUTRES STYLES --- */
        .stChatMessage { background-color: rgba(255,255,255,0.95); border-radius: 15px; padding: 10px; margin-bottom: 10px; border: 1px solid #e0e0e0; }
        
        /* Styles Alertes BOSS (Nécessaires pour app.py) */
        .boss-alert-box { padding: 12px !important; border-radius: 8px !important; margin-bottom: 10px !important; font-size: 14px !important; }
        .boss-red { background-color: #f8d7da !important; color: #721c24 !important; border: 1px solid #f5c6cb !important; }
        .boss-green { background-color: #d4edda !important; color: #155724 !important; border: 1px solid #c3e6cb !important; }
        .boss-link { text-decoration: underline !important; font-weight: bold !important; color: inherit !important; }
        
        .assurance-text { font-size: 10px !important; color: #024c6f !important; text-align: left; line-height: 1.3; margin-bottom: 5px; }
        .assurance-title { font-weight: bold; color: #024c6f; font-size: 10px !important; }
        .assurance-desc { font-weight: normal; color: #444; font-size: 10px !important; }
        
        </style>
    """, unsafe_allow_html=True)

    # Fond d'écran
    bg_data = get_base64('background.webp')
    if bg_data:
        st.markdown(f'<style>.stApp {{ background-image: url("data:image/webp;base64,{bg_data}"); background-size: cover; background-attachment: fixed; }}</style>', unsafe_allow_html=True)
    else:
        st.markdown("""<style>.stApp { background-image: url("https://www.transparenttextures.com/patterns/legal-pad.png"); background-size: cover; background-color: #f0f2f6; }</style>""", unsafe_allow_html=True)

def render_top_columns():
    cols = st.columns(5, gap="small")
    for i, col in enumerate(cols):
        title, desc = ARGUMENTS_UNIFIES[i]
        col.markdown(f'<p class="assurance-text"><span class="assurance-title">{title}</span><span class="assurance-desc">{desc}</span></p>', unsafe_allow_html=True)

def render_subscription_cards():
    col_m, col_a = st.columns(2)
    with col_m:
        st.markdown("""<div style="background-color: #e3f2fd; border-radius: 10px; padding: 20px; text-align: center; border: 1px solid #bbdefb;"><h3>Mensuel</h3><h2>50 € HT <small>/ mois</small></h2><p>Sans engagement</p></div><br>""", unsafe_allow_html=True)
        st.button("S'abonner (Mensuel)", key="btn_sub_month", use_container_width=True)
    with col_a:
        st.markdown("""<div style="background-color: #e8f5e9; border-radius: 10px; padding: 20px; text-align: center; border: 1px solid #c8e6c9;"><h3>Annuel</h3><h2>500 € HT <small>/ an</small></h2><p>2 mois offerts</p></div><br>""", unsafe_allow_html=True)
        st.button("S'abonner (Annuel)", key="btn_sub_year", use_container_width=True)
import streamlit as st
import os
import base64

# ==============================================================================
# DONNÉES DE RÉASSURANCE
# ==============================================================================
ARGUMENTS_UNIFIES = [
    ("Données Certifiées 2026 :", " Intégration prioritaire des nouveaux textes pour une précision chirurgicale."),
    ("Sources officielles :", " Une analyse simultanée et croisée du BOSS, du Code du Travail, du Code de la Sécurité Sociale et des communiqués des organismes sociaux."),
    ("Mise à Jour Agile :", " Notre base est actualisée en temps réel dès la publication de nouvelles circulaires ou réformes, garantissant une conformité permanente."),
    ("Traçabilité Totale :", " Chaque réponse est systématiquement sourcée via une liste détaillée, permettant de valider instantanément le fondement juridique."),
    ("Confidentialité Garantie :", " Aucun cookie publicitaire. Vos données sont traitées exclusivement en mémoire vive (RAM) et ne sont jamais utilisées pour entraîner des modèles d'IA.")
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

        /* --- 1. TITRE H1 --- */
        h1 {
            color: #000066 !important;
            font-family: 'Baskerville', 'Georgia', serif !important;
            font-weight: 800 !important;
            font-size: 35px !important;
            text-transform: uppercase !important; 
            margin-top: 10px !important;
            padding-top: 0px !important;
            margin-bottom: 20px !important; 
            line-height: 1.0 !important;
        }

        /* --- 2. BOUTONS D'ACTION (HAUT) - FIXATION STRICTE --- */
        
        /* Bouton "Nouvelle Session" (Standard) */
        button[data-testid="stBaseButton-secondary"] {
            background-color: rgba(255, 255, 255, 0.8) !important;
            border: 1px solid #ccc !important;
            color: #444 !important;
            font-size: 12px !important;
            font-weight: 500 !important;
            height: 38px !important;     /* Hauteur forcée */
            min-height: 38px !important; /* Hauteur forcée */
            width: 100% !important;
            margin: 0 !important;
            padding: 0px 10px !important;
            line-height: 1 !important;
            display: flex;
            align-items: center;
            justify-content: center;
        }

        /* Bouton "Upload" (Spécifique) */
        [data-testid="stFileUploader"] button {
            background-color: rgba(255, 255, 255, 0.8) !important;
            border: 1px solid #ccc !important;
            color: transparent !important; /* Cache le texte anglais */
            font-size: 0px !important;     /* Réduit le texte anglais à néant */
            height: 38px !important;
            min-height: 38px !important;
            width: 100% !important;
            margin: 0 !important;
            padding: 0 !important;
            position: relative !important; /* INDISPENSABLE pour le texte centré */
        }

        /* Le texte "Charger un document" qui se superpose */
        [data-testid="stFileUploader"] button::after {
            content: "Charger un document";
            position: absolute;
            top: 50%;
            left: 50%;
            transform: translate(-50%, -50%); /* Centrage parfait mathématique */
            color: #444 !important;
            font-size: 12px !important;
            font-weight: 500 !important;
            white-space: nowrap;
            pointer-events: none;
        }
        
        /* Nettoyage de l'interface Upload */
        [data-testid="stFileUploader"] section { padding: 0 !important; }
        [data-testid="stFileUploaderDropzoneInstructions"] { display: none !important; }
        [data-testid="stFileUploader"] div[data-testid="stFileUploaderInterface"] { margin: 0 !important; }


        /* --- 3. FOOTER INTEGRÉ - ALIGNEMENT PIXEL --- */
        
        /* Texte Copyright */
        .footer-text {
            color: #999 !important;
            font-size: 11px !important;
            font-family: sans-serif !important;
            margin: 0 !important;
            padding: 0 !important;
            line-height: 24px !important; /* Doit matcher la hauteur des boutons */
            text-align: right;
            display: block;
        }

        /* Liens (Boutons transformés) */
        button[data-testid="stBaseButton-tertiary"] {
            background: transparent !important;
            border: none !important;
            box-shadow: none !important;
            color: #999 !important; 
            text-decoration: underline !important; 
            font-size: 11px !important;
            padding: 0px 5px !important; 
            margin: 0px !important;
            height: 24px !important;
            min-height: 24px !important;
            line-height: 24px !important;
            white-space: nowrap !important;
            vertical-align: middle !important;
        }
        
        button[data-testid="stBaseButton-tertiary"]:hover {
            color: #555 !important;
        }
        
        /* Enlève le gap entre les colonnes du footer pour serrer les éléments */
        [data-testid="column"] {
            gap: 0rem !important;
        }

        /* --- AUTRES --- */
        .stChatMessage { background-color: rgba(255,255,255,0.95); border-radius: 15px; padding: 10px; margin-bottom: 10px; border: 1px solid #e0e0e0; }
        
        .boss-alert-box { padding: 12px !important; border-radius: 8px !important; margin-bottom: 10px !important; font-size: 14px !important; }
        .boss-red { background-color: #f8d7da !important; color: #721c24 !important; border: 1px solid #f5c6cb !important; }
        .boss-green { background-color: #d4edda !important; color: #155724 !important; border: 1px solid #c3e6cb !important; }
        .boss-link { text-decoration: underline !important; font-weight: bold !important; color: inherit !important; }
        
        .assurance-text { font-size: 10px !important; color: #024c6f !important; text-align: left; line-height: 1.3; margin-bottom: 5px; }
        .assurance-title { font-weight: bold; color: #024c6f; font-size: 10px !important; }
        .assurance-desc { font-weight: normal; color: #444; font-size: 10px !important; }
        
        </style>
    """, unsafe_allow_html=True)

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
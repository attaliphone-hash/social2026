import streamlit as st
import os
import base64

# ==============================================================================
# DONNÉES DE RÉASSURANCE (VERSION LONGUE REMISE EN PLACE)
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
    # Import Police Open Sans
    st.markdown("""
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Open+Sans:wght@400;600&display=swap');

        #MainMenu {visibility: hidden;}
        header {visibility: hidden !important; height: 0px;}
        footer {visibility: hidden;}
        [data-testid="stHeader"] {display: none;}
        .block-container { padding-top: 1rem !important; padding-bottom: 5rem !important;}

        /* --- 1. TITRE H1 (Baskerville - Aligné Gauche) --- */
        h1 {
            font-family: 'Baskerville', 'Libre Baskerville', 'Georgia', serif !important;
            color: #253E92 !important;
            font-size: 35px !important;
            font-weight: 700 !important;
            text-transform: uppercase !important; 
            margin-top: 10px !important;
            padding-top: 0px !important;
            margin-bottom: 20px !important; 
            line-height: 1.1 !important;
            text-align: left !important;
        }

        /* --- 2. BOUTONS (Nouvelle Session & Upload) --- */
        
        /* Style de base commun */
        button[data-testid="stBaseButton-secondary"], 
        [data-testid="stFileUploader"] button {
            font-family: 'Open Sans', sans-serif !important;
            font-size: 12px !important;
            height: 40px !important;
            min-height: 40px !important;
            background-color: rgba(255, 255, 255, 0.9) !important;
            border: 1px solid #ccc !important;
            color: #333 !important;
            border-radius: 4px !important;
            box-shadow: none !important;
            margin: 0 !important;
            width: 100% !important;
            padding: 0 10px !important;
            /* Flexbox pour centrage vertical parfait */
            display: flex !important;
            align-items: center !important;
            justify-content: center !important;
            position: relative !important;
        }

        /* Survol */
        button[data-testid="stBaseButton-secondary"]:hover, 
        [data-testid="stFileUploader"] button:hover {
            border-color: #253E92 !important;
            background-color: #fff !important;
        }

        /* --- CORRECTION UPLOADER (LA MÉTHODE 'TRANSPARENT TEXT') --- */
        
        /* 1. On rend le texte anglais "Browse files" TRANSPARENT mais présent */
        /* Cela garde la forme du bouton intacte */
        [data-testid="stFileUploader"] button {
            color: transparent !important;
        }
        
        /* 2. On ajoute le texte français par dessus, centré */
        [data-testid="stFileUploader"] button::after {
            content: "Charger un document";
            font-family: 'Open Sans', sans-serif !important;
            font-size: 12px !important;
            color: #333 !important; /* Couleur du texte visible */
            position: absolute;
            top: 50%;
            left: 50%;
            transform: translate(-50%, -50%);
            white-space: nowrap;
            pointer-events: none; /* Le clic traverse vers le bouton */
        }

        /* Changement de couleur du texte français au survol */
        [data-testid="stFileUploader"] button:hover::after {
            color: #253E92 !important;
        }

        /* Suppression des icônes parasites ou instructions */
        [data-testid="stFileUploader"] button svg { display: none !important; }
        [data-testid="stFileUploaderDropzoneInstructions"] { display: none !important; }
        [data-testid="stFileUploader"] section { padding: 0 !important; min-height: 0 !important; }
        [data-testid="stFileUploader"] div[data-testid="stFileUploaderInterface"] { margin: 0 !important; }


        /* --- 3. BARRE DE LIENS (Sous les arguments) --- */
        .footer-text {
            font-family: 'Open Sans', sans-serif !important;
            font-size: 11px !important; 
            color: #7A7A7A !important;
            margin: 0 !important;
            padding: 0 !important;
            white-space: nowrap;
        }

        button[data-testid="stBaseButton-tertiary"] {
            font-family: 'Open Sans', sans-serif !important;
            font-size: 11px !important; 
            color: #7A7A7A !important;
            background: transparent !important;
            border: none !important;
            box-shadow: none !important;
            text-decoration: none !important; 
            padding: 0 !important;
            margin: 0 !important;
            height: auto !important;
            line-height: 1 !important;
        }
        
        button[data-testid="stBaseButton-tertiary"]:hover {
            color: #253E92 !important;
            text-decoration: underline !important;
        }

        /* --- AUTRES --- */
        .stChatMessage { background-color: rgba(255,255,255,0.95); border-radius: 15px; padding: 10px; margin-bottom: 10px; border: 1px solid #e0e0e0; }
        .assurance-text { font-size: 10px !important; color: #024c6f !important; text-align: left; line-height: 1.3; margin-bottom: 5px; }
        .assurance-title { font-weight: bold; color: #024c6f; font-size: 10px !important; }
        .assurance-desc { font-weight: normal; color: #444; font-size: 10px !important; }
        
        .boss-alert-box { padding: 12px !important; border-radius: 8px !important; margin-bottom: 10px !important; font-size: 14px !important; }
        .boss-red { background-color: #f8d7da !important; color: #721c24 !important; border: 1px solid #f5c6cb !important; }
        .boss-green { background-color: #d4edda !important; color: #155724 !important; border: 1px solid #c3e6cb !important; }
        .boss-link { text-decoration: underline !important; font-weight: bold !important; color: inherit !important; }

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
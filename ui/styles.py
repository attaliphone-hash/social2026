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

# ==============================================================================
# FONCTIONS UTILITAIRES DE DESIGN
# ==============================================================================
def get_base64(bin_file):
    if os.path.exists(bin_file):
        return base64.b64encode(open(bin_file, "rb").read()).decode()
    return ""

def apply_pro_design():
    # CSS EXACT + CSS UPLOAD DISCRET + CSS PETITS BOUTONS FOOTER
    st.markdown("""
        <style>
        #MainMenu {visibility: hidden;}
        header {visibility: hidden !important; height: 0px;}
        footer {visibility: hidden;}
        [data-testid="stHeader"] {display: none;}
        .block-container { padding-top: 1rem !important; padding-bottom: 5rem !important;}

        /* Design des bulles de chat */
        .stChatMessage { background-color: rgba(255,255,255,0.95); border-radius: 15px; padding: 10px; margin-bottom: 10px; border: 1px solid #e0e0e0; }
        .stChatMessage p, .stChatMessage li { color: black !important; line-height: 1.6 !important; }

        /* --- CSS UPLOAD DISCRET & TRADUIT --- */
        .stFileUploader section {
            background-color: transparent !important;
            border: none !important;
            padding: 0 !important;
            min-height: 0 !important;
        }
        .stFileUploader [data-testid="stFileUploaderDropzoneInstructions"] {
            display: none !important;
        }
        .stFileUploader div[data-testid="stFileUploaderInterface"] {
            padding: 0 !important;
            margin: 0 !important;
        }

        /* REECRITURE DU TEXTE DU BOUTON (HACK CSS) */
        .stFileUploader button {
            border: 1px solid #ccc !important;
            background-color: white !important;
            color: transparent !important; /* On cache le texte 'Browse files' */
            padding: 0.25rem 0.75rem !important;
            font-size: 14px !important;
            margin-top: 3px !important;
            position: relative;
            width: 250px !important; 
        }

        .stFileUploader button::after {
            content: "Charger un document pour analyse";
            color: #333 !important;
            position: absolute;
            left: 0; top: 0;
            width: 100%; height: 100%;
            display: flex;
            justify-content: center;
            align-items: center;
            font-weight: 500;
        }

        /* CITATIONS (sub) */
        sub {
            font-size: 0.75em !important;
            color: #666 !important;
            vertical-align: baseline !important;
            position: relative;
            top: -0.3em;
        }

        /* ARGUMENTS EN HAUT */
        .assurance-text { font-size: 10px !important; color: #024c6f !important; text-align: left; display: block; line-height: 1.3; margin-bottom: 5px; }
        .assurance-title { font-weight: bold; color: #024c6f; display: inline; font-size: 10px !important; }
        .assurance-desc { font-weight: normal; color: #444; display: inline; font-size: 10px !important; }

        /* TITRES */
        h1 {
            color: #000066 !important;
            font-family: 'Baskerville', 'Georgia', serif !important;
            font-weight: 800 !important;
            font-size: 35px !important;
            text-transform: uppercase !important; 
            margin-top: 0 !important;
            margin-bottom: 20px !important; 
            padding: 0 !important;
            line-height: 1.2 !important;
        }

        h2 {
            color: #1e3a8a !important;
            font-family: 'Arial', sans-serif !important;
            font-weight: 600 !important;
            font-size: 1.8rem !important;
            border-bottom: 2px solid #e2e8f0;
            padding-bottom: 8px !important;
            margin-top: 20px !important;
        }

        h3 {
            color: #334155 !important;
            font-weight: bold !important;
            font-size: 1.4rem !important;
            margin-top: 15px !important;
        }

        /* ============================================================ */
        /* STYLE SPÉCIFIQUE DES BOUTONS JURIDIQUES (TERTIARY)          */
        /* Correction validée : data-testid */
        /* ============================================================ */
        button[data-testid="stBaseButton-tertiary"] {
            background-color: rgba(245, 245, 245, 0.7) !important;
            border: 1px solid #ddd !important;
            color: #666 !important;
            font-size: 10px !important; /* Texte vraiment petit */
            padding: 4px 10px !important;
            height: auto !important;
            min-height: 0px !important;
            border-radius: 4px !important;
            width: auto !important; /* Pas full width pour ceux-là */
            transition: all 0.2s ease;
        }
        
        button[data-testid="stBaseButton-tertiary"]:hover {
            background-color: #e0e0e0 !important;
            color: #333 !important;
            border-color: #ccc !important;
        }

        /* ============================================================ */
        /* RESPONSIVE DESIGN                                           */
        /* ============================================================ */
        
        /* On cible uniquement les boutons CLASSIQUES (Secondary) pour le full width */
        button[data-testid="stBaseButton-secondary"] {
            width: 100% !important;        
            white-space: normal !important; 
            height: auto !important;        
        }

        @media (max-width: 1024px) {
            h1 { font-size: 28px !important; } 
            h2 { font-size: 1.5rem !important; margin-top: 20px !important; }
        }

        @media (max-width: 768px) {
            .block-container { padding-top: 1rem !important; }
            .assurance-text { margin-bottom: 5px !important; line-height: 1.1 !important; font-size: 9px !important; }
            h1 { font-size: 22px !important; }
        }

        /* FOOTER & ALERTS BOSS (CRITIQUE) */
        .footer-copyright {
            text-align: center !important;
            color: #888 !important;
            font-size: 10px !important;
            margin-top: 15px !important;
        }

        .boss-alert-box {
            padding: 12px !important;
            border-radius: 8px !important;
            margin-bottom: 10px !important;
            font-size: 14px !important;
        }
        .boss-red { background-color: #f8d7da !important; color: #721c24 !important; border: 1px solid #f5c6cb !important; }
        .boss-green { background-color: #d4edda !important; color: #155724 !important; border: 1px solid #c3e6cb !important; }
        .boss-link { text-decoration: underline !important; font-weight: bold !important; color: inherit !important; }

        </style>
    """, unsafe_allow_html=True)

    # CHARGEMENT FOND D'ECRAN
    bg_data = get_base64('background.webp')
    if bg_data:
        st.markdown(
            f'<style>.stApp {{ background-image: url("data:image/webp;base64,{bg_data}"); background-size: cover; background-attachment: fixed; }}</style>',
            unsafe_allow_html=True
        )
    else:
        st.markdown(
            """<style>.stApp { background-image: url("https://www.transparenttextures.com/patterns/legal-pad.png"); background-size: cover; background-color: #f0f2f6; }</style>""",
            unsafe_allow_html=True
        )

def render_top_columns():
    cols = st.columns(5, gap="small")
    for i, col in enumerate(cols):
        title, desc = ARGUMENTS_UNIFIES[i]
        col.markdown(
            f'<p class="assurance-text"><span class="assurance-title">{title}</span><span class="assurance-desc">{desc}</span></p>',
            unsafe_allow_html=True
        )

# ==============================================================================
# CARTES D'ABONNEMENT
# ==============================================================================
def render_subscription_cards():
    col_m, col_a = st.columns(2)

    with col_m:
        st.markdown("""
        <div style="background-color: #e3f2fd; border-radius: 10px; padding: 20px; text-align: center; border: 1px solid #bbdefb; height: 100%;">
            <h3 style="color: #0d47a1; margin-top: 0;">Mensuel</h3>
            <h2 style="color: #1565c0; font-size: 24px; margin: 10px 0;">50 € HT <small style="font-size: 14px; color: #555;">/ mois</small></h2>
            <p style="color: #0277bd; font-style: italic; font-size: 14px;">Sans engagement</p>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)
        st.button("S'abonner (Mensuel)", key="btn_sub_month", use_container_width=True)

    with col_a:
        st.markdown("""
        <div style="background-color: #e8f5e9; border-radius: 10px; padding: 20px; text-align: center; border: 1px solid #c8e6c9; height: 100%;">
            <h3 style="color: #1b5e20; margin-top: 0;">Annuel</h3>
            <h2 style="color: #2e7d32; font-size: 24px; margin: 10px 0;">500 € HT <small style="font-size: 14px; color: #555;">/ an</small></h2>
            <p style="color: #2e7d32; font-style: italic; font-size: 14px;">2 mois offerts</p>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)
        st.button("S'abonner (Annuel)", key="btn_sub_year", use_container_width=True)
import streamlit as st
import os
import base64

# ==============================================================================
# 1. ARGUMENTS (VERSION LONGUE - STRICTE)
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
        @import url('https://fonts.googleapis.com/css2?family=Open+Sans:wght@400;600&display=swap');

        /* Cache Header/Footer Streamlit */
        #MainMenu, header, footer {visibility: hidden;}
        [data-testid="stHeader"] {display: none;}
        .block-container { padding-top: 1rem !important; padding-bottom: 5rem !important;}

        /* --- TITRE H1 --- */
        h1 {
            font-family: 'Baskerville', 'Georgia', serif !important;
            color: #253E92 !important;
            font-size: 35px !important;
            font-weight: 700 !important;
            text-transform: uppercase !important; 
            margin-top: 10px !important;
            margin-bottom: 20px !important; 
            text-align: left !important;
        }
        /* ---H2 --- */
        h2 {
            font-family: 'Open Sans', sans-serif!important;
            color: #253E92 !important;
            font-size: 20px !important;
            font-weight: 700 !important;
            text-transform: uppercase !important; 
            margin-top: 10px !important;
            margin-bottom: 20px !important; 
            text-align: left !important;
        }

        /* --- LE FAUX BOUTON UPLOAD (Visuel uniquement) --- */
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
            box-shadow: 0 1px 2px rgba(0,0,0,0.05);
            pointer-events: none; /* Le clic doit passer au travers vers l'uploader invisible */
        }

        /* --- LE VRAI UPLOADER (Invisible & Superposé) --- */
        [data-testid="stFileUploader"] {
            margin-top: -42px !important; /* On le remonte pour couvrir le faux bouton */
            opacity: 0 !important;        /* On le rend invisible */
            z-index: 99 !important;       /* On le met au-dessus */
            height: 40px !important;
        }
        
        [data-testid="stFileUploader"] section {
            height: 40px !important;
            min-height: 40px !important;
            padding: 0 !important;
        }
        
        /* Ajustement de la zone de drop pour qu'elle ne soit pas trop grande */
        [data-testid="stFileUploader"] button {
            width: 100% !important;
            height: 40px !important;
        }

        /* --- BOUTON NOUVELLE SESSION --- */
        button[data-testid="stBaseButton-secondary"] {
            font-family: 'Open Sans', sans-serif !important;
            font-size: 12px !important;
            height: 40px !important;
            min-height: 40px !important;
            background-color: white !important;
            border: 1px solid #ccc !important;
            color: #333 !important;
            border-radius: 4px !important;
            width: 100% !important;
            box-shadow: 0 1px 2px rgba(0,0,0,0.05);
        }
        button[data-testid="stBaseButton-secondary"]:hover {
            border-color: #253E92 !important;
            color: #253E92 !important;
        }

        /* --- FOOTER & TEXTES --- */
        .footer-text {
            font-family: 'Open Sans', sans-serif !important;
            font-size: 11px !important; 
            color: #7A7A7A !important;
        }

        button[data-testid="stBaseButton-tertiary"] {
            font-family: 'Open Sans', sans-serif !important;
            font-size: 11px !important; 
            color: #7A7A7A !important;
            background: transparent !important;
            border: none !important;
            padding: 0 !important;
            text-decoration: none !important; 
        }
        button[data-testid="stBaseButton-tertiary"]:hover {
            color: #253E92 !important;
            text-decoration: underline !important;
        }

        .assurance-text { font-size: 11px !important; color: #024c6f !important; line-height: 1.3; margin-bottom: 5px; }
        .assurance-title { font-weight: bold; color: #024c6f; font-size: 11px !important; }
        .assurance-desc { font-weight: normal; color: #444; font-size: 11px !important; }
        
        .stChatMessage { background-color: rgba(255,255,255,0.95); border-radius: 15px; border: 1px solid #e0e0e0; }
        .boss-alert-box { padding: 12px !important; border-radius: 8px !important; font-size: 14px !important; }

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
    """Affiche les cartes d'abonnement Mensuel (Bleu) et Annuel (Vert)"""
    import streamlit as st
    
    col1, col2 = st.columns(2, gap="medium")
    
    # --- CARTE MENSUELLE (BLEU) ---
    with col1:
        st.markdown("""
        <div style="background-color: #e3f2fd; padding: 20px; border-radius: 10px; border: 1px solid #90caf9; height: 100%;">
            <h3 style="color: #1565c0; margin-top:0;">Mensuel</h3>
            <h2 style="color: #0d47a1; font-size: 28px;">35 € <span style="font-size:16px; color:#555;">HT / MOIS</span></h2>
            <p style="color: #333; font-size: 14px; margin-top: 10px;">Sans engagement</p>
            <p style="color: #666; font-size: 13px;">Accès complet Expert Pro 2026</p>
        </div>
        """, unsafe_allow_html=True)
        
        # LIEN STRIPE MENSUEL (35€)
        st.link_button("S'abonner (Mensuel)", "https://buy.stripe.com/6oUeVf4U0enk1g07Q77AI01", use_container_width=True)

    # --- CARTE ANNUELLE (VERT) ---
    with col2:
        st.markdown("""
        <div style="background-color: #e8f5e9; padding: 20px; border-radius: 10px; border: 1px solid #a5d6a7; height: 100%;">
            <h3 style="color: #2e7d32; margin-top:0;">Annuel</h3>
            <h2 style="color: #1b5e20; font-size: 28px;">350 € <span style="font-size:16px; color:#555;">HT / AN</span></h2>
            <p style="color: #333; font-size: 14px; margin-top: 10px;">2 mois offerts</p>
            <p style="color: #666; font-size: 13px;">✅ Rentabilité immédiate</p>
        </div>
        """, unsafe_allow_html=True)
        
        # LIEN STRIPE ANNUEL (350€)
        st.link_button("S'abonner (Annuel)", "https://buy.stripe.com/8x25kFgCIgvscYI2vN7AI00", use_container_width=True)
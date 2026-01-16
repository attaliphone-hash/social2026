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
    # Import Police Open Sans
    st.markdown(
        """
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Open+Sans:wght@400;600&display=swap');

        /* Cache les éléments par défaut de Streamlit */
        #MainMenu, header, footer {visibility: hidden;}
        [data-testid="stHeader"] {display: none;}
        .block-container { padding-top: 1rem !important; padding-bottom: 5rem !important;}

        /* --- 1. TITRE H1 (Baskerville - Aligné Gauche) --- */
        h1 {
            font-family: 'Baskerville', 'Libre Baskerville', 'Georgia', serif !important;
            color: #253E92 !important;
            font-size: 35px !important;
            font-weight: 700 !important;
            text-transform: uppercase !important;
            margin-top: 15px !important;
            margin-bottom: 20px !important;
            line-height: 1.1 !important;
            text-align: left !important;
        }

        /* --- 2. BOUTONS (STYLE UNIFIÉ) --- */
        /* On cible le bouton standard ET le bouton interne de l'uploader */
        button[data-testid="stBaseButton-secondary"],
        [data-testid="stFileUploader"] button {
            font-family: 'Open Sans', sans-serif !important;
            font-size: 12px !important;
            height: 40px !important;
            min-height: 40px !important;
            background-color: white !important;
            border: 1px solid #ccc !important;
            color: #333 !important;
            border-radius: 4px !important;
            box-shadow: 0 1px 2px rgba(0,0,0,0.05) !important;
            width: 100% !important;
            margin: 0 !important;

            /* Flexbox pour centrage parfait */
            display: flex !important;
            align-items: center !important;
            justify-content: center !important;
        }

        /* Effet au survol (Hover) */
        button[data-testid="stBaseButton-secondary"]:hover,
        [data-testid="stFileUploader"] button:hover {
            border-color: #253E92 !important;
            background-color: #f8f9fa !important;
            color: #253E92 !important;
        }

        /* --- 3. UPLOADER : OVERLAY CSS STABLE (sans toucher au DOM) --- */

        /* A) Dropzone : on supprime le padding et les instructions */
        [data-testid="stFileUploader"] section { padding: 0 !important; }
        [data-testid="stFileUploaderDropzoneInstructions"] { display: none !important; }
        [data-testid="stFileUploader"] div[data-testid="stFileUploaderInterface"] { margin: 0 !important; }

        /* B) Bouton uploader : parent en relative pour caler ::after */
        [data-testid="stFileUploader"] button {
            position: relative !important;      /* ✅ crucial : ancre le pseudo-élément */
            overflow: hidden !important;
            color: transparent !important;      /* masque le texte natif */
        }

        /* C) Texte injecté centré, non cliquable (le clic traverse) */
        [data-testid="stFileUploader"] button::after {
            content: "Charger un document pour analyse";
            position: absolute;
            inset: 0;                           /* remplit le bouton */
            display: flex;
            align-items: center;
            justify-content: center;
            font-family: 'Open Sans', sans-serif !important;
            font-size: 12px !important;
            color: #253E92 !important;
            pointer-events: none;
            text-decoration: underline;
            white-space: nowrap;
        }

        /* D) Hover : cohérent */
        [data-testid="stFileUploader"] button:hover::after {
            color: #253E92 !important;
            text-decoration: underline;
        }

        /* E) Nettoyage icône trombone / svg */
        [data-testid="stFileUploader"] button svg { display: none !important; }

        /* Ajustements de layout pour l'uploader */
        [data-testid="stFileUploader"] { line-height: 0; }

        /* --- 4. FOOTER (Aligné en haut) --- */
        .footer-text {
            font-family: 'Open Sans', sans-serif !important;
            font-size: 11px !important;
            color: #7A7A7A !important;
            margin: 0 !important;
            padding: 0 !important;
            white-space: nowrap;
        }

        /* Liens discrets */
        button[data-testid="stBaseButton-tertiary"] {
            font-family: 'Open Sans', sans-serif !important;
            font-size: 11px !important;
            color: #7A7A7A !important;
            background: transparent !important;
            border: none !important;
            padding: 0 5px !important;
            height: auto !important;
            text-decoration: none !important;
        }

        button[data-testid="stBaseButton-tertiary"]:hover {
            color: #253E92 !important;
            text-decoration: underline !important;
        }

        /* --- AUTRES --- */
        /* Bulles de chat */
        .stChatMessage {
            background-color: rgba(255,255,255,0.95);
            border-radius: 15px;
            padding: 10px;
            margin-bottom: 10px;
            border: 1px solid #e0e0e0;
        }

        /* Texte arguments */
        .assurance-text { font-size: 10px !important; color: #024c6f !important; text-align: left; line-height: 1.3; margin-bottom: 5px; }
        .assurance-title { font-weight: bold; color: #024c6f; font-size: 10px !important; }
        .assurance-desc { font-weight: normal; color: #444; font-size: 10px !important; }

        /* Alertes BOSS */
        .boss-alert-box { padding: 12px !important; border-radius: 8px !important; margin-bottom: 10px !important; font-size: 14px !important; }

        </style>
        """,
        unsafe_allow_html=True
    )

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


def render_subscription_cards():
    col_m, col_a = st.columns(2)
    with col_m:
        st.markdown(
            """<div style="background-color: #e3f2fd; border-radius: 10px; padding: 20px; text-align: center; border: 1px solid #bbdefb;"><h3>Mensuel</h3><h2>50 € HT <small>/ mois</small></h2><p>Sans engagement</p></div><br>""",
            unsafe_allow_html=True
        )
        st.button("S'abonner (Mensuel)", key="btn_sub_month", use_container_width=True)
    with col_a:
        st.markdown(
            """<div style="background-color: #e8f5e9; border-radius: 10px; padding: 20px; text-align: center; border: 1px solid #c8e6c9;"><h3>Annuel</h3><h2>500 € HT <small>/ an</small></h2><p>2 mois offerts</p></div><br>""",
            unsafe_allow_html=True
        )
        st.button("S'abonner (Annuel)", key="btn_sub_year", use_container_width=True)

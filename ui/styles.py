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
    # CSS EXACT + CSS UPLOAD DISCRET + TRADUCTION BOUTON
    st.markdown("""
        <style>
        #MainMenu {visibility: hidden;}
        header {visibility: hidden !important; height: 0px;}
        footer {visibility: hidden;}
        [data-testid="stHeader"] {display: none;}
        .block-container { padding-top: 1.5rem !important; }

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
            width: 250px !important; /* Largeur fixe pour accueillir le texte français */
        }

        /* On écrit le nouveau texte par-dessus */
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

        /* CITATIONS (sub) - Style Expert Social */
        sub {
            font-size: 0.75em !important;
            color: #666 !important;
            vertical-align: baseline !important;
            position: relative;
            top: -0.3em;
        }

        .assurance-text { font-size: 11px !important; color: #024c6f !important; text-align: left; display: block; line-height: 1.3; margin-bottom: 20px; }
        .assurance-title { font-weight: bold; color: #024c6f; display: inline; font-size: 11px !important; }
        .assurance-desc { font-weight: normal; color: #444; display: inline; font-size: 11px !important; }

        /* --- TYPOGRAPHIE DES TITRES (H1, H2, H3) --- */
        
        /* H1 : Le Grand Titre (ex: ExpertSocialPro V4) */
        h1 {
            color: #000066 !important;      /* Couleur (Bleu) */
            font-family: 'Baskerville', sans-serif !important;
            font-weight: 800 !important;    /* La Graisse (400=Normal, 700=Gras, 900=Très Gras) */
            font-size: 35px !important;   /* La Taille */
            text-transform: uppercase !important; /* Mettre 'uppercase' pour tout en MAJUSCULES *
            margin-bottom: 25px !important;
        }

        /* H2 : Les Sous-titres (ex: Dans les réponses de l'IA) */
        h2 {
            color: #1e3a8a !important;      /* Bleu un peu plus vif */
            font-family: 'Arial', sans-serif !important;
            font-weight: 600 !important;    /* Semi-bold */
            font-size: 1.8rem !important;
            border-bottom: 2px solid #e2e8f0; /* Une ligne grise fine sous le titre */
            padding-bottom: 8px !important;
            margin-top: 30px !important;
        }

        /* H3 : Les petits titres de section */
        h3 {
            color: #334155 !important;      /* Gris bleuté foncé */
            font-weight: bold !important;
            font-size: 1.4rem !important;
            margin-top: 15px !important;
        }

        /* --- OPTIMISATION MOBILE --- */
        @media (max-width: 768px) {
            .block-container { padding-top: 0.2rem !important; }
            iframe[title="st.iframe"] + br, hr + br, .stMarkdown br { display: none; }
            .assurance-text { margin-bottom: 2px !important; line-height: 1.1 !important; font-size: 10px !important; }
            h1 { font-size: 1.5rem !important; margin-top: 0px !important; }
        }

        .stExpander details summary p { font-size: 12px !important; color: #666 !important; }
        .stExpander { border: none !important; background-color: transparent !important; }
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
    cols = st.columns(5)
    for i, col in enumerate(cols):
        title, desc = ARGUMENTS_UNIFIES[i]
        col.markdown(
            f'<p class="assurance-text"><span class="assurance-title">{title}</span><span class="assurance-desc">{desc}</span></p>',
            unsafe_allow_html=True
        )

def show_legal_info():
    st.markdown("<br><br>", unsafe_allow_html=True)
    _, col_l, col_r, _ = st.columns([1, 2, 2, 1])

    with col_l:
        with st.expander("Mentions Légales"):
            st.markdown("""
<div style='font-size: 11px; color: #444; line-height: 1.4;'>
    <strong>ÉDITEUR :</strong><br>
    Le site <em>socialexpertfrance.fr</em> est édité par la BUSINESS AGENT AI.<br>
    Contact : sylvain.attal@businessagent-ai.com<br><br>
    <strong>PROPRIÉTÉ INTELLECTUELLE :</strong><br>
    L'ensemble de ce site relève de la législation française et internationale sur le droit d'auteur.
    L'architecture, le code et le design sont la propriété exclusive de BUSINESS AGENT AI®. La réutilisation des réponses générées est autorisée dans le cadre de vos missions professionnelles.<br><br>
    <strong>RESPONSABILITÉ :</strong><br>
    Les réponses sont fournies à titre indicatif et ne remplacent pas une consultation juridique. L'utilisateur de l'application doit en toute circonstance vérifier les réponses de l'IA qui n'engagent pas l'éditeur de l'application
</div>
""", unsafe_allow_html=True)

    with col_r:
        with st.expander("Politique de Confidentialité & Cookies (RGPD)"):
            st.markdown("""
<div style='font-size: 11px; color: #444; line-height: 1.4;'>
    <strong>PROTECTION DES DONNÉES & COOKIES :</strong><br>
    1. <strong>Gestion des Cookies :</strong> Un unique cookie technique est déposé pour permettre la reconnaissance de votre compte client et maintenir votre connexion active (session).<br>
    2. <strong>Absence de Traçage :</strong> Aucun cookie publicitaire ou traceur tiers n'est utilisé.<br>
    3. <strong>Données Volatiles :</strong> Le traitement est effectué en mémoire vive (RAM) et vos données ne servent jamais à entraîner les modèles d'IA.<br><br>
    <em>Conformité RGPD : Droit à l'oubli garanti par défaut.</em>
</div>
""", unsafe_allow_html=True)

# ==============================================================================
# CARTES D'ABONNEMENT (SANS ARGUMENTS)
# ==============================================================================
def render_subscription_cards():
    """
    Affiche les deux cartes d'abonnement (Mensuel/Bleu et Annuel/Vert)
    Version SANS ARGUMENTS pour éviter toute régression de signature.

    IMPORTANT :
    - Les URL de paiement doivent être créées côté app.py via Stripe (sessions dynamiques).
    - Ici, on ne met aucun lien Stripe "cs_live_..." statique.
    - On déclenche simplement des boutons Streamlit avec des keys stables.
    """
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
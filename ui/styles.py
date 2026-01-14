import streamlit as st
import os
import base64

from services.stripe_service import create_checkout_session

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

        /* REECRITURE DU TEXTE DU BOUTON */
        .stFileUploader button {
            border: 1px solid #ccc !important;
            background-color: white !important;
            color: transparent !important;
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

        /* CITATIONS */
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

        h1 { font-family: 'Helvetica Neue', sans-serif; text-shadow: 1px 1px 2px rgba(255,255,255,0.8); }

        /* --- OPTIMISATION MOBILE --- */
        @media (max-width: 768px) {
            .block-container { padding-top: 0.2rem !important; }
            iframe[title="st.iframe"] + br, hr + br, .stMarkdown br { display: none; }
            .assurance-text { margin-bottom: 2px !important; line-height: 1.1 !important; font-size: 10px !important; }
            h1 { font-size: 1.5rem !important; margin-top: 0px !important; }
        }

        .stExpander details summary p { font-size: 12px !important; color: #666 !important; }
        .stExpander { border: none !important; background-color: transparent !important; }

        /* --- CARTES ABONNEMENT --- */
        .sub-card {
            border-radius: 10px;
            padding: 18px;
            border: 1px solid rgba(0,0,0,0.08);
            height: 100%;
        }
        .sub-blue { background-color: #e3f2fd; border-color: #bbdefb; }
        .sub-green { background-color: #e8f5e9; border-color: #c8e6c9; }

        .sub-title-blue { color: #0d47a1; margin: 0; text-align:center; }
        .sub-title-green { color: #1b5e20; margin: 0; text-align:center; }

        .sub-price-blue { color: #1565c0; font-size: 24px; margin: 10px 0; text-align:center; font-weight: 700; }
        .sub-price-green { color: #2e7d32; font-size: 24px; margin: 10px 0; text-align:center; font-weight: 700; }

        .sub-note-blue { color: #0277bd; font-style: italic; font-size: 14px; text-align:center; margin-bottom: 10px; }
        .sub-note-green { color: #2e7d32; font-style: italic; font-size: 14px; text-align:center; margin-bottom: 10px; }

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

def render_subscription_cards(link_month=None, link_year=None):
    """
    Affiche les deux cartes d'abonnement.

    IMPORTANT :
    - Si link_month / link_year sont fournis : on affiche des liens (mode ancien).
    - Sinon : on crée une session Stripe à chaque clic (mode recommandé, évite les sessions expirées).
    """

    col_m, col_a = st.columns(2)

    with col_m:
        st.markdown("""
        <div class="sub-card sub-blue">
            <h3 class="sub-title-blue">Mensuel</h3>
            <div class="sub-price-blue">50 € HT <span style="font-size:14px; color:#555;">/ mois</span></div>
            <div class="sub-note-blue">Sans engagement</div>
        </div>
        """, unsafe_allow_html=True)

        if link_month:
            st.link_button("S'abonner (Mensuel)", link_month, use_container_width=True)
        else:
            if st.button("S'abonner (Mensuel)", use_container_width=True, key="sub_month"):
                url = create_checkout_session("Mensuel")
                if url:
                    st.markdown(f'<meta http-equiv="refresh" content="0;URL={url}">', unsafe_allow_html=True)

    with col_a:
        st.markdown("""
        <div class="sub-card sub-green">
            <h3 class="sub-title-green">Annuel</h3>
            <div class="sub-price-green">500 € HT <span style="font-size:14px; color:#555;">/ an</span></div>
            <div class="sub-note-green">2 mois offerts</div>
        </div>
        """, unsafe_allow_html=True)

        if link_year:
            st.link_button("S'abonner (Annuel)", link_year, use_container_width=True)
        else:
            if st.button("S'abonner (Annuel)", use_container_width=True, key="sub_year"):
                url = create_checkout_session("Annuel")
                if url:
                    st.markdown(f'<meta http-equiv="refresh" content="0;URL={url}">', unsafe_allow_html=True)

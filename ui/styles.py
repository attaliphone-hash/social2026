import streamlit as st
import os
import base64

# ==============================================================================
# 1. UTILITAIRES (Fonctions techniques)
# ==============================================================================
def get_base64(bin_file):
    """Permet de charger une image en fond d'écran via CSS"""
    if os.path.exists(bin_file):
        return base64.b64encode(open(bin_file, "rb").read()).decode()
    return ""

# ==============================================================================
# 2. DESIGN CSS (C'est ici qu'on change les couleurs, polices, boutons)
# ==============================================================================
def apply_pro_design():
    st.markdown("""
<style>
/* --- IMPORT DES POLICES --- */
@import url('https://fonts.googleapis.com/css2?family=Open+Sans:wght@400;600&display=swap');

/* --- NETTOYAGE INTERFACE STREAMLIT (Cacher menu, header, footer par défaut) --- */
#MainMenu, header, footer {visibility: hidden;}
[data-testid="stHeader"] {display: none;}
.block-container { padding-top: 1rem !important; padding-bottom: 5rem !important;}

/* --- TYPOGRAPHIE (H1 = Titre principal, H2 = Sous-titres) --- */
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

/* --- BOUTONS STANDARD & ZONE UPLOAD --- */
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

button[data-testid="stBaseButton-secondary"] {
    font-family: 'Open Sans', sans-serif !important;
    font-size: 12px !important;
    height: 40px !important;
    background-color: white !important;
    border: 1px solid #ccc !important;
    color: #333 !important;
    border-radius: 4px !important;
    width: 100% !important;
}

/* --- BOUTONS DU FOOTER (ROUGE & GRIS) --- */

/* Bouton "Pourquoi..." (Rouge) */
button[kind="primary"] {
    background-color: transparent !important;
    border: none !important;
    box-shadow: none !important;
    color: #d32f2f !important; /* Rouge vif */
    padding: 0px !important;
    text-decoration: underline !important; /* Souligné */
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

/* Boutons "Mentions" / "Confidentialité" (Gris) */
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

/* --- RESPONSIVE (MOBILE) & CHAT --- */
@media (max-width: 768px) {
    [data-testid="column"] {
        margin-bottom: -15px !important;
    }
    div[data-testid="stVerticalBlock"] > div {
        gap: 0.5rem !important;
    }
}

.stChatMessage { background-color: rgba(255,255,255,0.95); border-radius: 15px; border: 1px solid #e0e0e0; }
</style>
""", unsafe_allow_html=True)

    # Gestion de l'image de fond
    bg_data = get_base64('background.webp')
    if bg_data:
        st.markdown(f'<style>.stApp {{ background-image: url("data:image/webp;base64,{bg_data}"); background-size: cover; background-attachment: fixed; }}</style>', unsafe_allow_html=True)
    else:
        st.markdown("""<style>.stApp { background-image: url("https://www.transparenttextures.com/patterns/legal-pad.png"); background-size: cover; background-color: #f0f2f6; }</style>""", unsafe_allow_html=True)


# ==============================================================================
# 3. ARGUMENTS DE RÉASSURANCE (Barre sous le titre)
# ==============================================================================
def render_top_columns():
    import streamlit as st
    st.markdown("""
<style>
/* MOBILE */
.mobile-header-text { 
    display: block !important; 
    text-align: left;
    font-family: 'Source Sans Pro', sans-serif;
    font-size: 11px;
    color: #555;
    margin-bottom: 20px;
    line-height: 1.6;
    padding: 0 5px;
}
.desktop-container { display: none !important; }

/* DESKTOP */
@media (min-width: 768px) {
    .mobile-header-text { display: none !important; }
    .desktop-container { 
        display: flex !important;
        flex-direction: row;
        justify-content: space-between;
        gap: 20px;
        width: 100%;
        margin-bottom: 30px;
    }
}
.desktop-col { flex: 1; text-align: left; }
.arg-title { color: #024c6f; font-weight: 700; font-size: 13px; margin-bottom: 5px; }
.arg-desc { color: #555; font-size: 11px; line-height: 1.4; }
.sep { color: #ccc; margin: 0 5px; }
</style>

<div class="mobile-header-text">
    Données Certifiées 2026 <span class="sep">-</span>
    Sources Officielles <span class="sep">-</span>
    Mise à jour Agile <span class="sep">-</span>
    Traçabilité <span class="sep">-</span>
    Confidentialité
</div>

<div class="desktop-container">
    <div class="desktop-col"><div class="arg-title">Données Certifiées 2026 :</div><div class="arg-desc">Intégration prioritaire des nouveaux textes pour une précision chirurgicale.</div></div>
    <div class="desktop-col"><div class="arg-title">Sources officielles :</div><div class="arg-desc">Une analyse simultanée et croisée du BOSS, du Code du Travail, du Code de la Sécurité Sociale et des communiqués des organismes sociaux.</div></div>
    <div class="desktop-col"><div class="arg-title">Mise à Jour Agile :</div><div class="arg-desc">Notre base est actualisée en temps réel dès la publication de nouvelles circulaires ou réformes, garantissant une conformité permanente.</div></div>
    <div class="desktop-col"><div class="arg-title">Traçabilité Totale :</div><div class="arg-desc">Chaque réponse est systématiquement sourcée via une liste détaillée, permettant de valider instantanément le fondement juridique.</div></div>
    <div class="desktop-col"><div class="arg-title">Confidentialité Garantie :</div><div class="arg-desc">Aucun cookie publicitaire. Vos données sont traitées exclusivement en mémoire vive (RAM) et ne sont jamais utilisées pour entraîner des modèles d'IA.</div></div>
</div>
""", unsafe_allow_html=True)


# ==============================================================================
# 4. ABONNEMENTS (Cartes de prix)
# ==============================================================================
def render_subscription_cards():
    import streamlit as st
    col1, col2 = st.columns(2, gap="medium")
    with col1:
        st.markdown("""<div style="background-color: #e3f2fd; padding: 20px; border-radius: 10px; border: 1px solid #90caf9; height: 100%;"><h3 style="color: #1565c0; margin-top:0;">Mensuel</h3><h2 style="color: #0d47a1; font-size: 28px;">35 € <span style="font-size:16px; color:#555;">HT / MOIS</span></h2><p style="color: #333; font-size: 14px; margin-top: 10px;">Sans engagement</p><p style="color: #666; font-size: 13px;">Accès complet Expert Pro 2026</p></div>""", unsafe_allow_html=True)
        st.link_button("Je m'abonne (35€)", "https://buy.stripe.com/6oUeVf4U0enk1g07Q77AI01", use_container_width=True)
    with col2:
        st.markdown("""<div style="background-color: #e8f5e9; padding: 20px; border-radius: 10px; border: 1px solid #a5d6a7; height: 100%;"><h3 style="color: #2e7d32; margin-top:0;">Annuel</h3><h2 style="color: #1b5e20; font-size: 28px;">350 € <span style="font-size:16px; color:#555;">HT / AN</span></h2><p style="color: #333; font-size: 14px; margin-top: 10px;">2 mois offerts</p><p style="color: #666; font-size: 13px;">✅ Rentabilité immédiate</p></div>""", unsafe_allow_html=True)
        st.link_button("Je m'abonne (350€)", "https://buy.stripe.com/8x25kFgCIgvscYI2vN7AI00", use_container_width=True)


# ==============================================================================
# 5. MODALS & FOOTER (Textes Légaux et Manifeste)
# ==============================================================================

# --- POPUP : MANIFESTE (Le "Pourquoi") ---
@st.dialog("Pourquoi Expert Social Pro existe ?")
def modal_manifesto():
    st.markdown("""
    <style>
        .manifesto-box { font-family: 'Open Sans', sans-serif; color: #1e293b; line-height: 1.6; font-size: 14px; }
        .manifesto-title { color: #024c6f; font-size: 16px; font-weight: 700; margin-top: 20px; margin-bottom: 10px; border-bottom: 2px solid #e2e8f0; padding-bottom: 5px; }
        .manifesto-intro { font-size: 15px; font-weight: 600; color: #0f172a; margin-bottom: 15px; font-style: italic; }
        .manifesto-highlight { color: #b91c1c; font-weight: 700; }
        .manifesto-list { margin-left: 20px; margin-bottom: 15px; }
        .manifesto-strong { color: #0f172a; font-weight: 700; }
        .manifesto-check { color: #15803d; font-weight: bold; font-size: 15px; }
        .manifesto-punchline { margin-top: 20px; padding-top: 15px; border-top: 1px dashed #cbd5e1; text-align: center; font-size: 16px; font-weight: 800; color: #024c6f; }
    </style>
    <div class="manifesto-box">
        <p>Pendant des années, j’ai vu des professionnels RH passer des heures à chercher la bonne règle. Entre le BOSS, le Code du travail, l’URSSAF, les circulaires, les mises à jour…</p>
        
        <p>Le problème n’était pas le manque d’information.<br>
        <span class="manifesto-highlight">C’était l’excès d’information.</span></p>

        <div class="manifesto-title">Aujourd’hui :</div>
        <ul class="manifesto-list">
            <li>Tout existe,</li>
            <li>Tout est accessible,</li>
            <li>Mais rien n’est centralisé intelligemment.</li>
        </ul>
        <p>👉 <strong>Résultat :</strong> des décisions prises avec un doute permanent.</p>

        <div class="manifesto-title">Une seule mission</div>
        <p>J’ai créé Expert Social Pro pour répondre à une seule question :</p>
        <div class="manifesto-intro">“Est-ce que je peux décider sereinement ?”</div>

        <p style="margin-left: 10px;">
        ❌ Pas : <em>“Est-ce que j’ai trouvé un article ?”</em><br>
        ❌ Pas : <em>“Est-ce que ça ressemble à la bonne réponse ?”</em><br>
        <br>
        <span class="manifesto-check">✅ Mais : “Est-ce que c’est juridiquement sûr ?”</span>
        </p>

        <div class="manifesto-punchline">
            Expert Social Pro n’est pas une IA qui répond.<br>
            <span style="color: #b91c1c;">C’est une IA qui sécurise.</span>
        </div>
    </div>
    """, unsafe_allow_html=True)
# --- POPUP : MENTIONS LÉGALES (Sylvain Attal) ---
@st.dialog("Mentions Légales")
def modal_mentions():
    st.markdown(f"""
    <div style='font-size: 12px; color: #1e293b; font-family: sans-serif;'>
        <p>ÉDITEUR DU SITE<br>
        Le site <em>socialexpertfrance.fr</em> est édité par <strong>Sylvain Attal EI (BUSINESS AGENT AI)</strong>.<br>
        SIREN : 948253711<br>
        Contact : sylvain.attal@businessagent-ai.com</p>
        HÉBERGEMENT
        Google Cloud EMEA Limited<br>
        70 Sir John Rogerson’s Quay, Dublin 2, Irlande</p>
        LIMITATION DE RESPONSABILITÉ (IA)<br>
        Les réponses sont générées par une Intelligence Artificielle de pointe. 
        Ces informations sont indicatives et <strong>ne remplacent pas une consultation juridique</strong> 
        auprès d'un professionnel du droit. L'utilisateur doit, en toute circonstance, vérifier les réponses de l'outil. Celles-ci n'engagent pas l'éditeur.</p>
        PROPRIÉTÉ<br>
        Code source, architecture et design : Propriété exclusive de BUSINESS AGENT AI®.</p>
    </div>
    """, unsafe_allow_html=True)

# --- POPUP : RGPD & CONFIDENTIALITÉ ---
@st.dialog("Politique de Confidentialité")
def modal_rgpd():
    st.markdown(f"""
    <div style='font-size: 13px; color: #1e293b; font-family: sans-serif;'>
        <p><strong>PROTECTION DES DONNÉES :</strong></p>
        <ul>
            <li><strong>Cookies :</strong> Uniquement technique pour maintenir votre session.</li>
            <li><strong>Traçage :</strong> Aucun cookie publicitaire ou analytique tiers n'est déposé.</li>
            <li><strong>Données :</strong> Vos saisies sont traitées en mémoire vive et ne sont pas stockées ni utilisées pour l'entraînement de l'IA.</li>
        </ul>
    </div>
    """, unsafe_allow_html=True)

# --- FONCTION PRINCIPALE : AFFICHER LE FOOTER ---
def render_footer():
    """Affiche le footer avec le bouton Manifeste (rouge) et les liens légaux"""
    import streamlit as st
    
    st.markdown("<div style='margin-bottom: 5px;'></div>", unsafe_allow_html=True)
    
    # Colonnes : Manifeste (Large), Mentions, RGPD, Vide
    c_line = st.columns([2.2, 0.8, 0.8, 2.2], vertical_alignment="center")

    with c_line[0]: 
        # Type "primary" = ROUGE (grâce au CSS plus haut)
        if st.button("Pourquoi Expert Social Pro existe", type="primary", key="btn_manif"):
            modal_manifesto()

    with c_line[1]: 
        # Type "tertiary" = GRIS
        if st.button("Mentions Légales", type="tertiary", key="btn_mentions"):
            modal_mentions()

    with c_line[2]: 
        if st.button("Confidentialité", type="tertiary", key="btn_rgpd"):
            modal_rgpd()

    st.markdown("<hr style='margin-top:5px; margin-bottom:15px'>", unsafe_allow_html=True)
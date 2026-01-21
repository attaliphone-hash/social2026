import streamlit as st
import os
import base64

# ==============================================================================
# 1. CONFIGURATION ET DESIGN GLOBAL
# ==============================================================================
def get_base64(bin_file):
    if os.path.exists(bin_file):
        return base64.b64encode(open(bin_file, "rb").read()).decode()
    return ""

def apply_pro_design():
    st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Open+Sans:wght@400;600&display=swap');

#MainMenu, header, footer {visibility: hidden;}
[data-testid="stHeader"] {display: none;}
.block-container { padding-top: 1rem !important; padding-bottom: 5rem !important;}

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
}

.stChatMessage { background-color: rgba(255,255,255,0.95); border-radius: 15px; border: 1px solid #e0e0e0; }
</style>
""", unsafe_allow_html=True)

    bg_data = get_base64('background.webp')
    if bg_data:
        st.markdown(f'<style>.stApp {{ background-image: url("data:image/webp;base64,{bg_data}"); background-size: cover; background-attachment: fixed; }}</style>', unsafe_allow_html=True)
    else:
        st.markdown("""<style>.stApp { background-image: url("https://www.transparenttextures.com/patterns/legal-pad.png"); background-size: cover; background-color: #f0f2f6; }</style>""", unsafe_allow_html=True)


# ==============================================================================
# 2. ARGUMENTS DE RÉASSURANCE (CORRIGÉ - SANS INDENTATION)
# ==============================================================================
def render_top_columns():
    import streamlit as st
    
    # NOTE: Le code HTML ci-dessous est collé à gauche pour éviter que Streamlit
    # ne le considère comme un bloc de code (markdown code block).
    
    st.markdown("""
<style>
/* MOBILE */
.mobile-header-text { 
    display: block !important; 
    text-align: center;
    font-family: 'Source Sans Pro', sans-serif;
    font-size: 11px;
    color: #444; 
    margin-bottom: 15px;
    line-height: 1.4;
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

/* STYLE TEXTE */
.desktop-col {
    flex: 1;
    text-align: left;
}
.arg-title {
    color: #024c6f;
    font-weight: 700;
    font-size: 13px;
    margin-bottom: 5px;
}
.arg-desc {
    color: #555;
    font-size: 11px;
    line-height: 1.4;
}
.sep { color: #aaa; margin: 0 4px; }
</style>

<div class="mobile-header-text">
    <strong>Données Certifiées 2026</strong> <span class="sep">-</span>
    Sources Officielles <span class="sep">-</span>
    Mise à jour Agile <span class="sep">-</span>
    Traçabilité Totale <span class="sep">-</span>
    Confidentialité Garantie
</div>

<div class="desktop-container">
    <div class="desktop-col">
        <div class="arg-title">Données Certifiées 2026 :</div>
        <div class="arg-desc">Intégration prioritaire des nouveaux textes pour une précision chirurgicale.</div>
    </div>
    <div class="desktop-col">
        <div class="arg-title">Sources officielles :</div>
        <div class="arg-desc">Une analyse simultanée et croisée du BOSS, du Code du Travail, du Code de la Sécurité Sociale et des communiqués des organismes sociaux.</div>
    </div>
    <div class="desktop-col">
        <div class="arg-title">Mise à Jour Agile :</div>
        <div class="arg-desc">Notre base est actualisée en temps réel dès la publication de nouvelles circulaires ou réformes, garantissant une conformité permanente.</div>
    </div>
    <div class="desktop-col">
        <div class="arg-title">Traçabilité Totale :</div>
        <div class="arg-desc">Chaque réponse est systématiquement sourcée via une liste détaillée, permettant de valider instantanément le fondement juridique.</div>
    </div>
    <div class="desktop-col">
        <div class="arg-title">Confidentialité Garantie :</div>
        <div class="arg-desc">Aucun cookie publicitaire. Vos données sont traitées exclusivement en mémoire vive (RAM) et ne sont jamais utilisées pour entraîner des modèles d'IA.</div>
    </div>
</div>
""", unsafe_allow_html=True)


# ==============================================================================
# 3. ABONNEMENTS
# ==============================================================================
def render_subscription_cards():
    import streamlit as st
    
    col1, col2 = st.columns(2, gap="medium")
    
    with col1:
        st.markdown("""
        <div style="background-color: #e3f2fd; padding: 20px; border-radius: 10px; border: 1px solid #90caf9; height: 100%;">
            <h3 style="color: #1565c0; margin-top:0;">Mensuel</h3>
            <h2 style="color: #0d47a1; font-size: 28px;">35 € <span style="font-size:16px; color:#555;">HT / MOIS</span></h2>
            <p style="color: #333; font-size: 14px; margin-top: 10px;">Sans engagement</p>
            <p style="color: #666; font-size: 13px;">Accès complet Expert Pro 2026</p>
        </div>
        """, unsafe_allow_html=True)
        st.link_button("Je m'abonne (35€)", "https://buy.stripe.com/6oUeVf4U0enk1g07Q77AI01", use_container_width=True)

    with col2:
        st.markdown("""
        <div style="background-color: #e8f5e9; padding: 20px; border-radius: 10px; border: 1px solid #a5d6a7; height: 100%;">
            <h3 style="color: #2e7d32; margin-top:0;">Annuel</h3>
            <h2 style="color: #1b5e20; font-size: 28px;">350 € <span style="font-size:16px; color:#555;">HT / AN</span></h2>
            <p style="color: #333; font-size: 14px; margin-top: 10px;">2 mois offerts</p>
            <p style="color: #666; font-size: 13px;">✅ Rentabilité immédiate</p>
        </div>
        """, unsafe_allow_html=True)
        st.link_button("Je m'abonne (350€)", "https://buy.stripe.com/8x25kFgCIgvscYI2vN7AI00", use_container_width=True)
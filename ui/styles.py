import streamlit as st
import os
import base64

# ==============================================================================
# 1. UTILITAIRES & CONFIGURATION
# ==============================================================================
def get_base64(bin_file):
    if os.path.exists(bin_file):
        return base64.b64encode(open(bin_file, "rb").read()).decode()
    return ""

def apply_pro_design():
    """
    Applique le CSS global (Titres, Boutons, Fond).
    """
    st.markdown("""
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Open+Sans:wght@400;600&display=swap');

        /* Cache Header/Footer Streamlit */
        #MainMenu, header, footer {visibility: hidden;}
        [data-testid="stHeader"] {display: none;}
        .block-container { padding-top: 1rem !important; padding-bottom: 5rem !important;}

        /* --- TYPOGRAPHIE --- */
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

        /* --- INTERFACE UPLOAD --- */
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

        /* --- BOUTONS --- */
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

        /* --- CHAT & FOOTER --- */
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
    """, unsafe_allow_html=True) # <-- C'est ici que j'avais oublié les guillemets. C'est réparé.

    # Gestion du Background
    bg_data = get_base64('background.webp')
    if bg_data:
        st.markdown(f'<style>.stApp {{ background-image: url("data:image/webp;base64,{bg_data}"); background-size: cover; background-attachment: fixed; }}</style>', unsafe_allow_html=True)
    else:
        st.markdown("""<style>.stApp { background-image: url("https://www.transparenttextures.com/patterns/legal-pad.png"); background-size: cover; background-color: #f0f2f6; }</style>""", unsafe_allow_html=True)


# ==============================================================================
# 2. ARGUMENTS (MOBILE COMPACT / DESKTOP CLASSIQUE)
# ==============================================================================
def render_top_columns():
    """
    Affiche les arguments.
    - MOBILE : Ligne de texte compacte.
    - DESKTOP : 5 Colonnes natives avec texte simple (SANS BLOCS BLANCS).
    """
    import streamlit as st
    
    # 1. CSS POUR GÉRER L'AFFICHAGE (Mobile vs Desktop)
    st.markdown("""
    <style>
    /* PAR DÉFAUT (MOBILE) : On affiche le texte compact, on cache le wrapper Desktop */
    .mobile-header-text { 
        display: block !important; 
        text-align: center;
        font-family: 'Source Sans Pro', sans-serif;
        font-size: 11px;
        color: #444; 
        margin-bottom: 15px;
        line-height: 1.4;
    }
    .desktop-wrapper { display: none !important; }

    /* SUR DESKTOP (Écran > 768px) */
    @media (min-width: 768px) {
        .mobile-header-text { display: none !important; }
        .desktop-wrapper { display: block !important; }
    }

    /* STYLE DES TEXTES DESKTOP (Simple, pas de cartes) */
    .arg-title {
        color: #024c6f;
        font-weight: 700;
        font-size: 14px;
        margin-bottom: 4px;
        text-align: center;
    }
    .arg-desc {
        color: #666;
        font-size: 12px;
        line-height: 1.3;
        text-align: center;
    }
    .sep { color: #aaa; margin: 0 4px; }
    </style>
    """, unsafe_allow_html=True)

    # 2. HTML MOBILE (Visible seulement sur mobile)
    st.markdown("""
    <div class="mobile-header-text">
        <strong>Données Certifiées 2026</strong> <span class="sep">-</span>
        Sources Officielles <span class="sep">-</span>
        Mise à jour Agile <span class="sep">-</span>
        Traçabilité <span class="sep">-</span>
        Confidentialité
    </div>
    """, unsafe_allow_html=True)

    # 3. STRUCTURE DESKTOP (St.columns natif)
    # On enveloppe tout ça dans une div 'desktop-wrapper' pour pouvoir le cacher sur mobile
    st.markdown('<div class="desktop-wrapper">', unsafe_allow_html=True)
    
    # C'EST ICI QU'ON RETROUVE L'AFFICHAGE SIMPLE D'HIER (5 COLONNES)
    c1, c2, c3, c4, c5 = st.columns(5)

    with c1:
        st.markdown('<div class="arg-title">✅ Données 2026</div><div class="arg-desc">SMIC, Plafonds SS, Taux à jour.</div>', unsafe_allow_html=True)
    with c2:
        st.markdown('<div class="arg-title">⚖️ Sources</div><div class="arg-desc">Code du travail, BOSS, CCN.</div>', unsafe_allow_html=True)
    with c3:
        st.markdown('<div class="arg-title">⚡ Mise à Jour</div><div class="arg-desc">Intégration des nouveaux décrets.</div>', unsafe_allow_html=True)
    with c4:
        st.markdown('<div class="arg-title">🔍 Traçabilité</div><div class="arg-desc">Réponses sourcées juridiquement.</div>', unsafe_allow_html=True)
    with c5:
        st.markdown('<div class="arg-title">🔒 Confidentialité</div><div class="arg-desc">Aucun stockage. RGPD Compliant.</div>', unsafe_allow_html=True)

    st.markdown('</div>', unsafe_allow_html=True)


# ==============================================================================
# 3. ABONNEMENTS
# ==============================================================================
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
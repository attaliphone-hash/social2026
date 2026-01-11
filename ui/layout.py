import streamlit as st
import base64
import os

# --- GESTION DU DESIGN (CSS & HTML) ---

def apply_pro_design():
    # CSS V4 : Propre, net, et sources discrètes
    st.markdown("""
        <style>
        #MainMenu {visibility: hidden;}
        header {visibility: hidden !important; height: 0px;}
        footer {visibility: hidden;}
        .block-container { padding-top: 1.5rem !important; }
        
        /* Bulles de chat */
        .stChatMessage { 
            background-color: rgba(255,255,255,0.95); 
            border-radius: 15px; 
            padding: 10px; 
            border: 1px solid #e0e0e0; 
        }
        
        /* CITATIONS INTELLIGENTES (V4) */
        sub {
            font-size: 0.75em !important;
            color: #666 !important;
            font-style: italic;
        }
        
        /* Bannière Arguments */
        .assurance-text { font-size: 11px !important; color: #024c6f !important; line-height: 1.3; margin-bottom: 20px; }
        .assurance-title { font-weight: bold; color: #024c6f; }
        .assurance-desc { color: #444; }
        </style>
    """, unsafe_allow_html=True)

def render_header():
    # Arguments commerciaux
    cols = st.columns(4)
    args = [
        ("Données 2026", "Certifiées & à jour"),
        ("Moteur Hybride", "Règles strictes + IA"),
        ("Sources", "Traçabilité totale"),
        ("Confidentialité", "RAM volatile (No-Log)")
    ]
    for i, col in enumerate(cols):
        t, d = args[i]
        col.markdown(f'<p class="assurance-text"><span class="assurance-title">{t} :</span> <span class="assurance-desc">{d}</span></p>', unsafe_allow_html=True)
    
    st.markdown("<hr style='margin-top: 0; margin-bottom: 20px;'>", unsafe_allow_html=True)
    st.markdown("<h1 style='color: #024c6f; margin:0;'>Expert Social Pro <span style='font-size:0.6em; vertical-align:middle; color:#888;'>v4.0 Alpha</span></h1>", unsafe_allow_html=True)
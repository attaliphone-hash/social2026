import streamlit as st
import os
from ui.styles import apply_pro_design, render_top_columns, show_legal_info
from services.boss_watcher import check_boss_updates
from services.stripe_service import create_checkout_session

def check_password():
    """Gère l'authentification, l'espace Admin et l'écran de connexion/abonnement"""
    
    # 1. SI DÉJÀ CONNECTÉ
    if st.session_state.get("password_correct"):
        # -- SI ADMIN : VEILLE BOSS (Via le service dédié) --
        if st.session_state.get("is_admin"):
             with st.expander("🔒 Espace Admin - Veille BOSS (RSS)", expanded=True):
                 
                 # === GESTION ALERTE VUE / MASQUÉE ===
                 if "boss_alert_seen" not in st.session_state:
                     st.session_state.boss_alert_seen = False
                     
                 if not st.session_state.boss_alert_seen:
                     # AFFICHE L'ALERTE
                     st.markdown(check_boss_updates(), unsafe_allow_html=True)
                     
                     # BOUTON POUR MASQUER
                     c_dismiss, _ = st.columns([1.5, 3.5])
                     with c_dismiss:
                         if st.button("✅ Marquer comme vu / Masquer"):
                             st.session_state.boss_alert_seen = True
                             st.rerun()
                 else:
                     # MESSAGE COURT QUAND MASQUÉ
                     st.success("✅ Alerte lue")
                     if st.button("Réafficher la veille"):
                         st.session_state.boss_alert_seen = False
                         st.rerun()
                         
        return True
    
    # 2. SI NON CONNECTÉ (Ecran de Login)
    apply_pro_design()
    render_top_columns()
    
    st.markdown("<hr>", unsafe_allow_html=True)
    st.markdown("<h1 style='text-align: center; color: #024c6f;'>🔑 Accès Expert Social Pro V4</h1>", unsafe_allow_html=True)
    
    col_l, col_m, col_r = st.columns([1, 2, 1])
    with col_m:
        tab_login, tab_subscribe = st.tabs(["Se connecter", "S'abonner"])
        with tab_login:
            pwd = st.text_input("Code d'accès :", type="password")
            if st.button("Se connecter"):
                # Récupération des mots de passe
                admin_pwd = os.getenv("ADMIN_PASSWORD", "ADMIN2026")
                user_pwd = os.getenv("APP_PASSWORD", "DEFAUT_USER_123")
                
                if pwd == admin_pwd:
                    st.session_state.update({"password_correct": True, "is_admin": True})
                    st.rerun()
                elif pwd == user_pwd:
                    st.session_state.update({"password_correct": True, "is_admin": False})
                    st.rerun()
                else:
                    st.error("Code erroné.")
        
        # --- BOUTONS ABONNEMENT EN DEUX COLONNES ---
        with tab_subscribe:
            st.markdown("<br>", unsafe_allow_html=True)
            col_sub1, col_sub2 = st.columns(2)
            
            with col_sub1:
                st.info("📅 **Mensuel**\n\nFlexibilité totale.")
                if st.button("S'abonner (Mensuel)", use_container_width=True):
                    # APPEL DU SERVICE STRIPE
                    url = create_checkout_session("Mensuel")
                    if url: st.markdown(f'<meta http-equiv="refresh" content="0;URL={url}">', unsafe_allow_html=True)
            
            with col_sub2:
                st.success("🗓 **Annuel**\n\n2 mois offerts !")
                if st.button("S'abonner (Annuel)", use_container_width=True):
                    # APPEL DU SERVICE STRIPE
                    url = create_checkout_session("Annuel")
                    if url: st.markdown(f'<meta http-equiv="refresh" content="0;URL={url}">', unsafe_allow_html=True)
    
    show_legal_info()
    return False
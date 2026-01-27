import streamlit as st
import os
from core.config import Config

st.title("🕵️ Test Config COMPLET")

try:
    config = Config.from_env()

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("APIs & Base")
        # GOOGLE
        if config.google_api_key: st.success(f"✅ Google API : {config.google_api_key[:4]}...")
        else: st.error("❌ Google API manquante")

        # STRIPE
        if config.stripe_secret_key: st.success(f"✅ Stripe : {config.stripe_secret_key[:4]}...")
        else: st.error("❌ Stripe manquante")

        # SUPABASE
        if config.supabase_url: st.success(f"✅ Supabase URL : {config.supabase_url[:15]}...")
        else: st.error("❌ Supabase URL manquante")

    with col2:
        st.subheader("Accès & Codes")
        # ADMIN
        if config.admin_password: st.success(f"✅ Mot de passe Admin détecté")
        else: st.error("❌ Mot de passe Admin manquant")

        # USER PROMO
        if config.app_password: st.success(f"✅ Mot de passe App détecté")
        else: st.error("❌ Mot de passe App manquant")

        # CODE ANDRH
        if config.code_promo_andrh: st.success(f"✅ Code ANDRH détecté")
        else: st.error("❌ Code ANDRH manquant")

except Exception as e:
    st.error(f"Erreur critique dans la config : {e}")
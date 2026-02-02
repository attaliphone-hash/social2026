import os
import streamlit as st
from dotenv import load_dotenv

# Charge les variables locales (.env)
load_dotenv()

class Config:
    def __init__(self):
        # 1. APIs Externes
        self.google_api_key = os.getenv("GOOGLE_API_KEY")
        self.pinecone_api_key = os.getenv("PINECONE_API_KEY")
        self.stripe_api_key = os.getenv("STRIPE_SECRET_KEY")

        # 2. Base de données (Supabase)
        self.supabase_url = os.getenv("SUPABASE_URL")
        self.supabase_key = os.getenv("SUPABASE_KEY")

        # 3. Sécurité & Accès (SÉCURISÉ : Plus de valeurs par défaut en dur)
        self.admin_password = os.getenv("ADMIN_PASSWORD")
        
        # On récupère la liste des codes promo depuis la nouvelle variable PROMO_CODES
        self.promo_codes = os.getenv("PROMO_CODES", "").split(",")

        # ⚠️ Sécurité P0 : Bloquer si le mot de passe admin est absent du .env
        if not self.admin_password:
            st.error("🚨 CONFIGURATION CRITIQUE MANQUANTE : ADMIN_PASSWORD non défini.")
            st.stop()

    def get_supabase_client(self):
        """Initialise et retourne le client Supabase (La pièce manquante)"""
        from supabase import create_client
        if self.supabase_url and self.supabase_key:
            try:
                return create_client(self.supabase_url, self.supabase_key)
            except Exception as e:
                st.error(f"⚠️ Erreur de connexion Supabase : {e}")
                return None
        return None

    def is_production(self):
        """Détecte si l'app tourne sur Cloud Run"""
        return os.getenv("K_SERVICE") is not None
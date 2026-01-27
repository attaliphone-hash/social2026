import os
import streamlit as st
from dataclasses import dataclass
from dotenv import load_dotenv

# Charge les variables locales (.env) pour le mode Dev
load_dotenv()

@dataclass
class Config:
    """
    Configuration centrale complète.
    """
    # APIs Externes
    google_api_key: str
    pinecone_api_key: str
    stripe_secret_key: str
    
    # Base de données
    supabase_url: str
    supabase_key: str
    
    # Sécurité & Accès
    admin_password: str
    app_password: str
    code_promo_andrh: str
    
    @classmethod
    def from_env(cls):
        """
        Récupère la configuration (Priorité : Cloud Run ENV > Streamlit Secrets)
        """
        def get_var(key):
            # 1. Environnement Système (Docker / Cloud Run / .env local)
            value = os.getenv(key)
            if value:
                return value
            
            # 2. Fallback Streamlit Secrets (si utilisé)
            try:
                return st.secrets.get(key, "")
            except (FileNotFoundError, AttributeError):
                return ""

        return cls(
            google_api_key=get_var("GOOGLE_API_KEY"),
            pinecone_api_key=get_var("PINECONE_API_KEY"),
            stripe_secret_key=get_var("STRIPE_SECRET_KEY"),
            supabase_url=get_var("SUPABASE_URL"),
            supabase_key=get_var("SUPABASE_KEY"),
            admin_password=get_var("ADMIN_PASSWORD"),
            app_password=get_var("APP_PASSWORD"),
            code_promo_andrh=get_var("CODE_PROMO_ANDRH")
        )
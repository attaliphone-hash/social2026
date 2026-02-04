import os
import streamlit as st
from dotenv import load_dotenv

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

        # 3. Sécurité & Accès
        self.admin_password = os.getenv("ADMIN_PASSWORD")
        self.promo_codes = os.getenv("PROMO_CODES", "").split(",")

        # 4. PARAMÈTRES TECHNIQUES (AUDIT)
        self.PINECONE_TOP_K = 6              # Nombre de documents RAG
        self.RSS_TIMEOUT = 30                # Timeout Cloud Run
        self.RATE_LIMIT_DELAY = 2.0          # Anti-Spam (secondes)
        self.MAX_INPUT_LENGTH = 5000         # Sécurité input

        if not self.admin_password:
            st.error("🚨 CONFIGURATION CRITIQUE MANQUANTE : ADMIN_PASSWORD non défini.")
            st.stop()

    def get_supabase_client(self):
        from supabase import create_client
        if self.supabase_url and self.supabase_key:
            try:
                return create_client(self.supabase_url, self.supabase_key)
            except: return None
        return None

    def is_production(self):
        return os.getenv("K_SERVICE") is not None
import os
from dotenv import load_dotenv

# Charge les variables locales (.env)
load_dotenv()

class Config:
    def __init__(self):
        # 1. APIs Externes
        self.google_api_key = os.getenv("GOOGLE_API_KEY")
        self.pinecone_api_key = os.getenv("PINECONE_API_KEY")
        self.stripe_api_key = os.getenv("STRIPE_API_KEY")

        # 2. Base de données (Supabase)
        self.supabase_url = os.getenv("SUPABASE_URL")
        self.supabase_key = os.getenv("SUPABASE_KEY")

        # 3. Sécurité & Accès
        # ADMIN_PASSWORD pour l'admin, CODE_PROMO_GENERAL pour les invités
        self.admin_password = os.getenv("ADMIN_PASSWORD", "expert2026")
        self.app_password = os.getenv("CODE_PROMO_GENERAL", "SOCIAL2026")
        self.code_promo_andrh = os.getenv("CODE_PROMO_ANDRH", "ANDRH2026")

    def is_production(self):
        """Détecte si l'app tourne sur Cloud Run"""
        return os.getenv("K_SERVICE") is not None
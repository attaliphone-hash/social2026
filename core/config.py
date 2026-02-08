"""
==============================================================================
CONFIGURATION CENTRALE - SOCIAL EXPERT FRANCE
VERSION : 4.0
DATE : 08/02/2026
==============================================================================
"""

import os
import streamlit as st
from dotenv import load_dotenv

load_dotenv()


class Config:
    """Configuration centralisée de l'application."""
    
    def __init__(self):
        # =====================================================================
        # 1. APIs EXTERNES
        # =====================================================================
        self.google_api_key = os.getenv("GOOGLE_API_KEY")
        self.pinecone_api_key = os.getenv("PINECONE_API_KEY")
        self.stripe_api_key = os.getenv("STRIPE_SECRET_KEY")

        # =====================================================================
        # 2. BASE DE DONNÉES (Supabase)
        # =====================================================================
        self.supabase_url = os.getenv("SUPABASE_URL")
        self.supabase_key = os.getenv("SUPABASE_KEY")

        # =====================================================================
        # 3. SÉCURITÉ & ACCÈS
        # =====================================================================
        self.admin_password = os.getenv("ADMIN_PASSWORD")
        self.promo_codes = self._parse_promo_codes(os.getenv("PROMO_CODES", ""))

        # =====================================================================
        # 4. PARAMÈTRES TECHNIQUES (AUDIT V4.0)
        # =====================================================================
        self.PINECONE_TOP_K = 8              # Nombre de documents RAG (augmenté de 6 à 8)
        self.RSS_TIMEOUT = 30                # Timeout Cloud Run (secondes)
        self.RATE_LIMIT_DELAY = 2.0          # Anti-Spam (secondes entre requêtes)
        self.MAX_INPUT_LENGTH = 5000         # Longueur max input utilisateur
        self.MAX_CONTEXT_CHARS = 10000       # Limite contexte RAG (~2500 tokens)
        
        # =====================================================================
        # 5. MODÈLES IA
        # =====================================================================
        self.GEMINI_MODEL = "gemini-2.0-flash"
        self.EMBEDDING_MODEL = "models/gemini-embedding-001"
        self.LLM_TEMPERATURE = 0             # Déterministe pour l'audit

        # =====================================================================
        # 6. VALIDATION
        # =====================================================================
        self._validate_config()

    def _parse_promo_codes(self, codes_str: str) -> list:
        """Parse les codes promo depuis la variable d'environnement."""
        if not codes_str:
            return []
        return [code.strip() for code in codes_str.split(",") if code.strip()]

    def _validate_config(self):
        """Valide que les configurations critiques sont présentes."""
        if not self.admin_password:
            st.error("🚨 CONFIGURATION CRITIQUE MANQUANTE : ADMIN_PASSWORD non défini.")
            st.stop()
        
        if not self.google_api_key:
            st.warning("⚠️ GOOGLE_API_KEY non défini - L'IA ne fonctionnera pas.")
        
        if not self.pinecone_api_key:
            st.warning("⚠️ PINECONE_API_KEY non défini - La recherche documentaire ne fonctionnera pas.")

    def get_supabase_client(self):
        """Retourne un client Supabase connecté."""
        if not self.supabase_url or not self.supabase_key:
            return None
        
        try:
            from supabase import create_client
            return create_client(self.supabase_url, self.supabase_key)
        except ImportError:
            st.warning("⚠️ Module supabase non installé.")
            return None
        except Exception as e:
            st.error(f"❌ Erreur connexion Supabase: {e}")
            return None

    def is_production(self) -> bool:
        """Détecte si l'app tourne sur Cloud Run."""
        return os.getenv("K_SERVICE") is not None

    def get_environment(self) -> str:
        """Retourne l'environnement actuel."""
        if self.is_production():
            return "PRODUCTION"
        return "DEVELOPMENT"

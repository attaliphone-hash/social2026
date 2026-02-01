import streamlit as st
from datetime import date

class QuotaService:
    """
    Gère les limites d'utilisation (Quotas).
    - Invités : Limité (ex: 20 questions/session)
    - Abonnés/Admins/Promo : Illimité
    """
    
    def __init__(self):
        if "questions_count" not in st.session_state:
            st.session_state.questions_count = 0
            
    def check_quota(self, user_role):
        """
        Vérifie si l'utilisateur peut encore poser des questions.
        Retourne True si OK, False si bloqué.
        """
        # 1. Illimité pour les payants/admins/codes promo
        # CORRECTION : Ajout de "ADMIN" et "TRIAL" pour matcher AuthManager
        if user_role in ["ADMIN", "ADMINISTRATEUR", "PROMO", "PREMIUM", "SUBSCRIBER", "TRIAL", "ANDRH"]:
            return True
            
        # 2. Limité pour les invités standards (sans compte)
        LIMIT = 20
        if st.session_state.questions_count >= LIMIT:
            return False
            
        return True

    def increment(self):
        """Ajoute +1 au compteur"""
        st.session_state.questions_count += 1

    def get_count(self):
        return st.session_state.questions_count
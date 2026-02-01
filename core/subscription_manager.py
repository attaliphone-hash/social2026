import streamlit as st
from services.stripe_service import StripeService

class SubscriptionManager:
    """
    Gère les droits d'accès et vérifie si l'utilisateur peut utiliser l'app.
    Centralise la logique "Gratuit vs Payant".
    """
    
    def __init__(self):
        self.stripe_service = StripeService()

    def get_user_status(self, user_info):
        """
        Détermine le statut final de l'utilisateur.
        """
        if not user_info:
            return "GUEST"

        role = user_info.get("role", "STANDARD")
        email = user_info.get("email")

        # 1. Accès illimités (Admin et Codes Promo/Trial)
        # CORRECTION : Ajout de "ADMIN" et "TRIAL" pour matcher AuthManager
        if role in ["ADMIN", "ADMINISTRATEUR", "PROMO", "ANDRH", "TRIAL"]:
            return "PREMIUM"

        # 2. Abonnés (Vérification Stripe)
        if role == "SUBSCRIBER":
            if not self.stripe_service.config.stripe_api_key:
                return "PREMIUM"
                
            if self.stripe_service.verify_active_subscription(email):
                return "PREMIUM"
            else:
                return "EXPIRED"

        return "FREE"

    def render_subscription_blocker(self):
        """Affiche l'écran de blocage si l'accès est restreint"""
        st.warning("⚠️ **Accès Limité**")
        st.info("Cette fonctionnalité nécessite un abonnement actif ou un code privilège.")
        
        if st.session_state.user_info and 'email' in st.session_state.user_info:
            email = st.session_state.user_info['email']
            st.write("Souhaitez-vous souscrire à une offre ?")
            
            url = self.stripe_service.create_checkout_session("Abonnement", email)
            if url:
                st.link_button("Découvrir les offres", url)
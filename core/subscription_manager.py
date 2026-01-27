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
        Retourne : "PREMIUM", "FREE", ou "EXPIRED"
        """
        if not user_info:
            return "GUEST"

        role = user_info.get("role", "STANDARD")
        email = user_info.get("email")

        # 1. VIPs (Toujours Premium, pas d'appel Stripe)
        if role in ["ADMINISTRATEUR", "PROMO", "ANDRH"]:
            return "PREMIUM"

        # 2. Abonnés (Vérification Stripe en direct)
        if role == "SUBSCRIBER":
            if self.stripe_service.verify_active_subscription(email):
                return "PREMIUM"
            else:
                return "EXPIRED" # Abonnement fini ou paiement échoué

        # 3. Autres cas
        return "FREE"

    def render_subscription_blocker(self):
        """Affiche l'écran de blocage si pas abonné"""
        st.warning("⚠️ **Abonnement requis**")
        st.info("Votre abonnement n'est plus actif ou a expiré.")
        
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("### Mensuel\n9.90€ / mois")
            # Appel à Stripe pour lien mensuel
            url_mensuel = self.stripe_service.create_checkout_session("Mensuel", st.session_state.user_info['email'])
            if url_mensuel:
                st.link_button("S'abonner (Mensuel)", url_mensuel)
        
        with col2:
            st.markdown("### Annuel\n99€ / an (2 mois offerts)")
            # Appel à Stripe pour lien annuel
            url_annuel = self.stripe_service.create_checkout_session("Annuel", st.session_state.user_info['email'])
            if url_annuel:
                st.link_button("S'abonner (Annuel)", url_annuel)
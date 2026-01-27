import stripe
import streamlit as st
from core.config import Config

class StripeService:
    """
    Gère les paiements et abonnements via Stripe.
    """
    def __init__(self):
        # Utilisation de l'instanciation simple conforme au backup
        self.config = Config()
        if self.config.stripe_api_key:
            stripe.api_key = self.config.stripe_api_key
        else:
            print("⚠️ Stripe API Key manquante dans la configuration")

    def create_checkout_session(self, price_id, customer_email):
        """Crée une session de paiement Stripe"""
        try:
            # En local, on utilise localhost, en prod l'URL du domaine
            domain = "https://socialexpertfrance.fr" if self.config.is_production() else "http://localhost:8501"
            
            checkout_session = stripe.checkout.Session.create(
                customer_email=customer_email,
                payment_method_types=['card'],
                line_items=[{'price': price_id, 'quantity': 1}],
                mode='subscription',
                success_url=domain + "/?session_id={CHECKOUT_SESSION_ID}",
                cancel_url=domain + "/",
            )
            return checkout_session.url
        except Exception as e:
            print(f"Erreur Stripe: {e}")
            return None
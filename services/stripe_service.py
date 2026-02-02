import stripe
import os
import streamlit as st
from core.config import Config
from utils.helpers import logger  # ✅ Utilise le logger créé à l'étape 1

class StripeService:
    """
    Gère les paiements Stripe avec vérification anti-injection de prix.
    """
    def __init__(self):
        self.config = Config()
        
        # ✅ Liste blanche : récupère les IDs autorisés depuis Google Cloud
        self.VALID_PRICE_IDS = [
            os.getenv("STRIPE_PRICE_MONTHLY"),
            os.getenv("STRIPE_PRICE_YEARLY")
        ]
        
        if self.config.stripe_api_key:
            stripe.api_key = self.config.stripe_api_key
        else:
            logger.warning("Stripe Service: API Key manquante dans la configuration")

    def create_checkout_session(self, price_id, customer_email):
        """Crée une session Stripe après validation du prix"""
        
        # ✅ SÉCURITÉ : On vérifie que l'ID demandé est bien l'un des nôtres
        allowed_prices = [p for p in self.VALID_PRICE_IDS if p]
        if price_id not in allowed_prices:
            logger.error(f"SÉCURITÉ : Tentative de paiement bloquée pour l'ID non autorisé : {price_id}")
            return None

        try:
            # Choix automatique du domaine (Prod vs Local)
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
            logger.error(f"Stripe Service: Erreur lors de la création de session : {e}")
            return None
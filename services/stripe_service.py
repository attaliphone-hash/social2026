import stripe
import os
import streamlit as st

# Configuration de la clé API
stripe.api_key = os.getenv("STRIPE_SECRET_KEY")

def create_checkout_session(plan_type):
    """Crée une session de paiement Stripe pour l'abonnement"""
    # IDs Stripe (Hardcodés pour ta version actuelle)
    price_id = "price_1SnaTDQZ5ivv0RayXfKqvJ6I" if plan_type == "Mensuel" else "price_1SnaUOQZ5ivv0RayFnols3TI"
    
    try:
        checkout_session = stripe.checkout.Session.create(
            payment_method_types=['card'],
            line_items=[{'price': price_id, 'quantity': 1}],
            mode='subscription',
            success_url="https://socialexpertfrance.fr?payment=success",
            cancel_url="https://socialexpertfrance.fr?payment=cancel",
        )
        return checkout_session.url
    except Exception as e:
        st.error(f"Erreur Stripe : {e}")
        return None
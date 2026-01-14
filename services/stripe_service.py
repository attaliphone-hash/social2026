import os
import streamlit as st
import stripe
from dotenv import load_dotenv

def create_checkout_session(plan_type: str):
    """Crée une session de paiement Stripe pour l'abonnement (Checkout)."""

    # Chargement de sécurité
    load_dotenv()

    # Compatibilité : certains projets utilisent STRIPE_SECRET_KEY, d'autres STRIPE_API_KEY
    stripe.api_key = os.getenv("STRIPE_SECRET_KEY") or os.getenv("STRIPE_API_KEY")

    if not stripe.api_key:
        st.error("Clé Stripe manquante (STRIPE_SECRET_KEY ou STRIPE_API_KEY).")
        return None

    # IDs Stripe (Price)
    price_id = (
        "price_1SnaTDQZ5ivv0RayXfKqvJ6I" if plan_type == "Mensuel"
        else "price_1SnaUOQZ5ivv0RayFnols3TI"
    )

    try:
        checkout_session = stripe.checkout.Session.create(
            payment_method_types=["card"],
            line_items=[{"price": price_id, "quantity": 1}],
            mode="subscription",
            success_url="https://socialexpertfrance.fr?payment=success",
            cancel_url="https://socialexpertfrance.fr?payment=cancel",
        )
        return checkout_session.url

    except Exception as e:
        st.error(f"Erreur Stripe : {e}")
        return None

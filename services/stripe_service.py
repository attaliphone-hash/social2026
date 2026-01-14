import os
import stripe
import streamlit as st
from dotenv import load_dotenv

# IDs Stripe
PRICE_ID_MONTHLY = "price_1SnaTDQZ5ivv0RayXfKqvJ6I"
PRICE_ID_ANNUAL = "price_1SnaUOQZ5ivv0RayFnols3TI"

def _get_stripe_secret_key() -> str:
    """
    Rend le code robuste : accepte STRIPE_API_KEY (souvent utilisé) ou STRIPE_SECRET_KEY.
    """
    load_dotenv()
    return (
        os.getenv("STRIPE_API_KEY")  # si tu utilises déjà ce nom dans Cloud Run
        or os.getenv("STRIPE_SECRET_KEY")  # compatibilité avec l'ancien nom
        or ""
    )

def create_checkout_session(plan_type: str):
    """Crée une session de paiement Stripe pour l'abonnement (Mensuel/Annuel)."""
    stripe_key = _get_stripe_secret_key()
    if not stripe_key:
        st.error("Erreur Stripe : clé API manquante (STRIPE_API_KEY ou STRIPE_SECRET_KEY).")
        return None

    stripe.api_key = stripe_key

    price_id = PRICE_ID_MONTHLY if plan_type == "Mensuel" else PRICE_ID_ANNUAL

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

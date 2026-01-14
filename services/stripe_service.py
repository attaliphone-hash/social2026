import os
import stripe
import streamlit as st
from dotenv import load_dotenv

def _get_stripe_key():
    """
    Stripe nécessite une clé secrète.
    Pour compatibilité, on accepte :
    - STRIPE_SECRET_KEY (recommandé)
    - STRIPE_API_KEY (si c'est ce que tu as déjà dans ton .env)
    """
    load_dotenv()
    return os.getenv("STRIPE_SECRET_KEY") or os.getenv("STRIPE_API_KEY")

def create_checkout_session(plan_type: str):
    """Crée une session Stripe Checkout pour un abonnement (Mensuel / Annuel)."""
    stripe.api_key = _get_stripe_key()

    price_id = "price_1SnaTDQZ5ivv0RayXfKqvJ6I" if plan_type == "Mensuel" else "price_1SnaUOQZ5ivv0RayFnols3TI"

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

def manage_subscription_link(email: str):
    """
    Retourne l'URL du portail client Stripe (factures, carte, résiliation),
    ou None si introuvable.
    """
    stripe.api_key = _get_stripe_key()

    try:
        customers = stripe.Customer.list(email=email, limit=1)
        if customers and len(customers.data) > 0:
            customer_id = customers.data[0].id
            session = stripe.billing_portal.Session.create(
                customer=customer_id,
                return_url="https://socialexpertfrance.fr",
            )
            return session.url
    except Exception as e:
        # On évite de casser l'app : on retourne None et on log
        print(f"Erreur Stripe Portal : {e}")

    return None

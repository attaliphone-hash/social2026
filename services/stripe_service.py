import os
import stripe
import streamlit as st
from dotenv import load_dotenv

def _get_stripe_key():
    """
    Priorité à STRIPE_SECRET_KEY (recommandé).
    Fallback sur STRIPE_API_KEY pour éviter de casser un environnement existant.
    """
    load_dotenv()
    return os.getenv("STRIPE_SECRET_KEY") or os.getenv("STRIPE_API_KEY")

def create_checkout_session(plan_type):
    """Crée une session de paiement Stripe pour l'abonnement"""

    stripe_key = _get_stripe_key()
    if not stripe_key:
        st.error("Erreur Stripe : clé API manquante (STRIPE_SECRET_KEY).")
        return None

    stripe.api_key = stripe_key

    # IDs Stripe
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

def manage_subscription_link(email):
    """
    Crée un lien vers le portail Stripe (factures, carte, désabonnement).
    """
    stripe_key = _get_stripe_key()
    if not stripe_key:
        return None

    stripe.api_key = stripe_key

    try:
        customers = stripe.Customer.list(email=email, limit=1)
        if customers and len(customers.data) > 0:
            customer_id = customers.data[0].id
            session = stripe.billing_portal.Session.create(
                customer=customer_id,
                return_url="https://socialexpertfrance.fr"
            )
            return session.url
    except Exception as e:
        print(f"Erreur Stripe Portal: {e}")

    return None

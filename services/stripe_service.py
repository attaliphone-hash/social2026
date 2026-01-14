import stripe
import os
import streamlit as st
from dotenv import load_dotenv

def _configure_stripe():
    """Charge l'environnement et configure Stripe de façon sûre."""
    load_dotenv()
    # Clé secrète Stripe (obligatoire pour créer sessions + portail)
    stripe.api_key = os.getenv("STRIPE_SECRET_KEY")

def create_checkout_session(plan_type):
    """Crée une session de paiement Stripe pour l'abonnement."""
    _configure_stripe()

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

def manage_subscription_link(email):
    """Crée un lien vers le portail client Stripe (factures, carte, désabonnement)."""
    _configure_stripe()

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

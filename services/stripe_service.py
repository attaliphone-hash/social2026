import os
import stripe
import streamlit as st
from dotenv import load_dotenv

# IDs Stripe (inchangés)
PRICE_ID_MONTHLY = "price_1SnaTDQZ5ivv0RayXfKqvJ6I"
PRICE_ID_ANNUAL = "price_1SnaUOQZ5ivv0RayFnols3TI"

SUCCESS_URL = "https://socialexpertfrance.fr?payment=success"
CANCEL_URL = "https://socialexpertfrance.fr?payment=cancel"
RETURN_URL_PORTAL = "https://socialexpertfrance.fr"

def _ensure_stripe_key():
    """
    Garantit que Stripe a bien une clé secrète chargée.
    On accepte STRIPE_SECRET_KEY en priorité, sinon fallback sur STRIPE_API_KEY
    (au cas où tu aurais déjà ce nom dans ton environnement).
    """
    load_dotenv()

    secret = os.getenv("STRIPE_SECRET_KEY") or os.getenv("STRIPE_API_KEY")
    if not secret:
        raise ValueError("Clé Stripe manquante : STRIPE_SECRET_KEY (ou STRIPE_API_KEY).")

    stripe.api_key = secret

def create_checkout_session(plan_type: str):
    """Crée une session de paiement Stripe pour l'abonnement."""
    try:
        _ensure_stripe_key()

        price_id = PRICE_ID_MONTHLY if plan_type == "Mensuel" else PRICE_ID_ANNUAL

        checkout_session = stripe.checkout.Session.create(
            payment_method_types=["card"],
            line_items=[{"price": price_id, "quantity": 1}],
            mode="subscription",
            success_url=SUCCESS_URL,
            cancel_url=CANCEL_URL,
        )
        return checkout_session.url

    except Exception as e:
        st.error(f"Erreur Stripe : {e}")
        return None

def manage_subscription_link(email: str):
    """
    Crée un lien vers le portail client Stripe (factures, changement carte, résiliation).
    Retourne l'URL ou None.
    """
    try:
        _ensure_stripe_key()

        customers = stripe.Customer.list(email=email, limit=1)
        if customers and len(customers.data) > 0:
            customer_id = customers.data[0].id
            session = stripe.billing_portal.Session.create(
                customer=customer_id,
                return_url=RETURN_URL_PORTAL
            )
            return session.url

    except Exception as e:
        # On log, mais sans casser l'interface.
        print(f"Erreur Stripe Portal: {e}")

    return None

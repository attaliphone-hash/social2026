import os
import stripe
import streamlit as st
from dotenv import load_dotenv

# IDs Stripe (inchangés)
PRICE_ID_MONTHLY = "price_1SnaTDQZ5ivv0RayXfKqvJ6I"
PRICE_ID_ANNUAL = "price_1SnaUOQZ5ivv0RayFnols3TI"

SUCCESS_URL = "https://socialexpertfrance.fr?payment=success"
CANCEL_URL = "https://socialexpertfrance.fr?payment=cancel"
PORTAL_RETURN_URL = "https://socialexpertfrance.fr"

def _configure_stripe():
    """
    Configure Stripe avec UNE SEULE variable standard.
    On choisit STRIPE_SECRET_KEY (clé secrète) et on n'utilise plus STRIPE_API_KEY.
    """
    load_dotenv()
    secret_key = os.getenv("STRIPE_SECRET_KEY")
    if not secret_key:
        raise RuntimeError("Variable d'environnement manquante : STRIPE_SECRET_KEY")
    stripe.api_key = secret_key

def create_checkout_session(plan_type: str):
    """Crée une session de paiement Stripe pour l'abonnement (Mensuel / Annuel)"""
    try:
        _configure_stripe()

        plan_type_norm = (plan_type or "").strip().lower()
        if plan_type_norm == "mensuel":
            price_id = PRICE_ID_MONTHLY
        elif plan_type_norm == "annuel":
            price_id = PRICE_ID_ANNUAL
        else:
            st.error("Formule inconnue. Utilisez 'Mensuel' ou 'Annuel'.")
            return None

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
    Crée un lien vers le portail client Stripe pour :
    factures, changement de carte, résiliation, etc.
    """
    try:
        _configure_stripe()

        email = (email or "").strip()
        if not email:
            return None

        customers = stripe.Customer.list(email=email, limit=1)
        if customers and len(customers.data) > 0:
            customer_id = customers.data[0].id
            session = stripe.billing_portal.Session.create(
                customer=customer_id,
                return_url=PORTAL_RETURN_URL
            )
            return session.url

        return None

    except Exception as e:
        # Pas de st.error ici : c'est appelé depuis la sidebar, on évite les effets de bord.
        print(f"Erreur Stripe Portal: {e}")
        return None

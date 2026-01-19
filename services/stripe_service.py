import os
import stripe
import logging
from dotenv import load_dotenv

# 1. Configuration initiale
load_dotenv()
logger = logging.getLogger(__name__)

# Récupération de la clé (on privilégie SECRET_KEY)
stripe.api_key = os.getenv("STRIPE_SECRET_KEY") or os.getenv("STRIPE_API_KEY")

def create_checkout_session(plan_type: str, user_email: str):
    """
    Crée une session de paiement Stripe.
    IMPORTANT : On ajoute 'user_email' pour lier le paiement au bon client.
    """
    if not stripe.api_key:
        logger.error("Clé Stripe manquante.")
        return None

    # Tes IDs de prix (Je les ai gardés tels quels)
    price_id = (
        "price_1SnaTDQZ5ivv0RayXfKqvJ6I" if plan_type == "Mensuel"
        else "price_1SnaUOQZ5ivv0RayFnols3TI"
    )

    try:
        checkout_session = stripe.checkout.Session.create(
            # On pré-remplit l'email pour que Stripe crée le client proprement
            customer_email=user_email, 
            payment_method_types=["card"],
            line_items=[{"price": price_id, "quantity": 1}],
            mode="subscription",
            success_url="https://socialexpertfrance.fr?payment=success",
            cancel_url="https://socialexpertfrance.fr?payment=cancel",
        )
        return checkout_session.url

    except Exception as e:
        logger.error(f"Erreur lors de la création de session Stripe : {e}")
        return None

def verify_active_subscription(email: str) -> bool:
    """
    Vérifie si l'utilisateur possède un abonnement ACTIF.
    Retourne True si oui, False sinon.
    """
    if not email or not stripe.api_key:
        return False

    try:
        # Étape 1 : Retrouver le client Stripe via son email
        customers = stripe.Customer.list(email=email, limit=1)
        
        # Si aucun client n'existe avec cet email, pas d'abonnement possible
        if not customers.data:
            logger.info(f"Stripe : Aucun client trouvé pour l'email {email}")
            return False
            
        customer_id = customers.data[0].id
        
        # Étape 2 : Chercher les abonnements ACTIFS de ce client
        subscriptions = stripe.Subscription.list(
            customer=customer_id,
            status='active', # On ne veut que les actifs
            limit=1
        )
        
        is_active = len(subscriptions.data) > 0
        logger.info(f"Stripe : Abonnement pour {email} -> {'ACTIF' if is_active else 'INACTIF'}")
        
        return is_active

    except Exception as e:
        logger.error(f"Erreur lors de la vérification de l'abonnement pour {email} : {e}")
        # Par sécurité, en cas d'erreur technique, on bloque l'accès
        return False
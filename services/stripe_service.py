import stripe
import logging
from core.config import Config

# Configuration du logger
logger = logging.getLogger(__name__)

class StripeService:
    """
    Service de gestion des paiements Stripe.
    Intègre vos IDs de prix spécifiques et la vérification d'abonnement.
    """
    
    def __init__(self):
        # On utilise notre config centralisée (Cerveau)
        self.config = Config.from_env()
        
        if self.config.stripe_secret_key:
            stripe.api_key = self.config.stripe_secret_key
        else:
            logger.error("⚠️ Clé Stripe manquante dans la config")

    def create_checkout_session(self, plan_type: str, user_email: str):
        """
        Crée une session de paiement avec vos IDs produits spécifiques.
        """
        if not stripe.api_key:
            return None

        # VOS IDs de prix (Conservés tels quels)
        price_id = (
            "price_1SnaTDQZ5ivv0RayXfKqvJ6I" if plan_type == "Mensuel"
            else "price_1SnaUOQZ5ivv0RayFnols3TI"
        )

        try:
            checkout_session = stripe.checkout.Session.create(
                customer_email=user_email,
                payment_method_types=["card"],
                line_items=[{"price": price_id, "quantity": 1}],
                mode="subscription",
                allow_promotion_codes=True,
                # VOS URLs (Conservées telles quelles)
                success_url="https://socialexpertfrance.fr?payment=success",
                cancel_url="https://socialexpertfrance.fr?payment=cancel",
            )
            return checkout_session.url

        except Exception as e:
            logger.error(f"Erreur création session Stripe : {e}")
            return None

    def verify_active_subscription(self, email: str) -> bool:
        """
        Vérifie si l'utilisateur possède un abonnement ACTIF.
        (Votre logique exacte de vérification)
        """
        if not email or not stripe.api_key:
            return False

        try:
            # Étape 1 : Retrouver le client Stripe via son email
            customers = stripe.Customer.list(email=email, limit=1)
            
            # Si aucun client n'existe, pas d'abonnement
            if not customers.data:
                return False
                
            customer_id = customers.data[0].id
            
            # Étape 2 : Chercher les abonnements ACTIFS
            subscriptions = stripe.Subscription.list(
                customer=customer_id,
                status='active',
                limit=1
            )
            
            is_active = len(subscriptions.data) > 0
            return is_active

        except Exception as e:
            logger.error(f"Erreur vérification abonnement {email} : {e}")
            return False
            
    def create_customer_portal(self, user_email):
        """(Optionnel) Permet au client de gérer son abonnement"""
        try:
            customers = stripe.Customer.list(email=user_email, limit=1)
            if not customers.data:
                return None
            
            portal = stripe.billing_portal.Session.create(
                customer=customers.data[0].id,
                return_url="https://socialexpertfrance.fr"
            )
            return portal.url
        except Exception:
            return None
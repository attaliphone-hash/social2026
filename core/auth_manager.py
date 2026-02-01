import streamlit as st
from core.config import Config
from supabase import create_client, Client

class AuthManager:
    """
    Gère l'authentification des utilisateurs.
    Logique : Admin (RSS) vs Codes Promo (Pas RSS) vs Abonnés Supabase.
    """
    
    def __init__(self):
        # Récupération de la config
        self.config = Config()
        
        # Initialisation du client Supabase uniquement si les clés existent
        if self.config.supabase_url and self.config.supabase_key:
            try:
                self.supabase: Client = create_client(self.config.supabase_url, self.config.supabase_key)
            except Exception as e:
                print(f"⚠️ Erreur init Supabase: {e}")
                self.supabase = None
        else:
            self.supabase = None

    def login(self, email_or_code, password=None):
        """
        Tente de connecter l'utilisateur.
        Retourne un dictionnaire user_info si succès, None sinon.
        """
        
        # --- 1. TEST : EST-CE UN ADMIN ? (ACCÈS TOTAL + RSS) ---
        # Vérifie si le mot de passe correspond à celui dans secrets.toml OU si c'est le code Admin
        if email_or_code == self.config.admin_password or password == self.config.admin_password:
            return {
                "email": "ADMINISTRATEUR", 
                "role": "ADMIN", # <--- C'est ce rôle qui débloque le RSS dans app.py
                "name": "Administrateur"
            }

        # --- 2. TEST : CODE PROMO "SEPT À HUIT" (PAS DE RSS) ---
        if email_or_code == "SocialPro2026SeptHuit" or password == "SocialPro2026SeptHuit":
             return {
                 "email": "Invité Sept à Huit", 
                 "role": "TRIAL", # <--- Pas de RSS
                 "name": "Invité Découverte"
             }

        # --- 3. TEST : CODE "ANDRH VIP" (PAS DE RSS) ---
        if email_or_code == "ANDRH_2026_VIP" or password == "ANDRH_2026_VIP":
             return {
                 "email": "Membre ANDRH", 
                 "role": "TRIAL", # <--- Pas de RSS
                 "name": "Invité RH"
             }

        # --- 4. TEST : ABONNÉ SUPABASE (EMAIL / MOT DE PASSE) ---
        if self.supabase and "@" in str(email_or_code) and password:
            try:
                res = self.supabase.auth.sign_in_with_password({
                    "email": email_or_code, 
                    "password": password
                })
                if res.user:
                    # L'abonné a le rôle 'SUBSCRIBER', donc il ne voit pas le RSS Admin (sauf si vous changez la règle)
                    return {
                        "email": res.user.email, 
                        "role": "SUBSCRIBER", 
                        "name": "Abonné"
                    }
            except Exception as e:
                print(f"Refus connexion Supabase: {e}")
                return None
        
        return None

    def logout(self):
        """Déconnecte l'utilisateur proprement"""
        if "user_info" in st.session_state:
            del st.session_state.user_info
        
        if self.supabase:
            try:
                self.supabase.auth.sign_out()
            except: pass
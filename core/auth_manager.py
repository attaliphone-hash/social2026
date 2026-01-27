import streamlit as st
from core.config import Config
from supabase import create_client, Client

class AuthManager:
    """
    Gère l'authentification des utilisateurs.
    Centralise la logique de connexion (Admin, Promo, Abonnés Supabase).
    """
    
    def __init__(self):
        self.config = Config.from_env()
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
        # 1. TEST : EST-CE UN ADMIN ?
        # On vérifie si l'input correspond au mot de passe Admin
        if email_or_code == "ADMIN" or password == self.config.admin_password:
            if password == self.config.admin_password or email_or_code == self.config.admin_password:
                return {"email": "ADMINISTRATEUR", "role": "ADMINISTRATEUR"}

        # 2. TEST : EST-CE UN CODE PROMO (Utilisateur App) ?
        if email_or_code == self.config.app_password or password == self.config.app_password:
             return {"email": "Utilisateur Promo", "role": "PROMO"}

        # 3. TEST : EST-CE UN MEMBRE ANDRH ?
        if email_or_code == self.config.code_promo_andrh or password == self.config.code_promo_andrh:
             return {"email": "Membre ANDRH (Invité)", "role": "ANDRH"}

        # 4. TEST : EST-CE UN ABONNÉ (SUPABASE) ?
        # Si on a un email (avec @) et un mot de passe, on interroge Supabase
        if self.supabase and "@" in str(email_or_code) and password:
            try:
                res = self.supabase.auth.sign_in_with_password({
                    "email": email_or_code, 
                    "password": password
                })
                if res.user:
                    return {"email": res.user.email, "role": "SUBSCRIBER"}
            except Exception as e:
                # Erreur classique (mauvais mot de passe ou user inconnu)
                print(f"Refus connexion Supabase: {e}")
                return None
        
        return None

    def logout(self):
        """Déconnecte l'utilisateur proprement"""
        st.session_state.authenticated = False
        st.session_state.user_info = None
        if self.supabase:
            try:
                self.supabase.auth.sign_out()
            except: pass
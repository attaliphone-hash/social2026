import streamlit as st
import os
from dotenv import load_dotenv

# Charge les variables pour lire votre .env actuel
load_dotenv()

class AuthManager:
    def __init__(self):
        # On récupère Supabase via la config si dispo
        self.supabase = None
        if hasattr(st.session_state, 'config'):
            self.supabase = st.session_state.config.get_supabase_client()
            
        if "user_info" not in st.session_state:
            st.session_state.user_info = None

    def login(self, email_or_code, password=None):
        """
        Gère la connexion selon l'onglet utilisé.
        """

        # --- CAS 1 : ONGLET "J'AI UN CODE DÉCOUVERTE" (Code seul) ---
        # Ici, email_or_code contient le CODE. password est vide.
        
        # 1. Test du Code "SocialPro..." (APP_PASSWORD dans votre .env)
        if email_or_code == os.getenv("APP_PASSWORD"):
             return {
                 "email": "Invité Découverte", 
                 "role": "TRIAL", # 🔒 PAS DE RSS, PAS DE DEBUG
                 "name": "Invité Découverte",
                 "id": "guest_sp"
             }

        # 2. Test du Code "ANDRH..." (CODE_PROMO_ANDRH dans votre .env)
        if email_or_code == os.getenv("CODE_PROMO_ANDRH"):
             return {
                 "email": "Invité RH", 
                 "role": "TRIAL", # 🔒 PAS DE RSS, PAS DE DEBUG
                 "name": "Invité RH",
                 "id": "guest_andrh"
             }

        # --- CAS 2 : ONGLET "JE SUIS ABONNÉ" (Email + Mot de passe) ---
        
        # 3. Test ADMIN (Master Password)
        # Si le mot de passe saisi est celui de l'ADMIN (ADMIN_PASSWORD dans .env)
        # Peu importe l'email saisi, ça connecte en Admin.
        if password == os.getenv("ADMIN_PASSWORD"):
            return {
                "email": "ADMINISTRATEUR", 
                "role": "ADMIN", # ✅ LE SEUL QUI VOIT TOUT (RSS + DEBUG)
                "name": "Administrateur",
                "id": "admin_001"
            }

        # 4. Test ABONNÉ CLASSIQUE (Supabase)
        if self.supabase and password:
            try:
                res = self.supabase.auth.sign_in_with_password({
                    "email": email_or_code,
                    "password": password
                })
                if res.user:
                    return {
                        "email": res.user.email,
                        "role": "SUBSCRIBER", # 🔒 PAS DE RSS, PAS DE DEBUG
                        "name": "Abonné",
                        "id": res.user.id
                    }
            except Exception:
                return None # Erreur (mauvais mot de passe ou email)
        
        return None

    def logout(self):
        if self.supabase:
            try:
                self.supabase.auth.sign_out()
            except: pass
        st.session_state.user_info = None
        st.rerun()
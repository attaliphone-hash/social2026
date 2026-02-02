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
        # Ici, email_or_code contient le CODE saisi par l'utilisateur.
        code_saisi = str(email_or_code).strip()

        # On récupère la liste unique que vous avez créée sur Google Run
        raw_promo_codes = os.getenv("PROMO_CODES", "")
        valid_codes = [c.strip() for c in raw_promo_codes.split(",") if c.strip()]

        if code_saisi in valid_codes:
            # On garde votre logique de noms personnalisés selon le contenu du code
            display_name = "Invité RH" if "ANDRH" in code_saisi else "Invité Découverte"
            
            return {
                "email": f"Code: {code_saisi}", 
                "role": "TRIAL", 
                "name": display_name,
                "id": f"guest_{code_saisi}"
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
import streamlit as st
import time

class QuotaService:
    def __init__(self):
        if "questions_count" not in st.session_state:
            st.session_state.questions_count = 0
        
        # ✅ OPTIMISATION CLAUDE : On utilise la config déjà chargée en session
        # On met une valeur par défaut (2.0) par sécurité si config n'est pas prêt
        if hasattr(st.session_state, 'config'):
            self.rate_limit_delay = st.session_state.config.RATE_LIMIT_DELAY
        else:
            self.rate_limit_delay = 2.0
            
    def check_quota(self, user_role):
        # 1. RATE LIMITING (Anti-Spam)
        if user_role != "ADMIN":
            last_time = st.session_state.get("last_request_time", 0)
            now = time.time()
            if now - last_time < self.rate_limit_delay:
                st.toast("🧘 Doucement ! Laissez-moi réfléchir...", icon="⏳")
                return False
            st.session_state["last_request_time"] = now

        # 2. VÉRIFICATION QUOTA CLASSIQUE
        if user_role in ["ADMIN", "ADMINISTRATEUR", "PROMO", "PREMIUM", "SUBSCRIBER", "TRIAL", "ANDRH"]:
            return True
            
        LIMIT = 20
        if st.session_state.questions_count >= LIMIT:
            return False
            
        return True

    def increment(self):
        st.session_state.questions_count += 1

    def get_count(self):
        return st.session_state.questions_count
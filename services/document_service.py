import io
import pypdf  # ✅ C'est la librairie que vous avez déjà dans requirements
import streamlit as st

class DocumentService:
    def extract_text(self, uploaded_file):
        """Extrait le texte d'un fichier uploadé (PDF ou TXT)"""
        # Sécurité 1 : Si pas de fichier, on renvoie vide tout de suite
        if not uploaded_file:
            return ""
        
        try:
            # CAS 1 : C'est un PDF
            if uploaded_file.type == "application/pdf":
                text = ""
                # On utilise pypdf comme vous l'avez installé
                reader = pypdf.PdfReader(uploaded_file)
                
                # On boucle sur les pages
                for page in reader.pages:
                    extracted = page.extract_text()
                    if extracted:
                        text += extracted + "\n"
                
                # Sécurité 2 : Si le texte est vide (PDF scanné / Image)
                if not text.strip():
                    st.warning("⚠️ Ce PDF semble être une image (scan). Je ne peux pas lire le texte.")
                
                return text

            # CAS 2 : C'est un fichier Texte (.txt)
            elif uploaded_file.type == "text/plain":
                # On décode les octets en texte
                return uploaded_file.getvalue().decode("utf-8")

            # CAS 3 : Autre chose
            else:
                st.error(f"❌ Format non supporté : {uploaded_file.type}")
                return ""

        except Exception as e:
            # Sécurité 3 : On affiche l'erreur réelle pour comprendre
            st.error(f"❌ Erreur Technique de lecture : {e}")
            return ""
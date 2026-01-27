import io
import pypdf  # ✅ CORRECTION : On utilise la librairie moderne installée
import streamlit as st

class DocumentService:
    """
    Service responsable de l'extraction de texte depuis des fichiers.
    Supporte : PDF, TXT.
    """
    
    def extract_text(self, uploaded_file):
        """
        Détecte le type de fichier et extrait le texte.
        Retourne : str (le texte complet) ou None si erreur.
        """
        if uploaded_file is None:
            return None
            
        try:
            # Cas 1 : Fichier Texte (.txt)
            if uploaded_file.type == "text/plain":
                # On décode en utf-8
                return uploaded_file.getvalue().decode("utf-8")
                
            # Cas 2 : Fichier PDF (.pdf)
            elif uploaded_file.type == "application/pdf":
                return self._extract_from_pdf(uploaded_file)
            
            else:
                st.error("Format de fichier non supporté. Utilisez PDF ou TXT.")
                return None

        except Exception as e:
            print(f"❌ Erreur extraction document : {e}")
            st.error(f"Erreur de lecture du fichier : {e}")
            return None

    def _extract_from_pdf(self, uploaded_file):
        """Méthode interne pour lire les PDF"""
        # ✅ CORRECTION ICI AUSSI : pypdf au lieu de PyPDF2
        pdf_reader = pypdf.PdfReader(uploaded_file)
        text = ""
        for page in pdf_reader.pages:
            page_text = page.extract_text()
            if page_text:
                text += page_text + "\n"
        return text
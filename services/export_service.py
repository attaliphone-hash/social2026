from fpdf import FPDF
import datetime
import os
import re
from utils.helpers import logger

class ExportService:
    def __init__(self):
        self.logo_path = "avatar-logo.png"

    def _clean_text_for_pdf(self, text):
        """
        Nettoyage Hybride : Robuste + Respect de la mise en page.
        """
        if text is None:
            return ""
        
        # 1. Sécurité Type
        text = str(text)
        
        # 2. Préservation de la structure
        structure_replacements = {
            "</h1>": "\n\n", "</h2>": "\n\n", "</h3>": "\n\n", "</h4>": "\n\n",
            "</p>": "\n", "</div>": "\n", "<br>": "\n", "<br/>": "\n",
            "<li>": "- ", "</li>": "\n"
        }
        for tag, replacement in structure_replacements.items():
            text = text.replace(tag, replacement)

        # 3. Nettoyage agressif HTML
        text = re.sub(r'<[^>]+>', '', text)

        # 4. Nettoyage des entités HTML
        entity_replacements = {
            "&nbsp;": " ", "&euro;": "Euros", "&amp;": "&",
            "&lt;": "<", "&gt;": ">", "&#39;": "'", "&quot;": '"'
        }
        for entity, char in entity_replacements.items():
            text = text.replace(entity, char)

        # 5. Nettoyage des espaces multiples
        text = re.sub(r'\n{3,}', '\n\n', text)
        
        # 6. Encodage Latin-1 (Gestion des émojis par remplacement)
        return text.encode('latin-1', 'replace').decode('latin-1')

    def generate_pdf(self, user_query, ai_response):
        """Génère un PDF binaire prêt à télécharger."""
        try:
            pdf = FPDF()
            pdf.add_page()
            
            # Nettoyage
            clean_query = self._clean_text_for_pdf(user_query)
            clean_response = self._clean_text_for_pdf(ai_response)

            # 1. En-tête
            if os.path.exists(self.logo_path):
                try:
                    pdf.image(self.logo_path, 10, 8, 25)
                except Exception as e:
                    logger.warning(f"Export PDF : Logo ignoré ({e})")
            
            pdf.set_font("helvetica", "B", 16)
            pdf.set_text_color(37, 62, 146) 
            pdf.cell(0, 10, "SOCIAL EXPERT FRANCE", ln=True, align="R")
            
            pdf.set_font("helvetica", "I", 10)
            pdf.set_text_color(100, 100, 100)
            date_str = datetime.datetime.now().strftime("%d/%m/%Y %H:%M")
            pdf.cell(0, 10, f"Simulation du {date_str}", ln=True, align="R")
            
            pdf.ln(20)
            
            # 2. Objet
            pdf.set_fill_color(240, 248, 255)
            pdf.set_font("helvetica", "B", 12)
            pdf.set_text_color(0, 0, 0)
            pdf.cell(0, 10, " OBJET DE LA CONSULTATION :", ln=True, fill=True)
            pdf.set_font("helvetica", "", 11)
            pdf.multi_cell(0, 7, clean_query)
            
            pdf.ln(10)
            
            # 3. Réponse
            pdf.set_font("helvetica", "B", 12)
            pdf.set_text_color(37, 62, 146)
            pdf.cell(0, 10, "ANALYSE ET SIMULATION :", ln=True)
            
            pdf.set_font("helvetica", "", 10)
            pdf.set_text_color(0, 0, 0)
            pdf.multi_cell(0, 6, clean_response)
            
            pdf.ln(10)
            
            # 4. Disclaimer
            pdf.set_font("helvetica", "I", 8)
            pdf.set_text_color(120, 120, 120)
            disclaimer = (
                "AVERTISSEMENT : Ce compte-rendu est une simulation automatisée établie selon les barèmes 2026. "
                "Il est exclusivement destiné à faciliter la réflexion de l'utilisateur et ne constitue en aucun cas "
                "un acte de conseil juridique."
            )
            pdf.multi_cell(0, 5, self._clean_text_for_pdf(disclaimer), align="C")
            
            # 👇👇👇 LA CORRECTION EST ICI 👇👇👇
            # On convertit le 'bytearray' de fpdf2 en 'bytes' standard pour Streamlit
            return bytes(pdf.output())

        except Exception as e:
            logger.error(f"ERREUR CRITIQUE SERVICE PDF : {e}")
            return None
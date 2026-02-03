from fpdf import FPDF
import datetime
import os
import re

class ExportService:
    def __init__(self):
        self.logo_path = "avatar-logo.png"

    def _clean_text_for_pdf(self, text):
        """
        Nettoie le texte pour FPDF (Latin-1) et supprime les balises HTML.
        Gère aussi la conversion forcée en string.
        """
        if text is None:
            return ""
        
        # 1. Force le type String
        text = str(text)
        
        # 2. Nettoyage HTML basique
        replacements = {
            "<h4>": "\n", "</h4>": "\n",
            "<ul>": "", "</ul>": "",
            "<li>": "- ", "</li>": "\n",
            "<strong>": "", "</strong>": "",
            "<br>": "\n", "<p>": "", "</p>": "\n",
            "<em>": "", "</em>": "",
            "</div>": "\n",
            "&nbsp;": " ", "&euro;": "Euros"
        }
        
        for tag, replacement in replacements.items():
            text = text.replace(tag, replacement)

        # 3. Suppression des balises div stylisées (Nettoyage agressif)
        text = re.sub(r'<div[^>]*>', '\n', text)
        
        # 4. Encodage : Remplacement des caractères non supportés par Latin-1
        # FPDF standard ne supporte pas les émojis -> On les supprime ou remplace
        # Cette ligne encode en latin-1 en ignorant les erreurs, puis décode pour avoir une string propre
        return text.encode('latin-1', 'replace').decode('latin-1')

    def generate_pdf(self, user_query, ai_response):
        pdf = FPDF()
        pdf.add_page()
        
        # Nettoyage préventif des entrées
        clean_query = self._clean_text_for_pdf(user_query)
        clean_response = self._clean_text_for_pdf(ai_response)

        # 1. En-tête avec Logo
        if os.path.exists(self.logo_path):
            try:
                pdf.image(self.logo_path, 10, 8, 25)
            except:
                pass # Si l'image est corrompue, on continue sans logo
        
        pdf.set_font("helvetica", "B", 16)
        pdf.set_text_color(37, 62, 146) # Bleu #253E92
        pdf.cell(0, 10, "SOCIAL EXPERT FRANCE", ln=True, align="R")
        
        pdf.set_font("helvetica", "I", 10)
        pdf.set_text_color(100, 100, 100)
        date_str = datetime.datetime.now().strftime("%d/%m/%Y %H:%M")
        pdf.cell(0, 10, f"Simulation générée le {date_str}", ln=True, align="R")
        
        pdf.ln(20)
        
        # 2. Objet de la demande
        pdf.set_fill_color(240, 248, 255)
        pdf.set_font("helvetica", "B", 12)
        pdf.set_text_color(0, 0, 0)
        pdf.cell(0, 10, " OBJET DE LA CONSULTATION :", ln=True, fill=True)
        pdf.set_font("helvetica", "", 11)
        # Utilisation de la version nettoyée
        pdf.multi_cell(0, 10, clean_query)
        
        pdf.ln(10)
        
        # 3. Analyse et Résultats
        pdf.set_font("helvetica", "B", 12)
        pdf.set_text_color(37, 62, 146)
        pdf.cell(0, 10, "ANALYSE JURIDIQUE ET SIMULATION :", ln=True)
        
        pdf.set_font("helvetica", "", 11)
        pdf.set_text_color(0, 0, 0)
        
        # Utilisation de la version nettoyée
        pdf.multi_cell(0, 7, clean_response)
        
        pdf.ln(10)
        
        # 4. Pied de page / Clause de non-responsabilité
        pdf.ln(5)
        pdf.set_font("helvetica", "I", 8)
        pdf.set_text_color(120, 120, 120)
        
        disclaimer = (
            "AVERTISSEMENT : Ce compte-rendu est une simulation automatisée établie selon les barèmes 2026. "
            "Il est exclusivement destiné à faciliter la réflexion de l'utilisateur et ne constitue en aucun cas "
            "un acte de conseil juridique. Social Expert France ne saurait être tenu pour responsable de l'usage "
            "fait de ces calculs."
        )
        # Nettoyage aussi du disclaimer pour être sûr (encodage)
        pdf.multi_cell(0, 5, self._clean_text_for_pdf(disclaimer), align="C")
        
        return pdf.output(dest='S').encode('latin-1') 
        # Note: dest='S' retourne une string, qu'on encode en bytes pour st.download_button
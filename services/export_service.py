from fpdf import FPDF
import datetime
import os
import re
from utils.helpers import logger

class SocialExpertPDF(FPDF):
    """
    Classe personnalisée pour gérer le design (Header/Footer) sur toutes les pages.
    """
    def header(self):
        # Logo
        logo_path = "avatar-logo.png"
        if os.path.exists(logo_path):
            try:
                self.image(logo_path, 10, 8, 20)
            except:
                pass
        
        # Titre Entreprise (Aligné à Droite) - On garde une taille modérée pour l'en-tête
        self.set_font('Times', 'B', 12)
        self.set_text_color(37, 62, 146) # Bleu Social Expert
        self.cell(0, 6, 'SOCIAL EXPERT FRANCE', ln=True, align='R')
        
        # Sous-titre date
        self.set_font('Times', 'I', 10)
        self.set_text_color(120, 120, 120) # Gris
        date_str = datetime.datetime.now().strftime("%d/%m/%Y")
        self.cell(0, 5, f'Dossier généré le {date_str}', ln=True, align='R')
        
        # Ligne de séparation bleue
        self.set_draw_color(37, 62, 146)
        self.set_line_width(0.5)
        self.line(10, 25, 200, 25)
        self.ln(20) # Saut de ligne après le header

    def footer(self):
        # Positionnement à 1.5 cm du bas
        self.set_y(-15)
        self.set_font('Times', 'I', 9)
        self.set_text_color(128)
        # Numéro de page
        self.cell(0, 10, f'Page {self.page_no()}/{{nb}}', align='C')

class ExportService:
    def __init__(self):
        self.logo_path = "avatar-logo.png"

    def _clean_text_for_pdf(self, text):
        """Nettoyage Hybride : Robuste + Structure."""
        if text is None: return ""
        text = str(text)
        
        # Préservation de la structure
        structure_replacements = {
            "</h1>": "\n\n", "</h2>": "\n\n", "</h3>": "\n\n", "</h4>": "\n\n",
            "</p>": "\n", "</div>": "\n", "<br>": "\n", "<br/>": "\n",
            "<li>": "  - ", "</li>": "\n" 
        }
        for tag, replacement in structure_replacements.items():
            text = text.replace(tag, replacement)

        # Nettoyage HTML
        text = re.sub(r'<[^>]+>', '', text)

        # Symboles
        entity_replacements = {
            "&nbsp;": " ", "&amp;": "&", "&lt;": "<", "&gt;": ">", "&#39;": "'", "&quot;": '"',
            "&euro;": " EUR", "€": " EUR",
            "🎯": ">>", "⚠️": "ATTENTION :", "✅": "[OK]", "❌": "[KO]"
        }
        for entity, char in entity_replacements.items():
            text = text.replace(entity, char)

        # Nettoyage espaces
        text = re.sub(r'\n{3,}', '\n\n', text)
        
        # Encodage Latin-1
        return text.encode('latin-1', 'replace').decode('latin-1')

    def generate_pdf(self, user_query, ai_response):
        """Génère un PDF avec un design professionnel (Police Times)."""
        try:
            # Instanciation de la classe personnalisée
            pdf = SocialExpertPDF()
            pdf.alias_nb_pages() 
            pdf.add_page()
            
            clean_query = self._clean_text_for_pdf(user_query)
            clean_response = self._clean_text_for_pdf(ai_response)

            # --- BLOC 1 : LA QUESTION ---
            # Titre Question : Times Bold 20
            pdf.set_fill_color(245, 245, 245) 
            pdf.set_text_color(0, 0, 0)
            pdf.set_font("Times", "B", 20) 
            
            # On augmente la hauteur de cellule (12) car la police est grande (20)
            pdf.cell(0, 12, "OBJET DE LA CONSULTATION", ln=True, fill=True)
            
            # Corps Question : Times 12
            pdf.set_font("Times", "", 12)
            pdf.multi_cell(0, 6, clean_query, fill=True)
            pdf.ln(8)

            # --- BLOC 2 : ANALYSE ---
            # Titre Analyse : Times Bold 20 (Bleu)
            pdf.set_font("Times", "B", 20)
            pdf.set_text_color(37, 62, 146) 
            pdf.cell(0, 12, "ANALYSE JURIDIQUE & SIMULATION", ln=True)
            
            # Ligne fine sous le titre
            pdf.set_draw_color(200, 200, 200)
            pdf.line(10, pdf.get_y(), 100, pdf.get_y())
            pdf.ln(8)
            
            # --- BLOC 3 : LE CONTENU ---
            
            if ">> RÉSULTAT" in clean_response:
                parts = clean_response.split(">> RÉSULTAT")
                main_text = parts[0]
                result_text = ">> RÉSULTAT" + parts[1]
            else:
                main_text = clean_response
                result_text = ""

            # Corps Analyse : Times 10
            pdf.set_font("Times", "", 10)
            pdf.set_text_color(20, 20, 20)
            pdf.multi_cell(0, 6, main_text) # Hauteur de ligne 6 pour aérer le texte en 12
            pdf.ln(5)

            # --- BLOC 4 : LE RÉSULTAT (Mise en valeur) ---
            if result_text:
                pdf.ln(5)
                pdf.set_fill_color(240, 248, 255) 
                
                x = pdf.get_x()
                y = pdf.get_y()
                
                # Résultat : Times Bold 10 (On garde 10 pour le corps, mais en gras pour le résultat)
                pdf.set_font("Times", "B", 10)
                pdf.set_text_color(37, 62, 146)
                
                pdf.multi_cell(0, 8, result_text, fill=True)
                
                h = pdf.get_y() - y
                pdf.set_fill_color(37, 62, 146)
                pdf.rect(x, y, 1.5, h, 'F') 
                pdf.ln(10)

            # --- BLOC 5 : DISCLAIMER ---
            pdf.ln(10)
            pdf.set_draw_color(200, 200, 200)
            pdf.line(10, pdf.get_y(), 200, pdf.get_y())
            pdf.ln(5)
            
            pdf.set_font("Times", "I", 8)
            pdf.set_text_color(100, 100, 100)
            disclaimer = (
                "DOCUMENT CONFIDENTIEL - SIMULATION AUTOMATISÉE.\n"
                "Ce document est établi sur la base des barèmes officiels 2026. "
                "Il ne remplace pas l'avis circonstancié d'un expert-comptable ou d'un avocat."
            )
            pdf.multi_cell(0, 4, self._clean_text_for_pdf(disclaimer), align="C")

            return bytes(pdf.output())

        except Exception as e:
            logger.error(f"ERREUR CRITIQUE SERVICE PDF : {e}")
            return None
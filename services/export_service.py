from fpdf import FPDF
import datetime
import os
import re
from utils.helpers import logger

class SocialExpertPDF(FPDF):
    def header(self):
        # --- EN-TÊTE ALIGNÉ SUR MARGES 20mm ---
        
        # Logo (Aligné à gauche, X=20)
        logo_path = "avatar-logo.png"
        if os.path.exists(logo_path):
            try:
                # Logo placé un peu plus haut pour ne pas gêner le texte
                self.image(logo_path, 20, 10, 18) 
            except:
                pass
        
        # Titre (Aligné à droite, marge 20mm soit fin à 190mm)
        self.set_y(10)
        self.set_font('Times', 'B', 12)
        self.set_text_color(37, 62, 146) 
        self.cell(0, 6, 'SOCIAL EXPERT FRANCE', ln=True, align='R')
        
        # Date
        self.set_font('Times', 'I', 9)
        self.set_text_color(100, 100, 100)
        date_str = datetime.datetime.now().strftime("%d/%m/%Y")
        self.cell(0, 5, f'Dossier du {date_str}', ln=True, align='R')
        
        # Ligne de séparation (De 20mm à 190mm)
        self.set_draw_color(37, 62, 146)
        self.set_line_width(0.3)
        self.line(20, 22, 190, 22)
        self.ln(15) 

    def footer(self):
        self.set_y(-20) # Un peu plus haut car marge bas = 20mm
        self.set_font('Times', 'I', 8)
        self.set_text_color(128)
        self.cell(0, 10, f'Page {self.page_no()}/{{nb}}', align='C')

class ExportService:
    def __init__(self):
        self.logo_path = "avatar-logo.png"

    def _clean_text_for_pdf(self, text):
        if text is None: return ""
        text = str(text)
        
        # Structure
        structure_replacements = {
            "</h1>": "\n", "</h2>": "\n", "</h3>": "\n", "</h4>": "\n",
            "</p>": "\n", "</div>": "\n", "<br>": "\n", "<br/>": "\n",
            "<li>": "  - ", "</li>": "\n",
            "<ul>": "", "</ul>": ""
        }
        for tag, replacement in structure_replacements.items():
            text = text.replace(tag, replacement)

        text = re.sub(r'<[^>]+>', '', text)

        # Symboles
        entity_replacements = {
            "&nbsp;": " ", "&amp;": "&", "&lt;": "<", "&gt;": ">", "&#39;": "'", "&quot;": '"',
            "&euro;": " EUR", "€": " EUR",
            "🎯": ">>", "⚠️": "ATTENTION :", "✅": "[OK]", "❌": "[KO]"
        }
        for entity, char in entity_replacements.items():
            text = text.replace(entity, char)

        text = re.sub(r'\n{3,}', '\n\n', text)
        return text.encode('latin-1', 'replace').decode('latin-1')

    def generate_pdf(self, user_query, ai_response):
        try:
            pdf = SocialExpertPDF()
            pdf.alias_nb_pages()
            pdf.add_page()
            
            # --- MARGES 20mm (Standard Word) ---
            pdf.set_margins(20, 20, 20)
            
            # Calcul de la largeur utile : 210 - 20 - 20 = 170mm
            useful_width = 170
            
            clean_query = self._clean_text_for_pdf(user_query)
            clean_response = self._clean_text_for_pdf(ai_response)

            # --- 1. OBJET (Gris) ---
            pdf.set_fill_color(248, 248, 248) 
            pdf.set_text_color(0, 0, 0)
            
            # Titre : Times Bold 11
            pdf.set_font("Times", "B", 11)
            pdf.cell(0, 8, "  OBJET DE LA CONSULTATION", ln=True, fill=True)
            
            # Texte : Times 10.5
            pdf.set_font("Times", "", 10.5)
            # Astuce : Marge gauche temporaire pour simuler le padding
            pdf.set_left_margin(22) 
            pdf.multi_cell(166, 5, clean_query) # 166 = 170 - 4mm de padding visuel
            pdf.set_left_margin(20) # Retour marge standard
            pdf.ln(6)

            # --- 2. ANALYSE (Titre Bleu) ---
            pdf.set_font("Times", "B", 14)
            pdf.set_text_color(37, 62, 146)
            pdf.cell(0, 10, "ANALYSE JURIDIQUE & SIMULATION", ln=True)
            
            # Ligne fine (juste sous le titre)
            pdf.set_draw_color(200, 200, 200)
            pdf.line(20, pdf.get_y(), 90, pdf.get_y())
            pdf.ln(6)
            
            # --- 3. CORPS DU TEXTE ---
            if ">> RÉSULTAT" in clean_response:
                parts = clean_response.split(">> RÉSULTAT")
                main_text = parts[0]
                result_text = ">> RÉSULTAT" + parts[1]
            else:
                main_text = clean_response
                result_text = ""

            pdf.set_font("Times", "", 11)
            pdf.set_text_color(20, 20, 20)
            pdf.multi_cell(0, 5.5, main_text.strip())
            
            # --- 4. BLOC RÉSULTAT (Ajusté largeur 170mm) ---
            # 👇 LA CORRECTION EST ICI (Ajout des deux points :)
            if result_text:
                pdf.ln(6)
                
                pdf.set_font("Times", "B", 11)
                lines = pdf.multi_cell(0, 6, result_text, split_only=True)
                height = len(lines) * 6 + 4 
                
                pdf.set_fill_color(245, 248, 255)
                
                x = pdf.get_x()
                y = pdf.get_y()
                
                # Cadre largeur utile (170mm)
                pdf.rect(x, y, useful_width, height, 'F')
                
                # Barre latérale bleue
                pdf.set_fill_color(37, 62, 146)
                pdf.rect(x, y, 1, height, 'F')
                
                # Texte
                pdf.set_x(x + 3)
                pdf.set_text_color(37, 62, 146)
                pdf.multi_cell(useful_width - 4, 6, result_text)
                
                pdf.ln(5)

            # --- 5. DISCLAIMER ---
            # Gestion intelligente du pied de page
            if pdf.get_y() > 240: # Si on est trop bas, nouvelle page
                pdf.add_page()
            
            remaining_space = 277 - pdf.get_y() # 297 - 20(marge) = 277 max
            if remaining_space > 30:
                pdf.set_y(-30) # Collage en bas
            else:
                pdf.ln(5)

            pdf.set_draw_color(220, 220, 220)
            pdf.line(20, pdf.get_y(), 190, pdf.get_y())
            pdf.ln(3)
            
            pdf.set_font("Times", "I", 7)
            pdf.set_text_color(100, 100, 100)
            disclaimer = (
                "DOCUMENT CONFIDENTIEL.\n"
                "Simulation établie sur la base des barèmes 2026. Ne remplace pas un conseil juridique."
            )
            pdf.multi_cell(0, 3.5, self._clean_text_for_pdf(disclaimer), align="C")

            return bytes(pdf.output())

        except Exception as e:
            logger.error(f"ERREUR PDF : {e}")
            return None
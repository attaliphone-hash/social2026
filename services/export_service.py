from fpdf import FPDF
import datetime
import os
import re
from utils.helpers import logger

class SocialExpertPDF(FPDF):
    def header(self):
        # --- EN-TÊTE ---
        
        # Logo (Remonté légèrement à Y=8 pour éviter la ligne)
        logo_path = "avatar-logo.png"
        if os.path.exists(logo_path):
            try:
                self.image(logo_path, 20, 8, 18) 
            except:
                pass
        
        # Titre 
        self.set_y(10)
        self.set_font('Times', 'B', 12)
        self.set_text_color(37, 62, 146) 
        self.cell(0, 6, 'SOCIAL EXPERT FRANCE', ln=True, align='R')
        
        # Date
        self.set_font('Times', 'I', 9)
        self.set_text_color(100, 100, 100)
        date_str = datetime.datetime.now().strftime("%d/%m/%Y")
        self.cell(0, 5, f'Dossier du {date_str}', ln=True, align='R')
        
        # Ligne de séparation (Abaissée à Y=28 pour ne pas couper le logo)
        self.set_draw_color(37, 62, 146)
        self.set_line_width(0.3)
        self.line(20, 28, 190, 28)
        self.ln(20) # Espace après header

    def footer(self):
        self.set_y(-20) 
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
            pdf.set_margins(20, 20, 20)
            useful_width = 170
            
            clean_query = self._clean_text_for_pdf(user_query)
            clean_response = self._clean_text_for_pdf(ai_response)

            # --- EXTRACTION INTELLIGENTE ---
            # 1. Séparer le RÉSULTAT
            if ">> RÉSULTAT" in clean_response:
                parts = clean_response.split(">> RÉSULTAT")
                body_text = parts[0]
                result_text = ">> RÉSULTAT" + parts[1]
            else:
                body_text = clean_response
                result_text = ""
            
            # 2. Séparer les SOURCES (Souvent à la fin du corps ou du résultat)
            sources_text = ""
            keyword_sources = "Sources utilisées"
            
            # On cherche dans le corps
            if keyword_sources in body_text:
                sub_parts = body_text.split(keyword_sources)
                body_text = sub_parts[0]
                sources_text = keyword_sources + sub_parts[1]
            # Sinon on cherche dans le résultat (parfois l'IA le met après le prix)
            elif keyword_sources in result_text:
                sub_parts = result_text.split(keyword_sources)
                result_text = sub_parts[0]
                sources_text = keyword_sources + sub_parts[1]

            # --- 1. OBJET (Gris) ---
            pdf.set_fill_color(248, 248, 248) 
            pdf.set_text_color(0, 0, 0)
            pdf.set_font("Times", "B", 11)
            pdf.cell(0, 8, "  OBJET DE LA CONSULTATION", ln=True, fill=True)
            
            pdf.set_font("Times", "", 10.5)
            pdf.set_left_margin(22) 
            pdf.multi_cell(166, 5, clean_query) 
            pdf.set_left_margin(20) 
            pdf.ln(6)

            # --- 2. ANALYSE (Titre Bleu) ---
            pdf.set_font("Times", "B", 14)
            pdf.set_text_color(37, 62, 146)
            pdf.cell(0, 10, "ANALYSE JURIDIQUE & SIMULATION", ln=True)
            pdf.set_draw_color(200, 200, 200)
            pdf.line(20, pdf.get_y(), 90, pdf.get_y())
            pdf.ln(6)
            
            # --- 3. CORPS DU TEXTE ---
            pdf.set_font("Times", "", 11)
            pdf.set_text_color(20, 20, 20)
            pdf.multi_cell(0, 5.5, body_text.strip())
            
            # --- 4. BLOC RÉSULTAT (Large Padding) ---
            if result_text:
                pdf.ln(8) # Espace avant le bloc
                
                pdf.set_font("Times", "B", 11)
                # On calcule la hauteur du texte
                lines = pdf.multi_cell(useful_width - 10, 6, result_text.strip(), split_only=True)
                
                # PADDING AUGMENTÉ : +12mm (6mm haut / 6mm bas)
                height = len(lines) * 6 + 12 
                
                pdf.set_fill_color(245, 248, 255)
                
                x = pdf.get_x()
                y = pdf.get_y()
                
                # Fond
                pdf.rect(x, y, useful_width, height, 'F')
                # Barre bleue
                pdf.set_fill_color(37, 62, 146)
                pdf.rect(x, y, 1, height, 'F')
                
                # Écriture du texte avec décalage (Padding interne)
                pdf.set_xy(x + 5, y + 6) # X+5mm, Y+6mm (Padding haut)
                pdf.set_text_color(37, 62, 146)
                pdf.multi_cell(useful_width - 10, 6, result_text.strip())
                
                # On repositionne le curseur après le bloc
                pdf.set_y(y + height + 5)

            # --- 5. SOURCES (Format Spécifique : Petit & Gauche) ---
            if sources_text:
                pdf.ln(2)
                pdf.set_font("Times", "I", 8) # Corps 8 italique
                pdf.set_text_color(100, 100, 100) # Gris foncé
                pdf.multi_cell(0, 4, sources_text.strip(), align='L') # Alignement Gauche
                pdf.ln(5)

            # --- 6. DISCLAIMER ---
            # Gestion saut de page
            if pdf.get_y() > 250: 
                pdf.add_page()
            
            remaining_space = 277 - pdf.get_y() 
            if remaining_space > 30:
                pdf.set_y(-30) 
            else:
                pdf.ln(5)

            pdf.set_draw_color(220, 220, 220)
            pdf.line(20, pdf.get_y(), 190, pdf.get_y())
            pdf.
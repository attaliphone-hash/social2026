from fpdf import FPDF
import datetime
import os
import re
from utils.helpers import logger

class SocialExpertPDF(FPDF):
    def header(self):
        # --- EN-TÊTE ---
        # 1. Logo (X=20, Y=10, H=18 -> Finit à Y=28)
        logo_path = "avatar-logo.png"
        if os.path.exists(logo_path):
            try:
                self.image(logo_path, 20, 10, 18) 
            except:
                pass
        
        # 2. Titre Entreprise
        self.set_y(15)
        self.set_font('Helvetica', 'B', 12)
        self.set_text_color(37, 62, 146) # Bleu
        self.cell(0, 6, 'Social Expert France', ln=True, align='R')
        
        # 3. Ligne de séparation (À Y=35 pour être LARGE sous le logo)
        self.set_y(35)
        self.set_draw_color(200, 200, 200) # Gris standard
        self.set_line_width(0.3)
        self.line(20, 35, 190, 35)
        self.ln(10) # On laisse de l'espace après la ligne

    def footer(self):
        self.set_y(-15) 
        self.set_font('Helvetica', '', 8)
        self.set_text_color(128)
        self.cell(0, 10, f'Page {self.page_no()}/{{nb}}', align='C')

class ExportService:
    def __init__(self):
        self.logo_path = "avatar-logo.png"

    def _clean_text_strict(self, text):
        """
        Nettoyage DRASTIQUE pour avoir un rendu 'Texte Brut' propre.
        Supprime tout le HTML qui cassait l'affichage.
        """
        if not text: return ""
        text = str(text)
        
        # 1. Suppression totale des balises HTML
        text = re.sub(r'<[^>]+>', '', text) 
        
        # 2. Nettoyage Markdown de base (On garde juste le texte)
        text = text.replace("**", "").replace("__", "") # On enlève le gras Markdown pour gérer nous-même si besoin
        text = text.replace("##", "").replace("###", "")
        
        # 3. Listes propres (Tirets)
        lines = []
        for line in text.split('\n'):
            line = line.strip()
            # Si c'est une puce ou un astérisque
            if line.startswith('* ') or line.startswith('- ') or line.startswith('•'):
                line = "  • " + line[1:].strip()
            lines.append(line)
        text = "\n".join(lines)

        # 4. Symboles
        replacements = {
            "&nbsp;": " ", "&amp;": "&", "&lt;": "<", "&gt;": ">",
            "&euro;": " EUR", "€": " EUR",
            "🎯": "", "⚠️": "ATTENTION : ", "✅": "[OK] ", "❌": "[KO] "
        }
        for entity, char in replacements.items():
            text = text.replace(entity, char)

        text = re.sub(r'\n{3,}', '\n\n', text)
        return text.encode('latin-1', 'replace').decode('latin-1')

    def generate_pdf(self, user_query, ai_response):
        try:
            pdf = SocialExpertPDF()
            pdf.alias_nb_pages()
            pdf.add_page()
            pdf.set_margins(20, 20, 20)
            pdf.set_auto_page_break(auto=True, margin=20)
            
            clean_query = self._clean_text_strict(user_query)
            
            # --- EXTRACTION SIMPLE ---
            if ">> RÉSULTAT" in ai_response:
                parts = ai_response.split(">> RÉSULTAT")
                body_raw = parts[0]
                result_raw = parts[1].strip()
            elif "RÉSULTAT" in ai_response:
                parts = ai_response.split("RÉSULTAT")
                body_raw = parts[0]
                result_raw = parts[1].strip()
            else:
                body_raw = ai_response
                result_raw = ""

            clean_body = self._clean_text_strict(body_raw)
            clean_result = self._clean_text_strict(result_raw)

            # ==========================================
            # DÉBUT DU DOCUMENT (Style "Word" Classique)
            # ==========================================

            # 1. DATE (Petit tag gris)
            pdf.set_y(45) # On commence bien en dessous de l'en-tête
            pdf.set_font("Helvetica", "B", 10)
            pdf.set_text_color(100, 100, 100) # Gris
            date_str = datetime.datetime.now().strftime("%d/%m/%Y")
            
            # Astuce pour le "Badge" gris (Fond gris clair)
            pdf.set_fill_color(240, 240, 240)
            pdf.cell(40, 8, f"  Question du {date_str}  ", ln=True, fill=True, align='C')
            pdf.ln(8)

            # 2. OBJET (Titre Gras + Texte)
            pdf.set_font("Helvetica", "B", 11)
            pdf.set_text_color(0, 0, 0) # Noir
            pdf.cell(0, 6, "OBJET DE LA CONSULTATION", ln=True)
            pdf.ln(2)
            
            pdf.set_font("Helvetica", "", 11)
            pdf.multi_cell(0, 6, clean_query)
            
            # Séparateur simple
            pdf.ln(6)
            pdf.set_draw_color(220, 220, 220)
            pdf.line(20, pdf.get_y(), 190, pdf.get_y())
            pdf.ln(8)

            # 3. ANALYSE (Titre Gras + Texte)
            pdf.set_font("Helvetica", "B", 11)
            pdf.cell(0, 6, "ANALYSE JURIDIQUE & SIMULATION", ln=True)
            pdf.ln(4)

            pdf.set_font("Helvetica", "", 10)
            pdf.set_text_color(20, 20, 20)
            pdf.multi_cell(0, 6, clean_body)
            
            pdf.ln(8)

            # 4. RÉSULTAT (Clair et Net)
            if clean_result:
                pdf.set_font("Helvetica", "B", 11)
                pdf.set_text_color(0, 0, 0)
                pdf.cell(0, 8, "RÉSULTAT", ln=True)
                
                # Le résultat en Gras plus gros
                pdf.set_font("Helvetica", "B", 11)
                pdf.set_text_color(0, 0, 0)
                pdf.multi_cell(0, 8, clean_result)
                
                pdf.ln(8)

            # 5. DISCLAIMER & SOURCES (Bas de page)
            pdf.set_draw_color(220, 220, 220)
            pdf.line(20, pdf.get_y(), 190, pdf.get_y())
            pdf.ln(6)
            
            # Sources
            pdf.set_font("Helvetica", "B", 10)
            pdf.set_text_color(50, 50, 50)
            pdf.write(5, "Sources utilisées : ")
            pdf.set_font("Helvetica", "", 10)
            pdf.write(5, "Barèmes officiels URSSAF & Code du travail 2026.") # Texte générique propre si extraction échoue
            pdf.ln(8)

            
            pdf.set_font("Helvetica", "B", 9)
            pdf.write(5, "DOCUMENT CONFIDENTIEL ")
            pdf.set_font("Helvetica", "", 9)
            pdf.write(5, "Simulation établie sur la base des barèmes 2026. Ne remplace pas un conseil juridique.")

            return bytes(pdf.output())

        except Exception as e:
            logger.error(f"ERREUR PDF : {e}")
            return None
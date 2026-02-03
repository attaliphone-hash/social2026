from fpdf import FPDF
import datetime
import os
import re
from utils.helpers import logger

class SocialExpertPDF(FPDF):
    def header(self):
        # --- EN-TÊTE ---
        logo_path = "avatar-logo.png"
        if os.path.exists(logo_path):
            try:
                self.image(logo_path, 20, 10, 18) 
            except:
                pass
        
        # Titre
        self.set_y(15)
        self.set_font('Helvetica', 'B', 12)
        self.set_text_color(37, 62, 146) 
        self.cell(0, 6, 'SOCIAL EXPERT FRANCE', ln=True, align='R')
        
        # Ligne
        self.set_y(35)
        self.set_draw_color(200, 200, 200) 
        self.set_line_width(0.3)
        self.line(20, 35, 190, 35)
        self.ln(10)

    def footer(self):
        self.set_y(-15) 
        self.set_font('Helvetica', '', 8)
        self.set_text_color(128)
        self.cell(0, 10, f'Page {self.page_no()}/{{nb}}', align='C')

class ExportService:
    def __init__(self):
        self.logo_path = "avatar-logo.png"

    def _clean_text_strict(self, text):
        """Nettoyage strict pour éviter tout bug d'affichage."""
        if not text: return ""
        text = str(text)
        text = re.sub(r'<[^>]+>', '', text) 
        text = text.replace("**", "").replace("__", "").replace("##", "")
        
        lines = []
        for line in text.split('\n'):
            line = line.strip()
            if line.startswith('* ') or line.startswith('- ') or line.startswith('•'):
                line = "  • " + line[1:].strip()
            lines.append(line)
        text = "\n".join(lines)

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
            
            # --- EXTRACTION INTELLIGENTE ---
            # 1. Séparation Body / Reste
            if ">> RÉSULTAT" in ai_response:
                parts = ai_response.split(">> RÉSULTAT")
                body_raw = parts[0]
                rest_raw = parts[1] # Contient le Résultat ET les Sources
            elif "RÉSULTAT" in ai_response:
                parts = ai_response.split("RÉSULTAT")
                body_raw = parts[0]
                rest_raw = parts[1]
            else:
                body_raw = ai_response
                rest_raw = ""

            # 2. Séparation Résultat / Sources (dans la 2ème partie)
            sources_raw = ""
            result_raw = rest_raw
            
            # On cherche le mot clé "Sources utilisées"
            if "Sources utilisées" in rest_raw:
                sub_parts = rest_raw.split("Sources utilisées")
                result_raw = sub_parts[0]
                sources_raw = "Sources utilisées" + sub_parts[1]
            elif "Sources" in rest_raw: # Variantes
                sub_parts = rest_raw.split("Sources")
                result_raw = sub_parts[0]
                sources_raw = "Sources" + sub_parts[1]

            clean_body = self._clean_text_strict(body_raw)
            clean_result = self._clean_text_strict(result_raw).strip()
            clean_sources = self._clean_text_strict(sources_raw).strip()

            # ==========================================
            # CONSTRUCTION DU DOCUMENT
            # ==========================================

            # 1. DATE
            pdf.set_y(45)
            pdf.set_font("Helvetica", "B", 10)
            pdf.set_text_color(100, 100, 100)
            date_str = datetime.datetime.now().strftime("%d/%m/%Y")
            
            pdf.set_fill_color(240, 240, 240)
            pdf.cell(40, 8, f"  Dossier du {date_str}  ", ln=True, fill=True, align='C')
            pdf.ln(8)

            # 2. OBJET
            pdf.set_font("Helvetica", "B", 11)
            pdf.set_text_color(0, 0, 0)
            pdf.cell(0, 6, "OBJET DE LA CONSULTATION", ln=True)
            pdf.ln(2)
            
            pdf.set_font("Helvetica", "", 11)
            pdf.multi_cell(0, 6, clean_query)
            
            pdf.ln(6)
            pdf.set_draw_color(220, 220, 220)
            pdf.line(20, pdf.get_y(), 190, pdf.get_y())
            pdf.ln(8)

            # 3. ANALYSE
            pdf.set_font("Helvetica", "B", 11)
            pdf.cell(0, 6, "ANALYSE JURIDIQUE & SIMULATION", ln=True)
            pdf.ln(4)

            pdf.set_font("Helvetica", "", 11)
            pdf.set_text_color(20, 20, 20)
            pdf.multi_cell(0, 6, clean_body)
            pdf.ln(8)

            # 4. RÉSULTAT
            if clean_result:
                pdf.set_font("Helvetica", "B", 11)
                pdf.set_text_color(0, 0, 0)
                pdf.cell(0, 8, ">> RÉSULTAT", ln=True)
                
                pdf.set_font("Helvetica", "B", 12)
                pdf.multi_cell(0, 8, clean_result)
                pdf.ln(4)

            # 5. SOURCES (CORRECTION ZONE ROUGE : TEXTE PETIT)
            if clean_sources:
                pdf.ln(2)
                pdf.set_font("Helvetica", "", 9) # Taille 9 (Petit)
                pdf.set_text_color(80, 80, 80)   # Gris foncé pour différencier
                pdf.multi_cell(0, 5, clean_sources)
                pdf.ln(8)

            # 6. DISCLAIMER (CORRECTION ZONE BLEUE : SUPPRESSION DU DOUBLON)
            pdf.set_draw_color(220, 220, 220)
            pdf.line(20, pdf.get_y(), 190, pdf.get_y())
            pdf.ln(6)
            
            # On passe directement au disclaimer légal, sans remettre les sources génériques
            pdf.set_font("Helvetica", "I", 9)
            pdf.set_text_color(100, 100, 100)
            pdf.multi_cell(0, 5, "Données certifiées conformes aux barèmes 2026.")
            pdf.ln(2)
            
            pdf.set_font("Helvetica", "B", 9)
            pdf.write(5, "DOCUMENT CONFIDENTIEL ")
            pdf.set_font("Helvetica", "", 9)
            pdf.write(5, "Simulation établie sur la base des barèmes 2026. Ne remplace pas un conseil juridique.")

            return bytes(pdf.output())

        except Exception as e:
            logger.error(f"ERREUR PDF : {e}")
            return None
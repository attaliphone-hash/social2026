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
        
        self.set_y(12)
        self.set_font('Helvetica', 'B', 12)
        self.set_text_color(37, 62, 146) # Bleu Brand
        self.cell(0, 6, 'SOCIAL EXPERT FRANCE', ln=True, align='R')
        
        # Ligne discrète
        self.ln(10)
        self.set_draw_color(230, 230, 230)
        self.line(20, 25, 190, 25)
        self.ln(10)

    def footer(self):
        self.set_y(-15) 
        self.set_font('Helvetica', '', 8)
        self.set_text_color(180, 180, 180)
        self.cell(0, 10, f'{self.page_no()}/{{nb}}', align='C')

class ExportService:
    def __init__(self):
        self.logo_path = "avatar-logo.png"

    def _clean_text_for_markdown(self, text):
        """
        Prépare le texte pour le moteur Markdown de FPDF2.
        """
        if not text: return ""
        text = str(text)
        
        # 1. Nettoyage HTML résiduel
        text = text.replace("</h1>", "\n").replace("</h2>", "\n").replace("</h3>", "\n")
        text = text.replace("<br>", "\n").replace("<br/>", "\n")
        
        # 2. Gestion des listes pour Markdown
        # FPDF2 gère bien les tirets "-" s'ils sont en début de ligne
        lines = text.split('\n')
        clean_lines = []
        for line in lines:
            line = line.strip()
            if line.startswith('<li>'):
                line = "- " + line.replace('<li>', '').replace('</li>', '')
            clean_lines.append(line)
        
        text = "\n".join(clean_lines)

        # 3. Symboles
        replacements = {
            "&nbsp;": " ", "&amp;": "&", "&lt;": "<", "&gt;": ">",
            "&euro;": " EUR", "€": " EUR",
            "🎯": "", "⚠️": "ATTENTION : ", "✅": "[OK] ", "❌": "[KO] "
        }
        for entity, char in replacements.items():
            text = text.replace(entity, char)

        # 4. Encodage
        return text.encode('latin-1', 'replace').decode('latin-1')

    def generate_pdf(self, user_query, ai_response):
        try:
            pdf = SocialExpertPDF()
            pdf.alias_nb_pages()
            pdf.add_page()
            pdf.set_margins(20, 20, 20)
            pdf.set_auto_page_break(auto=True, margin=20)
            
            clean_query = user_query.replace("\n", " ")
            
            # --- EXTRACTION RÉSULTAT ---
            if ">> RÉSULTAT" in ai_response:
                parts = ai_response.split(">> RÉSULTAT")
                body_raw = parts[0]
                result_raw = parts[1].strip()
            else:
                body_raw = ai_response
                result_raw = ""

            # Préparation Markdown
            body_md = self._clean_text_for_markdown(body_raw)
            result_md = self._clean_text_for_markdown(result_raw)

            # --- 1. DATE ---
            pdf.set_y(30)
            pdf.set_font("Helvetica", "B", 10)
            pdf.set_text_color(20, 20, 20)
            date_str = datetime.datetime.now().strftime("%d/%m/%Y")
            pdf.cell(0, 6, f"Dossier du {date_str}", ln=True)
            pdf.ln(8)

            # --- 2. OBJET (Normal) ---
            pdf.set_font("Helvetica", "B", 11)
            pdf.set_text_color(0, 0, 0)
            pdf.cell(0, 6, "OBJET DE LA CONSULTATION", ln=True)
            pdf.ln(2)
            
            pdf.set_font("Helvetica", "", 10)
            pdf.multi_cell(0, 5, clean_query)
            
            pdf.ln(6)
            pdf.set_draw_color(230, 230, 230)
            pdf.line(20, pdf.get_y(), 190, pdf.get_y())
            pdf.ln(6)

            # --- 3. ANALYSE (Markdown Natif !) ---
            pdf.set_font("Helvetica", "B", 11)
            pdf.cell(0, 6, "ANALYSE JURIDIQUE & SIMULATION", ln=True)
            pdf.ln(2)

            pdf.set_font("Helvetica", "", 10)
            pdf.set_text_color(30, 30, 30)
            
            # C'EST ICI LA RÉPARATION : markdown=True permet le gras (**texte**)
            try:
                pdf.multi_cell(0, 5, body_md, markdown=True)
            except:
                # Fallback si le markdown plante (sécurité absolue)
                pdf.multi_cell(0, 5, body_md)
            
            pdf.ln(4)

            # --- 4. RÉSULTAT ---
            if result_md:
                pdf.set_font("Helvetica", "B", 11)
                pdf.set_text_color(0, 0, 0)
                pdf.cell(0, 8, ">> RÉSULTAT", ln=True)
                
                # Fond Gris clair
                pdf.set_fill_color(245, 247, 250)
                pdf.set_font("Helvetica", "B", 11)
                
                # Affichage du résultat
                pdf.cell(0, 10, f"  {result_md}  ", ln=True, fill=True)
                pdf.ln(8)

            # --- 5. DISCLAIMER ---
            pdf.set_draw_color(230, 230, 230)
            pdf.line(20, pdf.get_y(), 190, pdf.get_y())
            pdf.ln(6)

            pdf.set_font("Helvetica", "I", 9)
            pdf.set_text_color(100, 100, 100)
            pdf.multi_cell(0, 4, "Données certifiées conformes aux barèmes 2026.")
            pdf.ln(2)
            
            pdf.set_font("Helvetica", "B", 9)
            pdf.write(4, "DOCUMENT CONFIDENTIEL ")
            pdf.set_font("Helvetica", "", 9)
            pdf.write(4, "Simulation établie sur la base des barèmes 2026. Ne remplace pas un conseil juridique.")

            return bytes(pdf.output())

        except Exception as e:
            logger.error(f"ERREUR CRITIQUE PDF : {e}")
            return None
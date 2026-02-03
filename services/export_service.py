from fpdf import FPDF
import datetime
import os
import re
from utils.helpers import logger

class SocialExpertPDF(FPDF):
    def header(self):
        logo_path = "avatar-logo.png"
        if os.path.exists(logo_path):
            try:
                self.image(logo_path, 20, 10, 18) 
            except:
                pass
        
        self.set_y(15)
        self.set_font('Helvetica', 'B', 12)
        self.set_text_color(37, 62, 146) 
        self.cell(0, 6, 'SOCIAL EXPERT FRANCE', ln=True, align='R')
        
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

    def _clean_markdown_for_pdf(self, text):
        if not text: return ""
        text = str(text)
        text = re.sub(r'<[^>]+>', '', text) # Sécurité
        
        lines = []
        for line in text.split('\n'):
            line = line.strip()
            # Conversion Titres Markdown -> Gras PDF
            if line.startswith('### ') or line.startswith('## '):
                content = line.replace('#', '').strip()
                line = f"\n**{content}**"
            elif line.startswith('- ') or line.startswith('* '):
                 line = "  • " + line[1:].strip()
            lines.append(line)
        text = "\n".join(lines)

        replacements = {"&nbsp;": " ", "&euro;": " EUR", "€": " EUR", "🎯": ">> "}
        for k, v in replacements.items(): text = text.replace(k, v)

        return text.encode('latin-1', 'replace').decode('latin-1')

    def generate_pdf(self, user_query, ai_response):
        try:
            pdf = SocialExpertPDF()
            pdf.alias_nb_pages()
            pdf.add_page()
            pdf.set_margins(20, 20, 20)
            pdf.set_auto_page_break(auto=True, margin=20)
            
            clean_query = self._clean_markdown_for_pdf(user_query)
            
            # Découpage intelligent
            if "RÉSULTAT" in ai_response:
                parts = ai_response.split("RÉSULTAT")
                body = parts[0]
                rest = parts[1] if len(parts)>1 else ""
            else:
                body, rest = ai_response, ""

            if "Sources" in rest:
                sub = rest.split("Sources")
                res_txt, src_txt = sub[0], "Sources" + sub[1]
            else:
                res_txt, src_txt = rest, ""

            clean_body = self._clean_markdown_for_pdf(body).replace(">>", "")
            clean_res = self._clean_markdown_for_pdf(res_txt).replace(":", "").strip()
            clean_src = self._clean_markdown_for_pdf(src_txt).strip()

            # --- DESSIN ---
            # Date
            pdf.set_y(45)
            pdf.set_font("Helvetica", "B", 10)
            pdf.set_text_color(100)
            pdf.set_fill_color(240)
            pdf.cell(40, 8, f"  Dossier du {datetime.datetime.now().strftime('%d/%m/%Y')}  ", ln=True, fill=True, align='C')
            pdf.ln(8)

            # Objet
            pdf.set_font("Helvetica", "B", 11)
            pdf.set_text_color(0)
            pdf.cell(0, 6, "OBJET DE LA CONSULTATION", ln=True)
            pdf.ln(2)
            pdf.set_font("Helvetica", "", 11)
            pdf.multi_cell(0, 6, clean_query)
            pdf.ln(6)
            pdf.set_draw_color(220)
            pdf.line(20, pdf.get_y(), 190, pdf.get_y())
            pdf.ln(8)

            # Analyse
            pdf.set_font("Helvetica", "B", 11)
            pdf.cell(0, 6, "ANALYSE JURIDIQUE & SIMULATION", ln=True)
            pdf.ln(4)
            pdf.set_font("Helvetica", "", 11)
            pdf.set_text_color(20)
            try:
                pdf.multi_cell(0, 6, clean_body, markdown=True)
            except:
                pdf.multi_cell(0, 6, clean_body)
            pdf.ln(8)

            # Résultat
            if clean_res:
                pdf.set_font("Helvetica", "B", 11)
                pdf.set_text_color(0)
                pdf.cell(0, 8, ">> RÉSULTAT", ln=True)
                pdf.set_font("Helvetica", "B", 12)
                pdf.multi_cell(0, 8, clean_res.replace("**", ""))
                pdf.ln(4)

            # Sources
            if clean_src:
                pdf.ln(2)
                pdf.set_font("Helvetica", "", 9) 
                pdf.set_text_color(80)
                pdf.multi_cell(0, 5, clean_src)
                pdf.ln(8)

            # Disclaimer
            pdf.set_draw_color(220)
            pdf.line(20, pdf.get_y(), 190, pdf.get_y())
            pdf.ln(6)
            pdf.set_text_color(100)
            pdf.set_font("Helvetica", "B", 9)
            pdf.write(5, "DOCUMENT CONFIDENTIEL ")
            pdf.set_font("Helvetica", "", 9)
            pdf.write(5, "Simulation établie sur la base des barèmes 2026. Ne remplace pas un conseil juridique.")

            return bytes(pdf.output())

        except Exception as e:
            logger.error(f"ERREUR PDF : {e}")
            return None
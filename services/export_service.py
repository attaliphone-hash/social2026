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
        
        # Ligne de séparation
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
        """
        Prépare le texte Markdown pour FPDF.
        Garde le gras (**texte**) mais retire les titres (###) pour éviter les erreurs de parsing.
        """
        if not text: return ""
        text = str(text)
        
        # 1. Nettoyage HTML résiduel (sécurité)
        text = re.sub(r'<[^>]+>', '', text) 
        
        # 2. Gestion des Titres Markdown (### Titre)
        # FPDF standard gère mal les titres #, on les transforme en gras simple avec saut de ligne
        lines = []
        for line in text.split('\n'):
            line = line.strip()
            # Transformation des titres "### Titre" en "**Titre**"
            if line.startswith('### ') or line.startswith('## '):
                content = line.replace('#', '').strip()
                line = f"\n**{content}**" # On force le gras et un saut de ligne avant
            elif line.startswith('- ') or line.startswith('* '):
                 line = "  • " + line[1:].strip()
            lines.append(line)
            
        text = "\n".join(lines)

        # 3. Symboles Spéciaux
        replacements = {
            "&nbsp;": " ", "&amp;": "&", "&lt;": "<", "&gt;": ">",
            "&euro;": " EUR", "€": " EUR",
            "🎯": ">> "
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
            
            clean_query = self._clean_markdown_for_pdf(user_query)
            
            # --- EXTRACTION CONTENU ---
            # On cherche le séparateur ">> RÉSULTAT" (format Markdown)
            # Note : Le prompt IA met maintenant "### >> RÉSULTAT"
            if "RÉSULTAT" in ai_response:
                # On split grossièrement sur "RÉSULTAT" pour trouver la fin
                parts = ai_response.split("RÉSULTAT")
                body_raw = parts[0]
                # On essaie de récupérer le reste
                rest_raw = parts[1] if len(parts) > 1 else ""
            else:
                body_raw = ai_response
                rest_raw = ""

            # Extraction Sources (Souvent à la fin)
            if "Sources utilisées" in rest_raw:
                sub_parts = rest_raw.split("Sources utilisées")
                result_raw = sub_parts[0]
                sources_raw = "Sources utilisées" + sub_parts[1]
            else:
                result_raw = rest_raw
                sources_raw = ""

            # Nettoyage
            # On retire les "###" éventuels qui traînent dans la découpe
            clean_body = self._clean_markdown_for_pdf(body_raw).replace(">>", "")
            clean_result = self._clean_markdown_for_pdf(result_raw).replace(":", "").strip()
            clean_sources = self._clean_markdown_for_pdf(sources_raw).strip()

            # ==========================================
            # GÉNÉRATION DOCUMENT (Support Markdown activé)
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
            # Pas de markdown pour la question user, texte brut
            pdf.multi_cell(0, 6, clean_query)
            
            pdf.ln(6)
            pdf.set_draw_color(220, 220, 220)
            pdf.line(20, pdf.get_y(), 190, pdf.get_y())
            pdf.ln(8)

            # 3. ANALYSE (Markdown Activé !)
            pdf.set_font("Helvetica", "B", 11)
            pdf.cell(0, 6, "ANALYSE JURIDIQUE & SIMULATION", ln=True)
            pdf.ln(4)

            pdf.set_font("Helvetica", "", 11)
            pdf.set_text_color(20, 20, 20)
            
            # C'est ici la magie : markdown=True permet d'interpréter les **gras**
            try:
                pdf.multi_cell(0, 6, clean_body, markdown=True)
            except:
                # Fallback si le markdown est cassé
                pdf.multi_cell(0, 6, clean_body)
            
            pdf.ln(8)

            # 4. RÉSULTAT
            if clean_result:
                pdf.set_font("Helvetica", "B", 11)
                pdf.set_text_color(0, 0, 0)
                pdf.cell(0, 8, ">> RÉSULTAT", ln=True)
                
                pdf.set_font("Helvetica", "B", 12)
                # On nettoie les éventuels astérisques résiduels pour le titre résultat
                clean_result_display = clean_result.replace("**", "")
                pdf.multi_cell(0, 8, clean_result_display)
                pdf.ln(4)

            # 5. SOURCES
            if clean_sources:
                pdf.ln(2)
                pdf.set_font("Helvetica", "", 9) 
                pdf.set_text_color(80, 80, 80)
                pdf.multi_cell(0, 5, clean_sources)
                pdf.ln(8)

            # 6. DISCLAIMER
            pdf.set_draw_color(220, 220, 220)
            pdf.line(20, pdf.get_y(), 190, pdf.get_y())
            pdf.ln(6)
            
            pdf.set_text_color(100, 100, 100)
            pdf.set_font("Helvetica", "B", 9)
            pdf.write(5, "DOCUMENT CONFIDENTIEL ")
            pdf.set_font("Helvetica", "", 9)
            pdf.write(5, "Simulation établie sur la base des barèmes 2026. Ne remplace pas un conseil juridique.")

            return bytes(pdf.output())

        except Exception as e:
            logger.error(f"ERREUR PDF : {e}")
            return None
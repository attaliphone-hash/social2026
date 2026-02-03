from fpdf import FPDF
import datetime
import os
import re
from utils.helpers import logger

class SocialExpertPDF(FPDF):
    def header(self):
        # --- EN-TÊTE CORRIGÉ ---
        # 1. Logo (Position X=20, Y=10, Hauteur=18)
        # Le bas du logo arrive donc à Y = 10 + 18 = 28
        logo_path = "avatar-logo.png"
        if os.path.exists(logo_path):
            try:
                self.image(logo_path, 20, 10, 18) 
            except:
                pass
        
        # 2. Titre Entreprise
        self.set_y(15) # On descend un peu le texte
        self.set_font('Helvetica', 'B', 12)
        self.set_text_color(37, 62, 146) # Bleu Brand
        self.cell(0, 6, 'SOCIAL EXPERT FRANCE', ln=True, align='R')
        
        # 3. Ligne de séparation (DESCENDUE pour ne pas couper le logo)
        # On la place à Y=35 (Le logo finit à 28, donc on a 7mm de marge)
        self.set_y(35)
        self.set_draw_color(230, 230, 230) # Gris très clair
        self.line(20, 35, 190, 35)
        self.ln(5) # Espace après la ligne

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
        Nettoie le texte pour retirer le HTML parasite et ne garder que le Markdown simple (**gras**).
        """
        if not text: return ""
        text = str(text)
        
        # 1. Suppression brutale des balises HTML complexes (div, span, etc.)
        # On ne veut pas que le PDF affiche "<div>"
        text = re.sub(r'<[^>]+>', '', text) 
        
        # 2. Nettoyage des sauts de ligne multiples
        text = text.replace("\r", "")
        text = re.sub(r'\n{3,}', '\n\n', text)
        
        # 3. Gestion des listes (Transformation des puces HTML ou texte en tirets Markdown)
        lines = []
        for line in text.split('\n'):
            line = line.strip()
            # Si la ligne commence par une puce bizarre, on met un tiret propre
            if line.startswith('•') or line.startswith('* '):
                line = "- " + line[1:].strip()
            lines.append(line)
        text = "\n".join(lines)

        # 4. Symboles & Devises
        replacements = {
            "&nbsp;": " ", "&amp;": "&", "&lt;": "<", "&gt;": ">",
            "&euro;": " EUR", "€": " EUR",
            "🎯": "", "⚠️": "ATTENTION : ", "✅": "[OK] ", "❌": "[KO] "
        }
        for entity, char in replacements.items():
            text = text.replace(entity, char)

        # 5. Encodage Latin-1 (Obligatoire pour FPDF standard)
        return text.encode('latin-1', 'replace').decode('latin-1')

    def generate_pdf(self, user_query, ai_response):
        try:
            pdf = SocialExpertPDF()
            pdf.alias_nb_pages()
            pdf.add_page()
            pdf.set_margins(20, 20, 20)
            pdf.set_auto_page_break(auto=True, margin=20)
            
            clean_query = user_query.replace("\n", " ").encode('latin-1', 'replace').decode('latin-1')
            
            # --- EXTRACTION CONTENU ---
            # On sépare le texte principal du résultat final
            if ">> RÉSULTAT" in ai_response:
                parts = ai_response.split(">> RÉSULTAT")
                body_raw = parts[0]
                result_raw = parts[1].strip()
            elif "RÉSULTAT" in ai_response: # Variantes
                parts = ai_response.split("RÉSULTAT")
                body_raw = parts[0]
                result_raw = parts[1].strip()
            else:
                body_raw = ai_response
                result_raw = ""

            # Nettoyage Markdown
            body_md = self._clean_text_for_markdown(body_raw)
            result_md = self._clean_text_for_markdown(result_raw)

            # --- 1. DATE & OBJET ---
            # On se place sous la ligne (qui est à Y=35)
            pdf.set_y(40)
            
            # Date Tag
            pdf.set_font("Helvetica", "B", 10)
            pdf.set_text_color(20, 20, 20)
            date_str = datetime.datetime.now().strftime("%d/%m/%Y")
            pdf.cell(0, 6, f"Dossier du {date_str}", ln=True)
            pdf.ln(6)

            # Objet Titre
            pdf.set_font("Helvetica", "B", 11)
            pdf.set_text_color(0, 0, 0)
            pdf.cell(0, 6, "OBJET DE LA CONSULTATION", ln=True)
            pdf.ln(2)
            
            # Objet Contenu (Normal)
            pdf.set_font("Helvetica", "", 10)
            pdf.multi_cell(0, 5, clean_query)
            
            # Séparateur fin
            pdf.ln(6)
            pdf.set_draw_color(240, 240, 240)
            pdf.line(20, pdf.get_y(), 190, pdf.get_y())
            pdf.ln(6)

            # --- 2. ANALYSE (Corps) ---
            pdf.set_font("Helvetica", "B", 11)
            pdf.cell(0, 6, "ANALYSE JURIDIQUE & SIMULATION", ln=True)
            pdf.ln(2)

            pdf.set_font("Helvetica", "", 10)
            pdf.set_text_color(30, 30, 30)
            
            # Utilisation du mode Markdown pour le gras (**texte**)
            # FPDF gère les tirets "- " comme des listes automatiquement en début de ligne
            pdf.multi_cell(0, 5, body_md, markdown=True)
            
            pdf.ln(6)

            # --- 3. RÉSULTAT (DESSINÉ MANUELLEMENT) ---
            if result_md:
                # Titre Resultat
                pdf.set_font("Helvetica", "B", 11)
                pdf.set_text_color(0, 0, 0)
                pdf.cell(0, 8, ">> RÉSULTAT", ln=True)
                
                # Cadre Gris (Dessiné, pas de HTML)
                pdf.set_fill_color(248, 249, 250) # Gris très, très clair (Web style)
                pdf.set_draw_color(230, 230, 230) # Bordure fine grise
                
                # On sauvegarde la position Y avant d'écrire
                y_before = pdf.get_y()
                x_start = 20
                
                # On prépare le texte du résultat
                res_lines = pdf.multi_cell(0, 10, result_md, split_only=True)
                height = len(res_lines) * 10
                
                # On dessine le rectangle D'ABORD
                pdf.rect(x_start, y_before, 170, height, style='FD') # Fill + Draw
                
                # On écrit le texte DEDANS
                pdf.set_xy(x_start + 5, y_before) # Petit padding gauche
                pdf.set_font("Helvetica", "B", 12) # Résultat un peu plus gros
                pdf.multi_cell(160, 10, result_md) # Hauteur de ligne confortable
                
                pdf.ln(8)

            # --- 4. DISCLAIMER ---
            pdf.set_draw_color(240, 240, 240)
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
            logger.error(f"ERREUR GENERATION PDF : {e}")
            return None
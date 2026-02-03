from fpdf import FPDF, HTMLMixin
import datetime
import os
import re
from utils.helpers import logger

class SocialExpertPDF(FPDF, HTMLMixin):
    def header(self):
        # --- EN-TÊTE ---
        # 1. Logo à Gauche (X=20)
        logo_path = "avatar-logo.png"
        if os.path.exists(logo_path):
            try:
                self.image(logo_path, 20, 10, 18) 
            except:
                pass
        
        # 2. Nom de l'entreprise à Droite (Aligné R)
        self.set_y(12)
        self.set_font('Helvetica', 'B', 12)
        self.set_text_color(37, 62, 146) # Bleu Brand
        self.cell(0, 6, 'SOCIAL EXPERT FRANCE', ln=True, align='R')
        
        # Ligne de séparation très discrète
        self.ln(10)
        self.set_draw_color(230, 230, 230)
        self.line(20, 25, 190, 25)
        self.ln(10) # Espace avant le contenu

    def footer(self):
        self.set_y(-15) 
        self.set_font('Helvetica', '', 8)
        self.set_text_color(180, 180, 180) # Gris très clair
        self.cell(0, 10, f'{self.page_no()}/{{nb}}', align='C')

class ExportService:
    def __init__(self):
        self.logo_path = "avatar-logo.png"

    def _markdown_to_html(self, text):
        """
        Convertit le Markdown de l'IA en HTML simple pour fpdf2.
        Gère le gras inline (**texte**) et les listes.
        """
        if not text: return ""
        text = str(text)
        
        # 1. Nettoyage préliminaire
        text = text.replace("</h1>", "<br>").replace("</h2>", "<br>").replace("</h3>", "<br>")
        
        # 2. Conversion du GRAS (**texte** -> <b>texte</b>)
        # C'est la clé pour avoir "Analyse & Règles" en gras dans la ligne
        text = re.sub(r'\*\*(.*?)\*\*', r'<b>\1</b>', text)
        
        # 3. Conversion des LISTES
        # On transforme les tirets "- " en <li>...</li>
        lines = text.split('\n')
        html_lines = []
        in_list = False
        
        for line in lines:
            line = line.strip()
            if line.startswith('- ') or line.startswith('* '):
                content = line[2:]
                if not in_list:
                    html_lines.append('<ul>')
                    in_list = True
                html_lines.append(f'<li>{content}</li>')
            else:
                if in_list:
                    html_lines.append('</ul>')
                    in_list = False
                # Gestion des sauts de ligne
                if line:
                    html_lines.append(f'{line}<br>')
        
        if in_list: html_lines.append('</ul>')
        
        html_text = "".join(html_lines)
        
        # 4. Nettoyage final symboles
        html_text = html_text.replace("€", " EUR").replace("EUR", "<b>EUR</b>") # Petit bonus : EUR en gras
        
        return html_text

    def generate_pdf(self, user_query, ai_response):
        try:
            pdf = SocialExpertPDF()
            pdf.alias_nb_pages()
            pdf.add_page()
            pdf.set_margins(20, 20, 20)
            pdf.set_auto_page_break(auto=True, margin=20)
            
            # Préparation des textes
            html_response = self._markdown_to_html(ai_response)
            clean_query = user_query.replace("\n", " ")

            # --- 1. DATE (Sous le header, aligné gauche, style "Tag") ---
            pdf.set_y(30)
            pdf.set_font("Helvetica", "B", 10)
            pdf.set_text_color(20, 20, 20)
            date_str = datetime.datetime.now().strftime("%d/%m/%Y")
            pdf.cell(0, 6, f"Dossier du {date_str}", ln=True)
            pdf.ln(8)

            # --- 2. OBJET DE LA CONSULTATION ---
            pdf.set_font("Helvetica", "B", 11)
            pdf.set_text_color(0, 0, 0) # Noir
            pdf.cell(0, 6, "OBJET DE LA CONSULTATION", ln=True)
            pdf.ln(2)
            
            # Texte de la question (Normal)
            pdf.set_font("Helvetica", "", 10)
            pdf.multi_cell(0, 5, clean_query)
            
            # Ligne fine séparation
            pdf.ln(6)
            pdf.set_draw_color(230, 230, 230)
            pdf.line(20, pdf.get_y(), 190, pdf.get_y())
            pdf.ln(6)

            # --- 3. ANALYSE & CONTENU (Via HTML pour le gras inline) ---
            # On sépare le bloc résultat pour le traiter à part
            if ">> RÉSULTAT" in html_response:
                parts = html_response.split(">> RÉSULTAT")
                body_html = parts[0]
                # On nettoie le résultat pour garder juste la valeur
                raw_result = parts[1].replace("<br>", "").strip()
            else:
                body_html = html_response
                raw_result = ""

            # Titre Section
            pdf.set_font("Helvetica", "B", 11)
            pdf.cell(0, 6, "ANALYSE JURIDIQUE & SIMULATION", ln=True)
            pdf.ln(2)

            # CORPS DU TEXTE (HTML)
            # C'est ici que la magie opère pour les puces et le gras
            pdf.set_font("Helvetica", "", 10)
            pdf.set_text_color(30, 30, 30)
            
            # On injecte le HTML. fpdf2 va gérer les <b> et <li>
            pdf.write_html(body_html)
            
            pdf.ln(4)

            # --- 4. RÉSULTAT (Style Capture : Titre puis Valeur Grise) ---
            if raw_result:
                # Titre
                pdf.set_font("Helvetica", "B", 11)
                pdf.set_text_color(0, 0, 0)
                pdf.cell(0, 8, ">> RÉSULTAT", ln=True)
                
                # Puce "Résultat" (Fond gris clair, texte gras)
                pdf.set_fill_color(245, 247, 250) # Gris très léger
                pdf.set_font("Helvetica", "B", 11)
                
                # On nettoie le HTML résiduel du résultat
                clean_res = re.sub(r'<[^>]+>', '', raw_result).strip()
                
                # Affichage dans une cellule grise
                pdf.cell(0, 10, f"  {clean_res}  ", ln=True, fill=True)
                pdf.ln(8)

            # --- 5. DISCLAIMER & SOURCES ---
            # Ligne séparation
            pdf.set_draw_color(230, 230, 230)
            pdf.line(20, pdf.get_y(), 190, pdf.get_y())
            pdf.ln(6)

            # Disclaimer (Italique)
            pdf.set_font("Helvetica", "I", 9)
            pdf.set_text_color(100, 100, 100)
            pdf.multi_cell(0, 4, "Données certifiées conformes aux barèmes 2026.")
            pdf.ln(2)
            
            # Document Confidentiel (Gras + Normal)
            pdf.set_font("Helvetica", "B", 9)
            pdf.write(4, "DOCUMENT CONFIDENTIEL ")
            pdf.set_font("Helvetica", "", 9)
            pdf.write(4, "Simulation établie sur la base des barèmes 2026. Ne remplace pas un conseil juridique.")

            return bytes(pdf.output())

        except Exception as e:
            logger.error(f"ERREUR PDF HTML : {e}")
            # Fallback en cas d'erreur HTML (sécurité)
            return None
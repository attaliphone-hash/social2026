from fpdf import FPDF
import datetime
import os
import re
from utils.helpers import logger

class SocialExpertPDF(FPDF):
    def header(self):
        # --- EN-TÊTE ---
        # Logo (Aligné à gauche)
        logo_path = "avatar-logo.png"
        if os.path.exists(logo_path):
            try:
                self.image(logo_path, 20, 10, 18) 
            except:
                pass
        
        # Titre Entreprise (Aligné à droite)
        self.set_y(12)
        self.set_font('Helvetica', 'B', 12) # Helvetica = Look moderne
        self.set_text_color(37, 62, 146)    # Bleu Brand
        self.cell(0, 6, 'SOCIAL EXPERT FRANCE', ln=True, align='R')
        
        # Espace après header
        self.ln(15) 

    def footer(self):
        self.set_y(-20) 
        self.set_font('Helvetica', '', 8)
        self.set_text_color(150, 150, 150) # Gris clair
        self.cell(0, 10, f'Page {self.page_no()}/{{nb}}', align='C')

class ExportService:
    def __init__(self):
        self.logo_path = "avatar-logo.png"

    def _clean_text_for_pdf(self, text):
        if text is None: return ""
        text = str(text)
        
        # Préservation de la structure "Liste" (Bullet points)
        structure_replacements = {
            "</h1>": "\n", "</h2>": "\n", "</h3>": "\n", "</h4>": "\n",
            "</p>": "\n", "</div>": "\n", "<br>": "\n", "<br/>": "\n",
            "<li>": "  • ", "</li>": "\n", # Puce ronde comme sur le web
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
            # Marges 20mm (Aéré)
            pdf.set_margins(20, 20, 20)
            
            clean_query = self._clean_text_for_pdf(user_query)
            clean_response = self._clean_text_for_pdf(ai_response)

            # --- EXTRACTION (Résultat & Sources) ---
            if ">> RÉSULTAT" in clean_response:
                parts = clean_response.split(">> RÉSULTAT")
                body_text = parts[0]
                result_text = parts[1].strip() # On enlève le ">> RÉSULTAT" du texte pour le gérer manuellement
            else:
                body_text = clean_response
                result_text = ""
            
            sources_text = ""
            keyword_sources = "Sources utilisées"
            
            # Recherche des sources dans le corps ou le résultat
            if keyword_sources in body_text:
                sub_parts = body_text.split(keyword_sources)
                body_text = sub_parts[0]
                sources_text = sub_parts[1]
            elif keyword_sources in result_text:
                sub_parts = result_text.split(keyword_sources)
                result_text = sub_parts[0]
                sources_text = sub_parts[1]

            # ==========================================
            # DÉBUT DU DOCUMENT (Style Capture d'écran)
            # ==========================================

            # 1. DATE (Gras, Noir)
            pdf.set_font("Helvetica", "B", 11)
            pdf.set_text_color(0, 0, 0)
            date_str = datetime.datetime.now().strftime("%d/%m/%Y")
            pdf.cell(0, 8, f"Dossier du {date_str}", ln=True)
            pdf.ln(4)

            # 2. OBJET DE LA CONSULTATION (Titre Majuscule)
            pdf.set_font("Helvetica", "B", 11) # Gras
            pdf.cell(0, 8, "OBJET DE LA CONSULTATION", ln=True)
            
            # Contenu Objet (Normal, Aéré)
            pdf.set_font("Helvetica", "", 10)
            pdf.multi_cell(0, 5, clean_query)
            
            # Ligne de séparation fine et discrète
            pdf.ln(6)
            pdf.set_draw_color(220, 220, 220) # Gris très clair
            pdf.line(20, pdf.get_y(), 190, pdf.get_y())
            pdf.ln(6)

            # 3. ANALYSE JURIDIQUE & SIMULATION
            pdf.set_font("Helvetica", "B", 11)
            pdf.cell(0, 8, "ANALYSE JURIDIQUE & SIMULATION", ln=True)
            pdf.ln(2)

            # Corps du texte (Analyse)
            # On imprime le corps tel quel. L'IA structure déjà avec des retours à la ligne.
            # Helvetica 10 pour le corps (lisible et propre)
            pdf.set_font("Helvetica", "", 10)
            pdf.set_text_color(20, 20, 20) # Noir doux
            
            # Astuce : On essaye de détecter les sous-titres "Analyse & Règles" et "Détail & Chiffres" 
            # pour les mettre en gras si possible, sinon on imprime tout le bloc.
            # Pour simplifier et garantir la robustesse : on imprime le bloc propre.
            pdf.multi_cell(0, 5, body_text.strip())
            
            pdf.ln(6)

            # 4. LE RÉSULTAT (Style ">> RÉSULTAT")
            if result_text:
                # Titre du résultat
                pdf.set_font("Helvetica", "B", 11)
                pdf.set_text_color(0, 0, 0)
                pdf.cell(0, 8, ">> RÉSULTAT", ln=True)
                
                # Valeur du résultat (Gras, un peu plus grand, Noir)
                pdf.set_font("Helvetica", "B", 11) 
                pdf.multi_cell(0, 6, result_text.strip())
                
                pdf.ln(4)
                # Ligne fine sous le résultat
                pdf.set_draw_color(220, 220, 220)
                pdf.line(20, pdf.get_y(), 190, pdf.get_y())
                pdf.ln(6)

            # 5. SOURCES (Style "Label: Valeur")
            if sources_text:
                pdf.set_font("Helvetica", "B", 10) # Label "Sources utilisées" en gras
                pdf.write(5, "Sources utilisées : ")
                
                pdf.set_font("Helvetica", "", 10) # Texte des sources normal
                pdf.write(5, sources_text.strip())
                pdf.ln(10)

            # 6. DISCLAIMER / PIED DE PAGE (Style italique)
            # Gestion saut de page
            if pdf.get_y() > 250: pdf.add_page()
            
            # Texte "Données certifiées..." (Italique)
            pdf.set_font("Helvetica", "I", 10)
            pdf.set_text_color(50, 50, 50)
            pdf.cell(0, 5, "Données certifiées conformes aux barèmes 2026.", ln=True)
            pdf.ln(4)

            # Bloc "DOCUMENT CONFIDENTIEL" (Gras + Normal)
            pdf.set_font("Helvetica", "B", 10)
            pdf.write(5, "DOCUMENT CONFIDENTIEL ")
            pdf.set_font("Helvetica", "", 10)
            pdf.write(5, "Simulation établie sur la base des barèmes 2026. Ne remplace pas un conseil juridique.")
            pdf.ln()

            return bytes(pdf.output())

        except Exception as e:
            logger.error(f"ERREUR PDF : {e}")
            return None
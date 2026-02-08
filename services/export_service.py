"""
==============================================================================
SERVICE D'EXPORT PDF - SOCIAL EXPERT FRANCE
VERSION : 4.0
DATE : 08/02/2026
==============================================================================
"""

from fpdf import FPDF
import datetime
import os
import re
from utils.helpers import logger


class SocialExpertPDF(FPDF):
    """Classe PDF personnalisée avec header et footer Social Expert."""
    
    def header(self):
        """En-tête du document."""
        logo_path = "avatar-logo.png"
        if os.path.exists(logo_path):
            try:
                self.image(logo_path, 20, 10, 18)
            except RuntimeError as e:
                logger.warning(f"Impossible de charger le logo: {e}")
        
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
        """Pied de page du document."""
        self.set_y(-15)
        self.set_font('Helvetica', '', 8)
        self.set_text_color(128)
        self.cell(0, 10, f'Page {self.page_no()}/{{nb}}', align='C')


class ExportService:
    """Service d'export des consultations en PDF."""
    
    def __init__(self):
        self.logo_path = "avatar-logo.png"
    
    def _clean_markdown_for_pdf(self, text: str) -> str:
        """
        Nettoie le texte Markdown pour l'export PDF.
        
        Args:
            text: Texte Markdown brut
            
        Returns:
            Texte nettoyé compatible PDF
        """
        if not text:
            return ""
        
        text = str(text)
        
        # Sécurité : suppression des balises HTML
        text = re.sub(r'<[^>]+>', '', text)
        
        lines = []
        for line in text.split('\n'):
            line = line.strip()
            
            # Conversion Titres Markdown -> Gras PDF
            if line.startswith('### ') or line.startswith('## '):
                content = line.replace('#', '').strip()
                line = f"\n**{content}**"
            
            # Conversion Bullet Points
            elif line.startswith('- ') or line.startswith('* '):
                line = "  - " + line[2:].strip()
            
            # Conversion listes numérotées
            elif re.match(r'^\d+\.\s', line):
                line = "  " + line
            
            lines.append(line)
        
        text = "\n".join(lines)
        
        # Remplacements de caractères spéciaux
        replacements = {
            "&nbsp;": " ",
            "&euro;": " EUR",
            "€": " EUR",
            "🎯": ">> ",
            "✅": "[OK] ",
            "❌": "[X] ",
            "⚠️": "[!] ",
            "📄": "",
            "🔍": "",
            "💡": "",
        }
        
        for old, new in replacements.items():
            text = text.replace(old, new)
        
        # Encodage sécurisé pour FPDF (latin-1 avec fallback)
        try:
            # Essayer d'abord UTF-8 via unicode_escape pour garder les accents
            text = text.encode('latin-1', 'replace').decode('latin-1')
        except (UnicodeEncodeError, UnicodeDecodeError) as e:
            logger.warning(f"Encodage PDF fallback: {e}")
            # Fallback agressif : supprimer tous les caractères non-ASCII
            text = text.encode('ascii', 'ignore').decode('ascii')
        
        return text
    
    def _extract_sections(self, ai_response: str) -> tuple:
        """
        Extrait les sections de la réponse IA.
        
        Args:
            ai_response: Réponse complète de l'IA
            
        Returns:
            Tuple (body, result, sources)
        """
        body = ai_response
        result = ""
        sources = ""
        
        # Extraction du RÉSULTAT
        if "RÉSULTAT" in ai_response:
            parts = ai_response.split("RÉSULTAT", 1)
            body = parts[0]
            rest = parts[1] if len(parts) > 1 else ""
            
            # Extraction des Sources
            if "Sources" in rest:
                sub = rest.split("Sources", 1)
                result = sub[0]
                sources = "Sources" + sub[1] if len(sub) > 1 else ""
            else:
                result = rest
        
        # Fallback si pas de section RÉSULTAT
        elif "Sources" in ai_response:
            parts = ai_response.split("Sources", 1)
            body = parts[0]
            sources = "Sources" + parts[1] if len(parts) > 1 else ""
        
        return body, result, sources
    
    def generate_pdf(self, user_query: str, ai_response: str) -> bytes:
        """
        Génère un PDF de la consultation.
        
        Args:
            user_query: Question de l'utilisateur
            ai_response: Réponse de l'IA
            
        Returns:
            Bytes du PDF généré, ou None en cas d'erreur
        """
        try:
            pdf = SocialExpertPDF()
            pdf.alias_nb_pages()
            pdf.add_page()
            pdf.set_margins(20, 20, 20)
            pdf.set_auto_page_break(auto=True, margin=20)
            
            # Nettoyage des contenus
            clean_query = self._clean_markdown_for_pdf(user_query)
            body, result, sources = self._extract_sections(ai_response)
            
            clean_body = self._clean_markdown_for_pdf(body).replace(">>", "")
            clean_result = self._clean_markdown_for_pdf(result).replace(":", "").strip()
            clean_sources = self._clean_markdown_for_pdf(sources).strip()
            
            # ===== DESSIN DU DOCUMENT =====
            
            # Date du dossier
            pdf.set_y(45)
            pdf.set_font("Helvetica", "B", 10)
            pdf.set_text_color(100)
            pdf.set_fill_color(240)
            date_str = datetime.datetime.now().strftime('%d/%m/%Y')
            pdf.cell(40, 8, f"  Dossier du {date_str}  ", ln=True, fill=True, align='C')
            pdf.ln(8)
            
            # Section : Objet de la consultation
            pdf.set_font("Helvetica", "B", 11)
            pdf.set_text_color(0)
            pdf.cell(0, 6, "OBJET DE LA CONSULTATION", ln=True)
            pdf.ln(2)
            pdf.set_font("Helvetica", "", 11)
            pdf.multi_cell(0, 6, clean_query)
            pdf.ln(6)
            
            # Ligne de séparation
            pdf.set_draw_color(220)
            pdf.line(20, pdf.get_y(), 190, pdf.get_y())
            pdf.ln(8)
            
            # Section : Analyse juridique
            pdf.set_font("Helvetica", "B", 11)
            pdf.cell(0, 6, "ANALYSE JURIDIQUE & SIMULATION", ln=True)
            pdf.ln(4)
            pdf.set_font("Helvetica", "", 11)
            pdf.set_text_color(20)
            
            try:
                pdf.multi_cell(0, 6, clean_body, markdown=True)
            except TypeError:
                # Fallback si markdown=True non supporté
                pdf.multi_cell(0, 6, clean_body)
            
            pdf.ln(8)
            
            # Section : Résultat (si présent)
            if clean_result:
                pdf.set_font("Helvetica", "B", 11)
                pdf.set_text_color(0)
                pdf.cell(0, 8, ">> RESULTAT", ln=True)
                pdf.set_font("Helvetica", "B", 12)
                # Suppression des ** du markdown
                pdf.multi_cell(0, 8, clean_result.replace("**", ""))
                pdf.ln(4)
            
            # Section : Sources (si présentes)
            if clean_sources:
                pdf.ln(2)
                pdf.set_font("Helvetica", "", 9)
                pdf.set_text_color(80)
                pdf.multi_cell(0, 5, clean_sources)
                pdf.ln(8)
            
            # Disclaimer final
            pdf.set_draw_color(220)
            pdf.line(20, pdf.get_y(), 190, pdf.get_y())
            pdf.ln(6)
            pdf.set_text_color(100)
            pdf.set_font("Helvetica", "B", 9)
            pdf.write(5, "DOCUMENT CONFIDENTIEL ")
            pdf.set_font("Helvetica", "", 9)
            pdf.write(5, "Simulation etablie sur la base des baremes 2026. Ne remplace pas un conseil juridique.")
            
            return bytes(pdf.output())
        
        except ValueError as e:
            logger.error(f"Erreur valeur PDF: {e}")
            return None
        except RuntimeError as e:
            logger.error(f"Erreur runtime PDF: {e}")
            return None
        except Exception as e:
            logger.error(f"Erreur inattendue PDF: {e}", exc_info=True)
            return None

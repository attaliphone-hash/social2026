from fpdf import FPDF
from datetime import datetime
from bs4 import BeautifulSoup

class PDFReport(FPDF):
    def header(self):
        # En-tête plus compact
        self.set_font('Helvetica', 'B', 12) # Taille réduite (15 -> 12)
        self.set_text_color(2, 76, 111) 
        self.cell(0, 8, 'EXPERT SOCIAL PRO - Rapport de Recherche', 0, 1, 'C') # Hauteur réduite (10 -> 8)
        self.ln(2) # Espace réduit après le titre

    def footer(self):
        self.set_y(-12) # Remonte un peu le pied de page
        self.set_font('Helvetica', 'I', 7) # Plus petit
        self.set_text_color(128)
        self.cell(0, 10, f'Page {self.page_no()}/{{nb}}', 0, 0, 'C')

def clean_text(text):
    """
    Nettoie, TRADUIT les emojis et gère l'EURO.
    """
    # 1. Dictionnaire de traduction (Emojis & Symboles)
    replacements = {
        "€": " EUR", # Sécurité pour le symbole Euro
        "🚨": "[ATTENTION] ",
        "⚠️": "[AVERTISSEMENT] ",
        "✅": "[OK] ",
        "❌": "[NON] ",
        "💡": "[CONSEIL] ",
        "👉": "> ",
        "🛑": "[STOP] ",
        "📍": "[POINT] ",
        "ℹ️": "[INFO] ",
        "📅": "[DATE] "
    }
    
    for original, replacement in replacements.items():
        text = text.replace(original, replacement)

    # 2. Nettoyage HTML
    soup = BeautifulSoup(text, "html.parser")
    text_plain = soup.get_text(separator="\n")
    
    # 3. Encodage final (Latin-1)
    return text_plain.encode('latin-1', 'ignore').decode('latin-1')

def create_pdf_report(user_question, ai_response, sources_list):
    # On initialise avec une marge un peu plus fine (10mm au lieu de défaut)
    pdf = PDFReport()
    pdf.set_margins(15, 15, 15) 
    pdf.alias_nb_pages()
    pdf.add_page()
    
    # 1. QUESTION (Compact)
    pdf.set_font('Helvetica', 'B', 10)
    pdf.set_text_color(0)
    pdf.cell(0, 6, "VOTRE QUESTION :", 0, 1, 'L')
    
    pdf.set_font('Helvetica', '', 10)
    # multi_cell(w, h, txt) -> On passe h à 5 (interligne serré)
    pdf.multi_cell(0, 5, clean_text(user_question))
    pdf.ln(3) # Petit saut seulement
    
    # 2. RÉPONSE (Compact)
    pdf.set_font('Helvetica', 'B', 10)
    pdf.set_text_color(2, 76, 111) # Bleu pro
    pdf.cell(0, 8, "ANALYSE DE L'EXPERT :", 0, 1, 'L')
    
    pdf.set_font('Helvetica', '', 10)
    # Le coeur du gain de place est ici : interligne de 5mm
    pdf.multi_cell(0, 5, clean_text(ai_response))
    pdf.ln(5)
    
    # 3. SOURCES (Très compact, en gris)
    pdf.set_font('Helvetica', 'B', 9)
    pdf.set_text_color(80)
    pdf.cell(0, 6, "SOURCES :", 0, 1, 'L')
    
    pdf.set_font('Helvetica', 'I', 8) # Tout petit pour les sources
    pdf.set_text_color(100)
    pdf.multi_cell(0, 4, clean_text(sources_list)) # Interligne très fin (4mm)
    pdf.ln(5)
    
    # 4. DISCLAIMER
    pdf.set_font('Helvetica', 'I', 6) # Minuscule pour le légal
    pdf.set_text_color(150)
    pdf.multi_cell(0, 3, "Document genere par IA a titre informatif. Ne remplace pas un avis juridique.")

    # Retour en bytes pour Streamlit
    return bytes(pdf.output())
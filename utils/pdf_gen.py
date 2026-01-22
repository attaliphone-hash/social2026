from fpdf import FPDF
from datetime import datetime
from bs4 import BeautifulSoup

class PDFReport(FPDF):
    def header(self):
        self.set_font('Helvetica', 'B', 15)
        self.set_text_color(2, 76, 111) 
        self.cell(0, 10, 'EXPERT SOCIAL PRO - Rapport', 0, 1, 'C')
        self.ln(5)

    def footer(self):
        self.set_y(-15)
        self.set_font('Helvetica', 'I', 8)
        self.set_text_color(128)
        self.cell(0, 10, f'Page {self.page_no()}/{{nb}}', 0, 0, 'C')

def clean_text(text):
    """
    Nettoie et TRADUIT les emojis en texte lisible.
    """
    # 1. Dictionnaire de traduction (Emojis -> Texte)
    replacements = {
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
    
    # 2. On applique les remplacements
    for emoji, texte_remplacement in replacements.items():
        text = text.replace(emoji, texte_remplacement)

    # 3. Nettoyage HTML classique
    soup = BeautifulSoup(text, "html.parser")
    text_plain = soup.get_text(separator="\n")
    
    # 4. Encodage final (si un emoji inconnu reste, il est supprimé proprement)
    return text_plain.encode('latin-1', 'ignore').decode('latin-1')

def create_pdf_report(user_question, ai_response, sources_list):
    pdf = PDFReport()
    pdf.alias_nb_pages()
    pdf.add_page()
    
    # 1. QUESTION
    pdf.set_font('Helvetica', 'B', 12)
    pdf.set_text_color(0)
    pdf.cell(0, 10, "VOTRE QUESTION :", 0, 1, 'L')
    
    pdf.set_font('Helvetica', '', 11)
    pdf.multi_cell(0, 7, clean_text(user_question))
    pdf.ln(5)
    
    # 2. REPONSE
    pdf.set_font('Helvetica', 'B', 12)
    pdf.cell(0, 10, "ANALYSE DE L'EXPERT :", 0, 1, 'L')
    
    pdf.set_font('Helvetica', '', 10)
    pdf.multi_cell(0, 6, clean_text(ai_response))
    pdf.ln(5)
    
    # 3. SOURCES
    pdf.set_font('Helvetica', 'B', 11)
    pdf.set_text_color(2, 76, 111)
    pdf.cell(0, 10, "SOURCES :", 0, 1, 'L')
    
    pdf.set_font('Helvetica', 'I', 9)
    pdf.set_text_color(50)
    pdf.multi_cell(0, 6, clean_text(sources_list))
    pdf.ln(10)
    
    # 4. DISCLAIMER
    pdf.set_font('Helvetica', 'I', 7)
    pdf.set_text_color(100)
    pdf.multi_cell(0, 4, "Document genere par IA a titre informatif.")

    return pdf.output(dest='S')
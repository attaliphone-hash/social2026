from fpdf import FPDF
from datetime import datetime
from bs4 import BeautifulSoup

class PDFReport(FPDF):
    def header(self):
        self.set_font('Helvetica', 'B', 11) # Police titre réduite
        self.set_text_color(2, 76, 111) 
        self.cell(0, 6, 'EXPERT SOCIAL PRO - Rapport', 0, 1, 'C') # Hauteur réduite
        self.ln(2)

    def footer(self):
        self.set_y(-10) # Pied de page très bas (10mm)
        self.set_font('Helvetica', 'I', 7)
        self.set_text_color(128)
        self.cell(0, 10, f'Page {self.page_no()}/{{nb}}', 0, 0, 'C')

def clean_text(text):
    """
    Nettoie, TRADUIT les emojis et COMPRESSE les sauts de ligne.
    """
    # 1. Dictionnaire de traduction
    replacements = {
        "€": " EUR",
        "🚨": "[ATTENTION] ", "⚠️": "[AVERTISSEMENT] ",
        "✅": "[OK] ", "❌": "[NON] ", "💡": "[CONSEIL] ",
        "👉": "> ", "🛑": "[STOP] ", "📍": "[POINT] ",
        "ℹ️": "[INFO] ", "📅": "[DATE] "
    }
    
    for original, replacement in replacements.items():
        text = text.replace(original, replacement)

    # 2. Nettoyage HTML
    soup = BeautifulSoup(text, "html.parser")
    # Astuce : on utilise un espace vide au lieu de \n par défaut, 
    # puis on gère les paragraphes manuellement si besoin
    text_plain = soup.get_text(separator="\n")
    
    # 3. COMPRESSION AGRESSIVE (C'est ici que ça se joue)
    # On enlève les doubles/triples sauts de ligne inutiles
    while "\n\n" in text_plain:
        text_plain = text_plain.replace("\n\n", "\n")
        
    # On enlève les espaces en début/fin
    text_plain = text_plain.strip()
    
    # 4. Encodage final
    return text_plain.encode('latin-1', 'ignore').decode('latin-1')

def create_pdf_report(user_question, ai_response, sources_list):
    # MARGES ULTRA FINES : 10mm partout (gagne beaucoup de place)
    pdf = PDFReport()
    pdf.set_margins(10, 10, 10)
    pdf.set_auto_page_break(auto=True, margin=8) # Écrit jusqu'à 8mm du bas
    pdf.alias_nb_pages()
    pdf.add_page()
    
    # 1. QUESTION
    pdf.set_font('Helvetica', 'B', 10)
    pdf.set_text_color(0)
    pdf.cell(0, 5, "VOTRE QUESTION :", 0, 1, 'L')
    
    pdf.set_font('Helvetica', '', 10)
    pdf.multi_cell(0, 4.5, clean_text(user_question)) # Interligne 4.5mm
    pdf.ln(2) # Espace minuscule
    
    # 2. REPONSE
    pdf.set_font('Helvetica', 'B', 10)
    pdf.set_text_color(2, 76, 111)
    pdf.cell(0, 6, "ANALYSE DE L'EXPERT :", 0, 1, 'L')
    
    pdf.set_font('Helvetica', '', 10)
    # Le texte de l'IA est maintenant "compacté" (plus de trous)
    pdf.multi_cell(0, 4.5, clean_text(ai_response))
    pdf.ln(3)
    
    # 3. SOURCES
    pdf.set_font('Helvetica', 'B', 9)
    pdf.set_text_color(80)
    pdf.cell(0, 5, "SOURCES :", 0, 1, 'L')
    
    pdf.set_font('Helvetica', 'I', 8)
    pdf.set_text_color(100)
    pdf.multi_cell(0, 4, clean_text(sources_list))
    pdf.ln(3)
    
    # 4. DISCLAIMER
    pdf.set_font('Helvetica', 'I', 6)
    pdf.set_text_color(150)
    pdf.multi_cell(0, 3, "Document genere par IA a titre informatif. Ne remplace pas un avis juridique.")

    return bytes(pdf.output())
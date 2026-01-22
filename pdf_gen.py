from fpdf import FPDF
from datetime import datetime
from bs4 import BeautifulSoup
import re

class PDFReport(FPDF):
    def header(self):
        # Titre / En-tête
        self.set_font('Helvetica', 'B', 15)
        self.set_text_color(2, 76, 111) # Le Bleu de ton site
        self.cell(0, 10, 'EXPERT SOCIAL PRO - Rapport de Recherche', 0, 1, 'C')
        self.ln(5)

    def footer(self):
        # Pied de page
        self.set_y(-15)
        self.set_font('Helvetica', 'I', 8)
        self.set_text_color(128)
        self.cell(0, 10, f'Page {self.page_no()}/{{nb}} - Généré le {datetime.now().strftime("%d/%m/%Y à %H:%M")}', 0, 0, 'C')

def clean_html_for_pdf(html_text):
    """Nettoie le HTML de l'IA pour le rendre lisible en texte brut dans le PDF"""
    soup = BeautifulSoup(html_text, "html.parser")
    return soup.get_text(separator="\n\n")

def create_pdf_report(user_question, ai_response, sources_list):
    pdf = PDFReport()
    pdf.alias_nb_pages()
    pdf.add_page()
    
    # 1. LA QUESTION
    pdf.set_font('Helvetica', 'B', 12)
    pdf.set_text_color(0)
    pdf.cell(0, 10, "VOTRE QUESTION :", 0, 1, 'L')
    
    pdf.set_font('Helvetica', '', 11)
    pdf.multi_cell(0, 7, user_question)
    pdf.ln(5)
    
    # 2. LA RÉPONSE (Nettoyée)
    pdf.set_font('Helvetica', 'B', 12)
    pdf.cell(0, 10, "ANALYSE DE L'EXPERT :", 0, 1, 'L')
    
    pdf.set_font('Helvetica', '', 10)
    # On nettoie le HTML pour avoir du texte propre
    clean_response = clean_html_for_pdf(ai_response)
    pdf.multi_cell(0, 6, clean_response)
    pdf.ln(5)
    
    # 3. LES SOURCES
    pdf.set_font('Helvetica', 'B', 11)
    pdf.set_text_color(2, 76, 111)
    pdf.cell(0, 10, "SOURCES UTILISÉES :", 0, 1, 'L')
    
    pdf.set_font('Helvetica', 'I', 9)
    pdf.set_text_color(50)
    pdf.multi_cell(0, 6, sources_list)
    pdf.ln(10)
    
    # 4. DISCLAIMER JURIDIQUE
    pdf.set_font('Helvetica', 'I', 7)
    pdf.set_text_color(100)
    pdf.multi_cell(0, 4, "AVERTISSEMENT : Ce document est généré par une IA à titre informatif. Il ne remplace pas une consultation juridique signée par un avocat ou un expert-comptable. Expert Social Pro décline toute responsabilité en cas d'utilisation contentieuse.")

    # Retourne les données binaires du PDF
    return pdf.output(dest='S')
from fpdf import FPDF
import datetime
import os

class ExportService:
    def __init__(self):
        self.logo_path = "avatar-logo.png"

    def generate_pdf(self, user_query, ai_response):
        pdf = FPDF()
        pdf.add_page()
        
        # 1. En-tête avec Logo
        if os.path.exists(self.logo_path):
            pdf.image(self.logo_path, 10, 8, 25)
        
        pdf.set_font("helvetica", "B", 16)
        pdf.set_text_color(37, 62, 146) # Votre bleu #253E92
        pdf.cell(0, 10, "SOCIAL EXPERT FRANCE", ln=True, align="R")
        
        pdf.set_font("helvetica", "I", 10)
        pdf.set_text_color(100, 100, 100)
        date_str = datetime.datetime.now().strftime("%d/%m/%Y %H:%M")
        pdf.cell(0, 10, f"Simulation générée le {date_str}", ln=True, align="R")
        
        pdf.ln(20)
        
        # 2. Objet de la demande
        pdf.set_fill_color(240, 248, 255)
        pdf.set_font("helvetica", "B", 12)
        pdf.set_text_color(0, 0, 0)
        pdf.cell(0, 10, " OBJET DE LA CONSULTATION :", ln=True, fill=True)
        pdf.set_font("helvetica", "", 11)
        pdf.multi_cell(0, 10, user_query)
        
        pdf.ln(10)
        
        # 3. Analyse et Résultats (Nettoyage du HTML pour le PDF)
        pdf.set_font("helvetica", "B", 12)
        pdf.set_text_color(37, 62, 146)
        pdf.cell(0, 10, "ANALYSE JURIDIQUE ET SIMULATION :", ln=True)
        
        pdf.set_font("helvetica", "", 11)
        pdf.set_text_color(0, 0, 0)
        
        # Nettoyage simple des balises HTML courantes pour le PDF
        clean_text = ai_response.replace("<h4>", "").replace("</h4>", "\n")
        clean_text = clean_text.replace("<ul>", "").replace("</ul>", "")
        clean_text = clean_text.replace("<li>", "- ").replace("</li>", "\n")
        clean_text = clean_text.replace("<strong>", "").replace("</strong>", "")
        clean_text = clean_text.replace("<br>", "\n").replace("<div style=\"background-color: #f9f9f9; padding: 15px; border-radius: 5px;\">", "\n--- DÉTAILS ---\n")
        clean_text = clean_text.replace("<div style=\"background-color: #f0f8ff; padding: 20px; border-left: 5px solid #024c6f; margin: 25px 0;\">", "\n--- RÉSULTAT FINAL ---\n")
        clean_text = clean_text.replace("</div>", "\n")
        
        pdf.multi_cell(0, 7, clean_text)
        
        pdf.ln(10)
        
        # 4. Pied de page / Clause de non-responsabilité
        pdf.ln(5)
        pdf.set_font("helvetica", "I", 8)
        pdf.set_text_color(120, 120, 120)
        
        disclaimer = (
            "AVERTISSEMENT : Ce compte-rendu est une simulation automatisée établie selon les barèmes 2026. "
            "Il est exclusivement destiné à faciliter la réflexion de l'utilisateur et ne constitue en aucun cas "
            "un acte de conseil juridique. Social Expert France ne saurait être tenu pour responsable de l'usage "
            "fait de ces calculs. Seul un examen approfondi de votre dossier par un professionnel qualifié "
            "(expert-comptable ou avocat) peut garantir une sécurité juridique totale."
        )
        pdf.multi_cell(0, 5, disclaimer, align="C")
        
        return pdf.output()
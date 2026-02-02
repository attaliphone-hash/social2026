import os
import logging

# Configuration du logging centralisé (Point 1 de l'audit)
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("SocialPro2026")

def clean_source_name(filename, category="AUTRE"):
    """Fonction unique de nettoyage (Supprime la duplication app/ia_service)"""
    filename = os.path.basename(filename).replace('.pdf', '').replace('.txt', '')
    
    if "Code_Travail" in filename: return "Code du Travail 2026"
    if "Code_Secu" in filename: return "Code de la Sécurité Sociale 2026"
    if category == "REF" or filename.startswith("REF_"): return "Barèmes Officiels 2026"
    if category == "DOC" or filename.startswith("DOC_"): return "BOSS 2026 et Jurisprudences"
    
    return filename.replace('_', ' ')
import logging
import re
import os

# --- CONFIGURATION DU LOGGER ---
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),  # Affiche dans la console
        logging.FileHandler("app_debug.log", mode='a', encoding='utf-8')  # Sauvegarde dans un fichier
    ]
)
logger = logging.getLogger("SocialExpert")

def clean_source_name(filename):
    """
    Transforme un nom de fichier technique (REF_Code_Travail.pdf) en nom lisible (Code du Travail).
    """
    if not filename: return "Document Inconnu"
    
    name = os.path.basename(filename)
    name = name.replace(".pdf", "").replace(".txt", "")
    
    # Dictionnaire de remplacement pour faire "Pro"
    replacements = {
        "REF_": "",
        "Code_Travail": "Code du Travail",
        "Barème_URSSAF": "Barème URSSAF",
        "BOSS_": "BOSS - ",
        "_": " "
    }
    
    for old, new in replacements.items():
        name = name.replace(old, new)
    
    return name.strip()
import logging
import re
import os

# --- CONFIGURATION DU LOGGER ---
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("app_debug.log", mode='a', encoding='utf-8')
    ]
)
logger = logging.getLogger("SocialExpert")

# ✅ CORRECTION : On ajoute l'argument 'category' (même optionnel) pour éviter le crash
def clean_source_name(filename, category=None):
    """
    Transforme un nom de fichier technique en nom lisible.
    Accepte une catégorie optionnelle pour compatibilité future.
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
    
    # (Optionnel) Si vous vouliez utiliser la catégorie plus tard, c'est ici :
    # if category and category != "AUTRE":
    #     name = f"[{category}] {name}"

    return name.strip()
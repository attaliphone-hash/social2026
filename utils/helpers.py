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

def clean_source_name(filename, category=None):
    """Transforme un nom de fichier technique en nom lisible."""
    if not filename: return "Document Inconnu"
    name = os.path.basename(filename).replace(".pdf", "").replace(".txt", "")
    replacements = {"REF_": "", "Code_Travail": "Code du Travail", "Barème_URSSAF": "Barème URSSAF", "BOSS_": "BOSS - ", "_": " "}
    for old, new in replacements.items(): name = name.replace(old, new)
    return name.strip()

# ✅ AJOUT AUDIT SÉCURITÉ
def sanitize_user_input(text, max_length=5000):
    """
    Nettoie les entrées utilisateur :
    - Coupe si trop long.
    - Retire les caractères de contrôle invisibles (sauf sauts de ligne).
    """
    if not text: return ""
    text = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]', '', text)
    return text[:max_length].strip()
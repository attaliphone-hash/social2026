import logging
import re
import os

# --- CONFIGURATION DU LOGGER (RESTAURATION INTÉGRALE) ---
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
    """
    Transforme un nom de fichier technique en nom lisible ET purge les dates.
    EMPECHE LE MIMÉTISME DE L'IA SUR LES SOURCES (ex: évite "Janvier 2026").
    """
    if not filename: 
        return "Document Inconnu"
    
    # 1. Extraction du nom de base
    name = os.path.basename(filename).replace(".pdf", "").replace(".txt", "")
    
    # 2. FILTRE PURIFICATEUR : Supprime mois et années (2024-2026)
    # Cette regex cible les mentions temporelles fr/en pour que l'IA ne les voit plus.
    pattern_dates = r"(?i)(-?\s?(janvier|février|mars|avril|mai|juin|juillet|août|septembre|octobre|novembre|décembre|january|february|march|april|may|june|july|august|september|october|november|december|2024|2025|2026)\s?-?)"
    name = re.sub(pattern_dates, " ", name)

    # 3. MAPPING DES REMPLACEMENTS (CONSERVATION DE TA LOGIQUE)
    replacements = {
        "REF_": "", 
        "Code_Travail": "Code du Travail", 
        "Barème_URSSAF": "Barème URSSAF", 
        "BOSS_": "BOSS - ", 
        "_": " "
    }
    
    for old, new in replacements.items(): 
        name = name.replace(old, new)
    
    # 4. NETTOYAGE DES ESPACES DOUBLES
    name = re.sub(r'\s+', ' ', name).strip()
    
    return name

# ✅ AJOUT AUDIT SÉCURITÉ (RESTAURATION INTÉGRALE)
def sanitize_user_input(text, max_length=5000):
    """
    Nettoie les entrées utilisateur :
    - Coupe si trop long.
    - Retire les caractères de contrôle invisibles (sauf sauts de ligne).
    """
    if not text: 
        return ""
    # Retire les caractères de contrôle invisibles (sauf sauts de ligne)
    text = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]', '', text)
    return text[:max_length].strip()
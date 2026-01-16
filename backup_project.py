import os
import shutil
import datetime

def create_backup_folder():
    # --- CONFIGURATION ---
    # Nom du dossier qui sera créé sur le Bureau
    BACKUP_NAME = "BACKUP_SOCIAL_EXPERT_STABLE"
    
    # Liste des dossiers/fichiers à IGNORER (ne pas copier)
    # Ajoute ici tout ce qui est lourd et inutile pour un backup
    PATTERNS_TO_IGNORE = {
        '.git', 
        '__pycache__', 
        'venv', 
        'env', 
        '.idea', 
        '.vscode', 
        'node_modules', 
        'chroma_db', # Base de données vectorielle locale
        '.DS_Store'
    }

    # --- LOGIQUE ---
    project_root = os.getcwd()
    desktop_path = os.path.join(os.path.expanduser("~"), "Desktop")
    destination_path = os.path.join(desktop_path, BACKUP_NAME)

    print(f"🔄 Préparation du backup...")
    print(f"📍 Source : {project_root}")
    print(f"🎯 Destination : {destination_path}")

    # 1. NETTOYAGE : Si le dossier existe déjà sur le Bureau, on le supprime
    if os.path.exists(destination_path):
        print("🗑️  Suppression de l'ancienne version stable sur le bureau...")
        try:
            shutil.rmtree(destination_path)
        except Exception as e:
            print(f"❌ Impossible de supprimer l'ancien dossier : {e}")
            return

    # 2. COPIE : On clone le projet vers le Bureau en filtrant les indésirables
    try:
        shutil.copytree(
            project_root, 
            destination_path, 
            ignore=shutil.ignore_patterns(*PATTERNS_TO_IGNORE)
        )
        
        # 3. TIMESTAMP : On ajoute un petit fichier texte dedans pour la date
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d à %Hh%M")
        with open(os.path.join(destination_path, "DATE_VERSION.txt"), "w") as f:
            f.write(f"Cette version stable a été sauvegardée le : {timestamp}")

        print("-" * 30)
        print(f"✅ SUCCÈS ! Le DOSSIER '{BACKUP_NAME}' est sur ton Bureau.")
        print(f"📅 Version datée du : {timestamp}")

    except Exception as e:
        print(f"❌ Erreur lors de la copie du dossier : {e}")

if __name__ == "__main__":
    create_backup_folder()
import os
import zipfile
import shutil
import datetime

# --- CONFIGURATION ---
IGNORE_FOLDERS = {'venv', '__pycache__', '.git', '.idea', '.vscode', '.DS_Store', 'chroma_db', 'data_clean'}
EXTENSIONS_TEXTE = {'.py', '.txt', '.md', '.css', '.toml', '.yaml', '.json'}

def get_desktop_path():
    return os.path.join(os.path.expanduser("~"), "Desktop")

def create_backup():
    desktop = get_desktop_path()
    
    # 1. Nom du dossier sur le bureau
    backup_dir = os.path.join(desktop, "LATEST_BACKUP_SOCIAL_EXPERT")
    
    # NETTOYAGE : Si le dossier existe déjà, on le supprime pour repartir à neuf
    if os.path.exists(backup_dir):
        try:
            shutil.rmtree(backup_dir)
        except Exception as e:
            print(f"⚠️ Impossible de supprimer l'ancien dossier (il est peut-être ouvert) : {e}")
            return
    
    os.makedirs(backup_dir, exist_ok=True)
    
    # Noms des fichiers à l'intérieur
    zip_filename = os.path.join(backup_dir, "social_expert_source.zip")
    txt_filename = os.path.join(backup_dir, "CONTEXTE_IA_SOCIAL_EXPERT.txt")
    
    print(f"🚀 Création du backup Social Expert sur le Bureau...")

    project_root = os.getcwd()
    files_to_process = []

    # Parcours des fichiers
    for root, dirs, files in os.walk(project_root):
        # Filtrage des dossiers ignorés
        dirs[:] = [d for d in dirs if d not in IGNORE_FOLDERS]
        
        for file in files:
            # On ne se backup pas soi-même et on ignore les fichiers cachés
            if file == "backup_project.py" or file.startswith("."):
                continue
                
            file_path = os.path.join(root, file)
            rel_path = os.path.relpath(file_path, project_root)
            files_to_process.append((file_path, rel_path))

    # 2. Création du ZIP (Pour archivage/déploiement)
    with zipfile.ZipFile(zip_filename, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for file_path, rel_path in files_to_process:
            zipf.write(file_path, rel_path)
    print("📦 Archive ZIP créée.")

    # 3. Création du fichier TEXTE (Pour l'IA)
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d à %Hh%M")
    with open(txt_filename, 'w', encoding='utf-8') as outfile:
        outfile.write(f"# DERNIÈRE VERSION STABLE - SOCIAL EXPERT ({timestamp})\n")
        outfile.write("# Ce fichier contient tout le code source pour l'IA.\n\n")
        
        for file_path, rel_path in files_to_process:
            _, ext = os.path.splitext(file_path)
            if ext.lower() in EXTENSIONS_TEXTE:
                outfile.write("="*60 + "\n")
                outfile.write(f"FICHIER : {rel_path}\n")
                outfile.write("="*60 + "\n")
                try:
                    with open(file_path, 'r', encoding='utf-8', errors='ignore') as infile:
                        outfile.write(infile.read())
                    outfile.write("\n\n")
                except Exception as e:
                    outfile.write(f"[Erreur de lecture : {e}]\n\n")
    print("🧠 Fichier de contexte IA créé.")

    print(f"✅ TERMINÉ ! Le dossier 'LATEST_BACKUP_SOCIAL_EXPERT' est prêt sur ton Bureau.")

if __name__ == "__main__":
    create_backup()
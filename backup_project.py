import os
import zipfile
import datetime

# --- CONFIGURATION ---
# Dossiers à ignorer (pour ne pas alourdir le backup avec des fichiers inutiles)
IGNORE_FOLDERS = {
    'venv', '__pycache__', '.git', '.idea', '.vscode', 'data_clean', 'data', '.DS_Store'
}
# Extensions de fichiers à inclure dans le fichier texte (pour l'IA)
EXTENSIONS_TEXTE = {'.py', '.txt', '.md', '.css', '.toml', '.yaml', '.json'}

def get_desktop_path():
    return os.path.join(os.path.expanduser("~"), "Desktop")

def create_backup():
    # 1. Préparation du nom et du dossier
    now = datetime.datetime.now().strftime("%Y-%m-%d_%Hh%Mm%S")
    desktop = get_desktop_path()
    backup_name = f"BACKUP_SOCIAL_2026_{now}"
    backup_dir = os.path.join(desktop, backup_name)
    
    os.makedirs(backup_dir, exist_ok=True)
    
    zip_filename = os.path.join(backup_dir, f"source_complete_{now}.zip")
    txt_filename = os.path.join(backup_dir, f"CONTEXTE_IA_{now}.txt")
    
    print(f"🚀 Démarrage du backup vers le Bureau...")
    print(f"📂 Dossier : {backup_dir}")

    project_root = os.getcwd()
    files_to_process = []

    # 2. Scan des fichiers
    for root, dirs, files in os.walk(project_root):
        # Filtrer les dossiers ignorés
        dirs[:] = [d for d in dirs if d not in IGNORE_FOLDERS]
        
        for file in files:
            if file == "backup_project.py" or file.startswith("."):
                continue
                
            file_path = os.path.join(root, file)
            rel_path = os.path.relpath(file_path, project_root)
            files_to_process.append((file_path, rel_path))

    # 3. Création du ZIP (Sauvegarde technique)
    with zipfile.ZipFile(zip_filename, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for file_path, rel_path in files_to_process:
            zipf.write(file_path, rel_path)
    print(f"✅ Archive ZIP créée ({len(files_to_process)} fichiers).")

    # 4. Création du fichier TEXTE (Pour l'IA)
    with open(txt_filename, 'w', encoding='utf-8') as outfile:
        outfile.write(f"# BACKUP DU PROJET SOCIAL 2026 - {now}\n")
        outfile.write(f"# Ce fichier contient tout le code source pour analyse.\n\n")
        
        for file_path, rel_path in files_to_process:
            # On ne met dans le texte que le code, pas les images ou pdfs
            _, ext = os.path.splitext(file_path)
            if ext.lower() in EXTENSIONS_TEXTE:
                outfile.write("="*60 + "\n")
                outfile.write(f"FICHIER : {rel_path}\n")
                outfile.write("="*60 + "\n")
                try:
                    with open(file_path, 'r', encoding='utf-8') as infile:
                        outfile.write(infile.read())
                    outfile.write("\n\n")
                except Exception as e:
                    outfile.write(f"[Erreur de lecture : {e}]\n\n")

    print(f"✅ Fichier CONTEXTE IA généré.")
    print(f"🎉 Terminé ! Tout est sur ton Bureau.")

if __name__ == "__main__":
    create_backup()
import os
import shutil
import zipfile
from datetime import datetime

def backup_to_desktop():
    # 1. CONFIGURATION DES CHEMINS
    # Le dossier actuel (ton projet social2026)
    source_project_dir = os.getcwd()
    
    # Chemin vers ton BUREAU (Desktop)
    user_home = os.path.expanduser("~")
    desktop_path = os.path.join(user_home, "Desktop")
    
    # Le nom du dossier final sur le bureau
    output_folder_name = "LATEST_BACKUP_SOCIAL_EXPERT"
    final_output_path = os.path.join(desktop_path, output_folder_name)
    
    # Noms des fichiers
    timestamp = datetime.now().strftime("%Y-%m-%d_%Hh%Mm")
    txt_filename = f"CONTEXTE_IA_{timestamp}.txt"
    zip_filename = f"SOURCE_PROJET_{timestamp}.zip"

    print(f"📍 Source : {source_project_dir}")
    print(f"🎯 Destination : {final_output_path}")

    # 2. NETTOYAGE (On écrase l'ancien dossier sur le bureau)
    if os.path.exists(final_output_path):
        print(f"🧹 Suppression de l'ancien dossier sur le bureau...")
        shutil.rmtree(final_output_path)
    
    # Création du nouveau dossier
    os.makedirs(final_output_path)

    # 3. GÉNÉRATION DU FICHIER TEXTE (CONTEXTE)
    print(f"📝 Création du fichier texte...")
    full_txt_path = os.path.join(final_output_path, txt_filename)
    
    exclude_dirs = {'venv', '.git', '__pycache__', '.DS_Store', '.streamlit', 'data_clean', 'chroma_db', 'ui', output_folder_name}
    code_extensions = {'.py', '.yaml', '.txt', '.md', 'Dockerfile'}

    with open(full_txt_path, 'w', encoding='utf-8') as f_out:
        f_out.write(f"CONTEXTE PROJET SOCIAL 2026\nDATE : {timestamp}\n")
        f_out.write("="*50 + "\n\n")
        
        for root, dirs, files in os.walk(source_project_dir):
            dirs[:] = [d for d in dirs if d not in exclude_dirs]
            
            for file in files:
                if os.path.splitext(file)[1] in code_extensions or file == "Dockerfile":
                    # On ignore le dossier de backup s'il est dans le projet
                    if output_folder_name in root: continue
                    
                    file_path = os.path.join(root, file)
                    rel_path = os.path.relpath(file_path, source_project_dir)
                    
                    f_out.write(f"\n--- FICHIER : {rel_path} ---\n")
                    try:
                        with open(file_path, 'r', encoding='utf-8') as f_in:
                            f_out.write(f_in.read())
                    except:
                        f_out.write("[Erreur de lecture]")
                    f_out.write("\n")

    # 4. GÉNÉRATION DU ZIP
    print(f"📦 Compression du code...")
    full_zip_path = os.path.join(final_output_path, zip_filename)
    
    with zipfile.ZipFile(full_zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, dirs, files in os.walk(source_project_dir):
            dirs[:] = [d for d in dirs if d not in exclude_dirs]
            
            for file in files:
                # On ne zippe pas le dossier de backup lui-même
                if output_folder_name in root: continue
                if file.endswith('.pyc') or file == '.DS_Store': continue
                
                file_path = os.path.join(root, file)
                arcname = os.path.relpath(file_path, source_project_dir)
                zipf.write(file_path, arcname)

    print(f"✅ TERMINÉ ! Regarde ton bureau, le dossier '{output_folder_name}' est à jour.")

if __name__ == "__main__":
    backup_to_desktop()
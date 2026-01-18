import os
import shutil
import zipfile
from datetime import datetime

def backup_project_folder_mode():
    # 1. CONFIGURATION
    base_dir = os.getcwd()
    # Le nom EXACT du dossier que tu aimes
    output_folder_name = "LATEST_BACKUP_SOCIAL_EXPERT"
    output_path = os.path.join(base_dir, output_folder_name)
    
    # Noms des fichiers à l'intérieur
    txt_filename = "CONTEXTE_IA_SOCIAL_EXPERT.txt"
    zip_filename = "social_expert_source.zip"

    # 2. NETTOYAGE RADICAL (On supprime le dossier existant pour le recréer à neuf)
    if os.path.exists(output_path):
        print(f"🧹 Suppression de l'ancien dossier : {output_folder_name}...")
        shutil.rmtree(output_path)
    
    # On recrée le dossier vide
    os.makedirs(output_path)
    print(f"uD83DuDCC2 Création du dossier : {output_folder_name}")

    # 3. GÉNÉRATION DU FICHIER TEXTE (CONTEXTE)
    print(f"uD83DuDCDD Génération du fichier texte : {txt_filename}...")
    full_txt_path = os.path.join(output_path, txt_filename)
    
    exclude_dirs = {'venv', '.git', '__pycache__', '.DS_Store', '.streamlit', 'data_clean', 'chroma_db', 'ui', output_folder_name}
    code_extensions = {'.py', '.yaml', '.txt', '.md', 'Dockerfile'}
    
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")

    with open(full_txt_path, 'w', encoding='utf-8') as f_out:
        f_out.write(f"CONTEXTE PROJET SOCIAL 2026\nDATE : {timestamp}\n")
        f_out.write("="*50 + "\n\n")
        
        for root, dirs, files in os.walk(base_dir):
            dirs[:] = [d for d in dirs if d not in exclude_dirs]
            
            for file in files:
                if os.path.splitext(file)[1] in code_extensions or file == "Dockerfile":
                    # On ignore le dossier de backup lui-même s'il apparait
                    if output_folder_name in root: continue
                    
                    file_path = os.path.join(root, file)
                    rel_path = os.path.relpath(file_path, base_dir)
                    
                    f_out.write(f"\n--- FICHIER : {rel_path} ---\n")
                    try:
                        with open(file_path, 'r', encoding='utf-8') as f_in:
                            f_out.write(f_in.read())
                    except:
                        f_out.write("[Erreur de lecture]")
                    f_out.write("\n")

    # 4. GÉNÉRATION DU ZIP (SOURCE)
    print(f"uD83DuDCE6 Création du fichier ZIP : {zip_filename}...")
    full_zip_path = os.path.join(output_path, zip_filename)
    
    with zipfile.ZipFile(full_zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, dirs, files in os.walk(base_dir):
            dirs[:] = [d for d in dirs if d not in exclude_dirs]
            
            for file in files:
                # On évite de zipper le dossier de backup lui-même
                if output_folder_name in root: continue
                if file.endswith('.pyc') or file == '.DS_Store': continue
                
                file_path = os.path.join(root, file)
                arcname = os.path.relpath(file_path, base_dir)
                zipf.write(file_path, arcname)

    print(f"✅ TERMINÉ ! Le dossier '{output_folder_name}' est prêt.")

if __name__ == "__main__":
    backup_project_folder_mode()
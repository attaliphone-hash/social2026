import os
from pypdf import PdfReader

def pdf_to_txt():
    # Créez un dossier 'sources_pdf' et mettez vos PDF dedans
    source_folder = "./sources_pdf"
    
    if not os.path.exists(source_folder):
        os.makedirs(source_folder)
        print(f"📁 Dossier '{source_folder}' créé. Mettez vos PDF officiels (Code Travail, BOSS) dedans et relancez !")
        return

    # Liste des PDF
    files = [f for f in os.listdir(source_folder) if f.endswith('.pdf')]
    
    if not files:
        print("⚠️ Aucun PDF trouvé dans 'sources_pdf'.")
        return

    print(f"🚀 Début de la conversion de {len(files)} fichiers...")

    for filename in files:
        pdf_path = os.path.join(source_folder, filename)
        txt_filename = filename.replace('.pdf', '.txt')
        
        # On crée le fichier texte à la racine (là où build_db.py ira le chercher)
        print(f"   - Traitement de {filename}...")
        
        try:
            reader = PdfReader(pdf_path)
            full_text = ""
            for page in reader.pages:
                full_text += page.extract_text() + "\n\n"
            
            # Sauvegarde en .txt
            with open(txt_filename, "w", encoding="utf-8") as f_out:
                f_out.write(f"SOURCE OFFICIELLE : {filename}\n\n")
                f_out.write(full_text)
            
            print(f"   ✅ Converti en {txt_filename}")
            
        except Exception as e:
            print(f"   ❌ Erreur sur {filename} : {e}")

if __name__ == "__main__":
    pdf_to_txt()
import os
from pypdf import PdfReader

# --- CONFIGURATION ---
RAW_FILES = [
    {"source": "RAW_Code_Travail.pdf", "prefix": "LEGAL_Code_du_Travail"},
    {"source": "RAW_Code_SS.pdf", "prefix": "LEGAL_Code_Securite_Sociale"}
]

OUTPUT_DIR = "data_clean"
CHUNK_SIZE = 3000  # ~1 page dense

def process_pdfs():
    # On ne crée le dossier que s'il n'existe pas, on ne l'efface pas !
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)

    for item in RAW_FILES:
        source_pdf = item["source"]
        prefix_name = item["prefix"]

        if not os.path.exists(source_pdf):
            print(f"⚠️ Fichier source introuvable à la racine : {source_pdf}")
            continue

        print(f"📖 Lecture de {source_pdf}...")
        try:
            reader = PdfReader(source_pdf)
            full_text = ""
            
            # 1. Extraction globale
            for page in reader.pages:
                text = page.extract_text()
                if text:
                    full_text += text + "\n"
            
            print(f"   Texte extrait. Découpage en cours...")
            
            # 2. Découpage physique
            total_chunks = 0
            for i in range(0, len(full_text), CHUNK_SIZE):
                chunk_content = full_text[i:i + CHUNK_SIZE]
                
                # Nommage : LEGAL_Code_du_Travail_0001.txt
                chunk_filename = f"{prefix_name}_{total_chunks:04d}.txt"
                chunk_path = os.path.join(OUTPUT_DIR, chunk_filename)
                
                with open(chunk_path, "w", encoding="utf-8") as f:
                    f.write(chunk_content)
                
                total_chunks += 1

            print(f"✅ Terminé pour {source_pdf} : {total_chunks} fichiers .txt ajoutés dans {OUTPUT_DIR}")

        except Exception as e:
            print(f"❌ Erreur sur {source_pdf}: {e}")

if __name__ == "__main__":
    process_pdfs()
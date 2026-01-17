import os
from pinecone import Pinecone
from dotenv import load_dotenv

# --- CONFIGURATION ---
load_dotenv()

# Le nom exact de votre dossier de données
DATA_PATH = "data_clean" 
# Le nom de votre index Pinecone
INDEX_NAME = "expert-social"

def run_purge():
    # 1. Connexion à Pinecone
    try:
        pc = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))
        index = pc.Index(INDEX_NAME)
        print("✅ Connexion Pinecone réussie.")
    except Exception as e:
        print(f"❌ Erreur de connexion : {e}")
        return

    if not os.path.exists(DATA_PATH):
        print(f"❌ Dossier '{DATA_PATH}' introuvable. Impossible de lister les fichiers à supprimer.")
        return

    print("🚨 DÉMARRAGE DE LA PURGE CIBLÉE (Code du Travail)...")
    
    # 2. On liste les fichiers présents sur le disque
    files = os.listdir(DATA_PATH)
    count = 0
    
    for filename in files:
        # ⚠️ FILTRE DE SÉCURITÉ : On ne supprime que les TXT du Code du Travail
        # Adaptez "LEGAL_Code" si vos fichiers s'appellent différemment
        if filename.startswith("LEGAL_Code") and filename.endswith(".txt"):
            
            # On reconstruit l'ID tel qu'il a été enregistré lors de l'ingest
            # C'est généralement "data_clean/nom_du_fichier"
            source_id = os.path.join(DATA_PATH, filename)
            
            try:
                # 3. L'Ordre de suppression
                index.delete(filter={"source": source_id})
                print(f"   🗑️  Supprimé de la mémoire : {filename}")
                count += 1
            except Exception as e:
                print(f"   ❌ Erreur sur {filename}: {e}")

    if count == 0:
        print("\n⚠️ Aucun fichier correspondant trouvé sur le disque.")
        print("   Rappel : Ne supprimez pas les fichiers du dossier AVANT de lancer ce script.")
    else:
        print(f"\n✅ TERMINÉ. {count} fichiers ont été effacés de l'IA.")

if __name__ == "__main__":
    run_purge()
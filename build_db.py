import os
import chromadb
import google.generativeai as genai
import time
from tqdm import tqdm

# --- SÉCURITÉ : On demande la clé à chaque lancement ---
# Elle ne sera JAMAIS enregistrée dans ce fichier.
print("🔑 SÉCURITÉ :")
MY_API_KEY = input("Veuillez coller votre clé API Google (elle restera secrète) : ").strip()

if not MY_API_KEY:
    print("❌ Erreur : Aucune clé fournie.")
    exit()

genai.configure(api_key=MY_API_KEY)

def build_database():
    print("\n🚀 Démarrage de la construction de la Base de Données...")
    
    # Création du dossier local
    client = chromadb.PersistentClient(path="./chroma_db")
    
    # Nettoyage
    try:
        client.delete_collection("expert_rh_pro_v5")
    except:
        pass
        
    collection = client.create_collection("expert_rh_pro_v5")
    
    # Lecture
    fichiers_txt = [f for f in os.listdir('.') if f.endswith('.txt') and 'requirements' not in f]
    print(f"📂 {len(fichiers_txt)} fichiers trouvés.")

    docs_textes = []
    docs_ids = []
    docs_metadatas = []
    compteur = 0
    
    # Découpage
    for fichier in fichiers_txt:
        print(f"   - Traitement de : {fichier}")
        with open(fichier, "r", encoding="utf-8") as f:
            contenu = f.read()
        
        taille_bloc = 1500
        chevauchement = 200
        for i in range(0, len(contenu), taille_bloc - chevauchement):
            morceau = contenu[i : i + taille_bloc]
            if len(morceau.strip()) > 10:
                docs_textes.append(f"Source [{fichier}] :\n{morceau}")
                docs_ids.append(f"doc_{compteur}")
                docs_metadatas.append({"source": fichier})
                compteur += 1

    print(f"📊 Total : {len(docs_textes)} morceaux à vectoriser.")
    
    # Vectorisation par lots
    batch_size = 20 
    for i in tqdm(range(0, len(docs_textes), batch_size)):
        batch_docs = docs_textes[i : i + batch_size]
        batch_ids = docs_ids[i : i + batch_size]
        batch_meta = docs_metadatas[i : i + batch_size]
        
        try:
            embeddings = []
            for doc in batch_docs:
                res = genai.embed_content(
                    model="models/text-embedding-004",
                    content=doc,
                    task_type="retrieval_document"
                )
                embeddings.append(res['embedding'])
                time.sleep(0.1)
            
            collection.add(
                documents=batch_docs,
                ids=batch_ids,
                embeddings=embeddings,
                metadatas=batch_meta
            )
        except Exception as e:
            print(f"❌ Erreur sur le lot {i} : {e}")
            time.sleep(5) 

    print("✅ Base de données construite avec succès dans le dossier 'chroma_db' !")

if __name__ == "__main__":
    build_database()
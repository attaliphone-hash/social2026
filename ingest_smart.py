import os
import time
from datetime import datetime, timedelta
from dotenv import load_dotenv
from langchain_community.document_loaders import PyPDFLoader, TextLoader, CSVLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_pinecone import PineconeVectorStore
from pinecone import Pinecone

# --- CONFIGURATION ---
load_dotenv()

DATA_PATH = "data_clean"
INDEX_NAME = "expert-social"
# 🕒 RÉGLAGE AUTOMATIQUE : On ne traite que les fichiers modifiés depuis X heures
HOURS_THRESHOLD = 24 

def run_smart_ingestion():
    # 1. Connexion Pinecone
    try:
        pc = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))
        index = pc.Index(INDEX_NAME)
    except Exception as e:
        print(f"❌ Erreur connexion Pinecone : {e}")
        return

    embeddings = GoogleGenerativeAIEmbeddings(model="models/text-embedding-004")
    vectorstore = PineconeVectorStore(index_name=INDEX_NAME, embedding=embeddings)

    if not os.path.exists(DATA_PATH):
        print(f"❌ Dossier '{DATA_PATH}' introuvable.")
        return

    print(f"--- 🧠 Mode SMART AUTO : Analyse des modifications (< {HOURS_THRESHOLD}h) ---")
    
    # Seuil de temps (Maintenant moins 24h)
    threshold_time = time.time() - (HOURS_THRESHOLD * 3600)
    
    files = [f for f in os.listdir(DATA_PATH) if f.endswith(('.pdf', '.txt', '.csv'))]
    processed_count = 0

    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=150)

    for filename in files:
        file_path = os.path.join(DATA_PATH, filename)
        
        # 🔍 VÉRIFICATION AUTOMATIQUE DE LA DATE
        # Si le fichier est plus vieux que le seuil, on passe
        mod_time = os.path.getmtime(file_path)
        if mod_time < threshold_time:
            # Optionnel : décommenter pour voir ce qui est ignoré
            # print(f"💤 Ignoré (pas de changement récent) : {filename}")
            continue

        # Si on arrive ici, c'est que le fichier a changé récemment !
        print(f"⚡ DÉTECTÉ (Modifié récemment) : {filename}")
        processed_count += 1
        
        documents = []
        try:
            if filename.endswith(".pdf"):
                documents = PyPDFLoader(file_path).load()
            elif filename.endswith(".txt"):
                documents = TextLoader(file_path, encoding="utf-8").load()
            elif filename.endswith(".csv"):
                documents = CSVLoader(file_path, csv_args={"delimiter": ";"}, encoding="latin-1").load()

            if not documents:
                continue

            source_id = documents[0].metadata.get("source")
            if not source_id:
                # Fallback si metadata vide
                source_id = file_path

            # NETTOYAGE CIBLÉ AVANT AJOUT
            print(f"   🧹 Nettoyage des anciennes versions dans Pinecone...")
            index.delete(filter={"source": source_id})
            
            # DÉCOUPAGE ET ENVOI
            chunks = text_splitter.split_documents(documents)
            print(f"   🚀 Envoi de {len(chunks)} fragments...")
            
            batch_size = 100
            for i in range(0, len(chunks), batch_size):
                vectorstore.add_documents(chunks[i:i + batch_size])
            
            print(f"   ✅ Terminé pour {filename}.")

        except Exception as e:
            print(f"❌ Erreur sur {filename}: {e}")

    if processed_count == 0:
        print("\n💤 Aucun fichier modifié récemment n'a été trouvé.")
        print("   Astuce : Ouvrez et enregistrez un fichier pour qu'il soit détecté.")
    else:
        print(f"\n🎉 Succès : {processed_count} fichier(s) mis à jour.")

if __name__ == "__main__":
    run_smart_ingestion()
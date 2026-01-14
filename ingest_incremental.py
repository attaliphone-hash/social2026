import os
import time
from dotenv import load_dotenv
from langchain_community.document_loaders import PyPDFLoader, TextLoader, CSVLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_pinecone import PineconeVectorStore
from pinecone import Pinecone

# --- 1. CONFIGURATION ---
load_dotenv()

DATA_PATH = "data_clean"
INDEX_NAME = "expert-social"

def run_incremental_ingestion():
    # Connexion à Pinecone (pour les suppressions ciblées)
    try:
        pc = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))
        index = pc.Index(INDEX_NAME)
    except Exception as e:
        print(f"❌ Erreur de connexion Pinecone : {e}")
        return

    # Préparation des embeddings
    embeddings = GoogleGenerativeAIEmbeddings(model="models/text-embedding-004")
    vectorstore = PineconeVectorStore(index_name=INDEX_NAME, embedding=embeddings)

    if not os.path.exists(DATA_PATH):
        print(f"❌ Dossier '{DATA_PATH}' introuvable.")
        return

    print(f"--- 🔄 Mode Incrémental : Mise à jour dossier {DATA_PATH} ---")
    
    files = [f for f in os.listdir(DATA_PATH) if f.endswith(('.pdf', '.txt', '.csv'))]
    print(f"📂 {len(files)} fichiers détectés.")

    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=150)

    for filename in files:
        file_path = os.path.join(DATA_PATH, filename)
        documents = []
        
        try:
            # A. CHARGEMENT
            if filename.endswith(".pdf"):
                loader = PyPDFLoader(file_path)
                documents = loader.load()
            elif filename.endswith(".txt"):
                loader = TextLoader(file_path, encoding="utf-8")
                documents = loader.load()
            elif filename.endswith(".csv"):
                loader = CSVLoader(file_path, csv_args={"delimiter": ";"}, encoding="latin-1")
                documents = loader.load()

            if not documents:
                print(f"⚠️  Vide ou illisible : {filename}")
                continue

            # Récupération de la source exacte (pour le filtre de suppression)
            # Langchain met le chemin relatif ou absolu dans metadata['source']
            source_id = documents[0].metadata.get("source")
            
            if not source_id:
                print(f"⚠️  Pas de source détectée pour {filename}, on passe.")
                continue

            # B. NETTOYAGE CIBLÉ (La magie est ici)
            # On supprime dans Pinecone tout ce qui correspond à CE fichier
            print(f"🔄 Traitement de : {filename}")
            
            # On supprime les anciens chunks de ce fichier spécifique
            index.delete(filter={"source": source_id})
            
            # C. DÉCOUPAGE ET ENVOI
            chunks = text_splitter.split_documents(documents)
            
            # Envoi par petits paquets pour éviter les erreurs de timeout
            batch_size = 100
            for i in range(0, len(chunks), batch_size):
                batch = chunks[i:i + batch_size]
                vectorstore.add_documents(batch)
            
            print(f"   ✅ Mis à jour ({len(chunks)} fragments).")

        except Exception as e:
            print(f"❌ Erreur sur {filename}: {e}")

    print("--- Terminé ! 🎉 ---")

if __name__ == "__main__":
    run_incremental_ingestion()
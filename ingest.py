import os
from dotenv import load_dotenv  # Pour lire votre fichier .env
from langchain_community.document_loaders import PyPDFLoader, TextLoader, CSVLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_pinecone import PineconeVectorStore

# --- CHARGEMENT DES CLÉS ---
load_dotenv() 

# --- CONFIGURATION ---
DATA_PATH = "DATA_CLEAN"  # Votre dossier actuel
INDEX_NAME = "expert-social" 

def run_ingestion():
    # 1. Vérification du dossier
    if not os.path.exists(DATA_PATH):
        print(f"❌ Erreur : Le dossier '{DATA_PATH}' est introuvable.")
        return
    
    documents = []
    print(f"--- 📂 Chargement depuis {DATA_PATH} ---")
    
    for filename in os.listdir(DATA_PATH):
        file_path = os.path.join(DATA_PATH, filename)
        try:
            if filename.endswith(".pdf"):
                print(f"📄 Lecture PDF : {filename}")
                loader = PyPDFLoader(file_path)
                documents.extend(loader.load())
            elif filename.endswith(".txt"):
                print(f"📝 Lecture TXT : {filename}")
                loader = TextLoader(file_path, encoding="utf-8") 
                documents.extend(loader.load())
            elif filename.endswith(".csv"):
                print(f"📊 Lecture CSV : {filename}")
                loader = CSVLoader(file_path, csv_args={'delimiter': ';'}, encoding="latin-1")
                documents.extend(loader.load())
        except Exception as e:
            print(f"❌ Erreur sur {filename}: {e}")

    if not documents:
        print("⚠️ Aucun document trouvé.")
        return

    # 2. Découpage (Chunks)
    print(f"--- ✂️ Découpage de {len(documents)} éléments ---")
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=150)
    chunks = text_splitter.split_documents(documents)

    # 3. Envoi vers Pinecone Cloud
    print("--- 🚀 Envoi vers PINECONE (Cloud) ---")
    embeddings = GoogleGenerativeAIEmbeddings(model="models/text-embedding-004")
    
    try:
        PineconeVectorStore.from_documents(
            chunks, 
            embeddings, 
            index_name=INDEX_NAME
        )
        print(f"☀️ SUCCÈS : L'index '{INDEX_NAME}' est à jour !")
    except Exception as e:
        print(f"❌ Erreur : {e}")

if __name__ == "__main__":
    run_ingestion()
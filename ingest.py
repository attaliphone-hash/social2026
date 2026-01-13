import os
import time
from dotenv import load_dotenv
from langchain_community.document_loaders import PyPDFLoader, TextLoader, CSVLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_pinecone import PineconeVectorStore
from pinecone import Pinecone

# --- CHARGEMENT DES CLÉS ---
load_dotenv() 

# --- CONFIGURATION ---
DATA_PATH = "DATA_CLEAN"
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
    
    # --- NETTOYAGE OBLIGATOIRE ---
    print(f"🧹 VIDAGE de l'index '{INDEX_NAME}'...")
    try:
        pc = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))
        index = pc.Index(INDEX_NAME)
        index.delete(delete_all=True)
        print("✅ Index vidé avec succès.")
    except Exception as e:
        print(f"⚠️ Attention : Impossible de vider l'index (Erreur: {e})")

    embeddings = GoogleGenerativeAIEmbeddings(model="models/text-embedding-004")
    
    # --- ENVOI PAR PAQUETS (BATCHING) POUR ÉVITER LES ERREURS 502 ---
    batch_size = 100
    print(f"📦 Envoi de {len(chunks)} fragments par paquets de {batch_size}...")
    
    try:
        # Initialisation avec le premier paquet
        first_batch = chunks[:batch_size]
        vectorstore = PineconeVectorStore.from_documents(
            first_batch, 
            embeddings, 
            index_name=INDEX_NAME
        )
        print(f"➡️ {min(batch_size, len(chunks))}/{len(chunks)} envoyés...")

        # Envoi du reste
        if len(chunks) > batch_size:
            for i in range(batch_size, len(chunks), batch_size):
                batch = chunks[i : i + batch_size]
                vectorstore.add_documents(batch)
                print(f"➡️ {min(i + batch_size, len(chunks))}/{len(chunks)} envoyés...")
                # Petite pause pour laisser respirer l'API si nécessaire
                time.sleep(1) 

        print(f"☀️ SUCCÈS : L'index '{INDEX_NAME}' est à jour !")
    except Exception as e:
        print(f"❌ Erreur lors de l'envoi : {e}")

if __name__ == "__main__":
    run_ingestion()
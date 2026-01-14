import os
import time
from dotenv import load_dotenv
from langchain_community.document_loaders import PyPDFLoader, TextLoader, CSVLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_pinecone import PineconeVectorStore
from pinecone import Pinecone

# --- 1. CHARGEMENT CONFIGURATION ---
load_dotenv()

# Homogénéité : dossier en minuscules (comme dans le projet / gcloudignore)
DATA_PATH = os.getenv("DATA_PATH", "data_clean")
INDEX_NAME = os.getenv("PINECONE_INDEX_NAME", "expert-social")

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")

def run_ingestion():
    # Vérifications de base
    if not GOOGLE_API_KEY:
        print("❌ Erreur : GOOGLE_API_KEY manquant dans l'environnement.")
        return
    if not PINECONE_API_KEY:
        print("❌ Erreur : PINECONE_API_KEY manquant dans l'environnement.")
        return

    if not os.path.exists(DATA_PATH):
        print(f"❌ Erreur : Le dossier '{DATA_PATH}' est introuvable.")
        return

    documents = []
    print(f"--- 📂 Chargement des fichiers depuis {DATA_PATH} ---")

    for filename in os.listdir(DATA_PATH):
        file_path = os.path.join(DATA_PATH, filename)
        try:
            if filename.lower().endswith(".pdf"):
                loader = PyPDFLoader(file_path)
                documents.extend(loader.load())
            elif filename.lower().endswith(".txt"):
                loader = TextLoader(file_path, encoding="utf-8")
                documents.extend(loader.load())
            elif filename.lower().endswith(".csv"):
                loader = CSVLoader(file_path, csv_args={'delimiter': ';'}, encoding="latin-1")
                documents.extend(loader.load())
            else:
                continue

            print(f"✅ Chargé : {filename}")
        except Exception as e:
            print(f"❌ Erreur sur {filename}: {e}")

    if not documents:
        print("⚠️ Aucun document trouvé dans le dossier.")
        return

    # --- 2. DÉCOUPAGE EN FRAGMENTS (CHUNKS) ---
    print(f"--- ✂️ Découpage de {len(documents)} documents ---")
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=150)
    chunks = text_splitter.split_documents(documents)
    print(f"Total : {len(chunks)} fragments créés.")

    # --- 3. NETTOYAGE CRITIQUE DE L'INDEX ---
    print(f"--- 🧹 Nettoyage de l'index '{INDEX_NAME}' ---")
    try:
        pc = Pinecone(api_key=PINECONE_API_KEY)
        index = pc.Index(INDEX_NAME)

        index.delete(delete_all=True)

        print("⏳ Attente de la confirmation de suppression par Pinecone...")
        while True:
            stats = index.describe_index_stats()
            count = stats.get('total_vector_count', 0)
            if count == 0:
                break
            print(f"   ... encore {count} vecteurs en cache, on patiente...")
            time.sleep(5)

        print("✨ Index totalement vide. Prêt pour l'ingestion.")
    except Exception as e:
        print(f"⚠️ Erreur lors du nettoyage : {e}")
        return

    # --- 4. ENVOI PAR PAQUETS (BATCHING) ---
    print("--- 🚀 Envoi vers PINECONE (Cloud) ---")
    embeddings = GoogleGenerativeAIEmbeddings(
        model="models/text-embedding-004",
        google_api_key=GOOGLE_API_KEY
    )

    batch_size = 100
    try:
        first_batch = chunks[:batch_size]
        vectorstore = PineconeVectorStore.from_documents(
            first_batch,
            embeddings,
            index_name=INDEX_NAME
        )
        print(f"➡️ {min(batch_size, len(chunks))}/{len(chunks)} fragments envoyés...")

        if len(chunks) > batch_size:
            for i in range(batch_size, len(chunks), batch_size):
                batch = chunks[i:i + batch_size]
                vectorstore.add_documents(batch)
                print(f"➡️ {min(i + batch_size, len(chunks))}/{len(chunks)} fragments envoyés...")
                time.sleep(1)

        print(f"☀️ SUCCÈS : L'index '{INDEX_NAME}' est propre et à jour !")
    except Exception as e:
        print(f"❌ Erreur lors de l'envoi : {e}")

if __name__ == "__main__":
    run_ingestion()

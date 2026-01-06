import os
import sys
from langchain_community.document_loaders import TextLoader, PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_chroma import Chroma

def build():
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        print("❌ ERREUR : Variable GOOGLE_API_KEY manquante.")
        return

    # --- CONFIGURATION DES CHEMINS ---
    # On cible explicitement le dossier 'data'
    current_dir = os.path.dirname(os.path.abspath(__file__))
    data_dir = os.path.join(current_dir, "data")
    persist_db = os.path.join(current_dir, "chroma_db")

    print(f"🚀 Démarrage de la construction...")
    print(f"📂 Scan du dossier : {data_dir}")

    if not os.path.exists(data_dir):
        print(f"❌ ERREUR : Le dossier {data_dir} n'existe pas.")
        return

    # --- CHARGEMENT DES DOCUMENTS ---
    documents = []
    for filename in os.listdir(data_dir):
        file_path = os.path.join(data_dir, filename)
        try:
            if filename.endswith(".txt"):
                loader = TextLoader(file_path, encoding="utf-8")
                documents.extend(loader.load())
                print(f"✅ Chargé : {filename}")
            elif filename.endswith(".pdf"):
                loader = PyPDFLoader(file_path)
                documents.extend(loader.load())
                print(f"✅ Chargé : {filename}")
        except Exception as e:
            print(f"⚠️ Erreur sur {filename} : {e}")

    if not documents:
        print("❌ Aucun document trouvé dans le dossier /data/.")
        return

    # --- DECOUPAGE ---
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=100)
    docs = text_splitter.split_documents(documents)
    print(f"✂️  Nombre de segments créés : {len(docs)}")

    # --- VECTORISATION ---
    print("🧠 Création des vecteurs (Embeddings)...")
    embeddings = GoogleGenerativeAIEmbeddings(
        model="models/text-embedding-004",
        google_api_key=api_key
    )

    # On recrée la base proprement
    if os.path.exists(persist_db):
        import shutil
        shutil.rmtree(persist_db)

    vectorstore = Chroma.from_documents(
        documents=docs,
        embedding=embeddings,
        persist_directory=persist_db
    )

    print(f"✨ Terminé ! La base chroma_db est prête dans {persist_db}")

if __name__ == "__main__":
    build()
import os
import sys
import shutil
from langchain_community.document_loaders import TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_chroma import Chroma

# --- CONFIGURATION ---
MY_API_KEY = os.environ.get("GOOGLE_API_KEY")
os.environ["GOOGLE_API_KEY"] = MY_API_KEY
SOURCE_DIRECTORY = "."  # Vos fichiers .txt sont à la racine
PERSIST_DIRECTORY = "chroma_db"

def main():
    print("🚀 Vectorisation basée sur les fichiers TXT...")
    if os.path.exists(PERSIST_DIRECTORY):
        shutil.rmtree(PERSIST_DIRECTORY)

    # On cible les fichiers .txt présents à la racine
    files = [f for f in os.listdir(SOURCE_DIRECTORY) if f.lower().endswith('.txt')]
    print(f"📂 {len(files)} fichiers texte détectés.")

    all_documents = []
    for i, filename in enumerate(files, 1):
        print(f"[{i}/{len(files)}] 📝 Lecture : {filename}...", end=" ", flush=True)
        try:
            loader = TextLoader(os.path.join(SOURCE_DIRECTORY, filename), encoding='utf-8')
            all_documents.extend(loader.load())
            print("✅")
        except Exception as e:
            print(f"❌ Erreur : {e}")

    # Découpage et Vectorisation par paquets
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
    chunks = text_splitter.split_documents(all_documents)
    embeddings = GoogleGenerativeAIEmbeddings(model="models/text-embedding-004")

    vectorstore = None
    batch_size = 100
    for i in range(0, len(chunks), batch_size):
        batch = chunks[i : i + batch_size]
        print(f"   📤 Envoi paquet {i//batch_size + 1}... ", end="", flush=True)
        if vectorstore is None:
            vectorstore = Chroma.from_documents(batch, embeddings, persist_directory=PERSIST_DIRECTORY)
        else:
            vectorstore.add_documents(batch)
        print("✅")
    print("\n✅ Base de données mise à jour avec succès !")

if __name__ == "__main__":
    main()
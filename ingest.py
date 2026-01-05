import os
import shutil
from langchain_community.document_loaders import PyPDFLoader, TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_chroma import Chroma

# Configuration
DATA_PATH = "data"
DB_PATH = "chroma_db"

def create_vector_db():
    # 1. Nettoyage de l'ancienne base pour repartir propre
    if os.path.exists(DB_PATH):
        shutil.rmtree(DB_PATH)
        print(f"🗑️ Ancienne base '{DB_PATH}' supprimée.")

    documents = []
    
    # 2. Vérification du dossier data
    if not os.path.exists(DATA_PATH):
        os.makedirs(DATA_PATH)
        print(f"⚠️ Dossier '{DATA_PATH}' créé. Mettez-y vos fichiers.")
        return

    # 3. Chargement des fichiers
    print("--- Chargement des documents ---")
    files_found = False
    for filename in os.listdir(DATA_PATH):
        file_path = os.path.join(DATA_PATH, filename)
        
        try:
            if filename.endswith(".pdf"):
                print(f"📄 Lecture PDF : {filename}")
                loader = PyPDFLoader(file_path)
                documents.extend(loader.load())
                files_found = True
            elif filename.endswith(".txt"):
                print(f"📝 Lecture TXT : {filename}")
                # encodage utf-8 vital pour les accents français
                loader = TextLoader(file_path, encoding="utf-8") 
                documents.extend(loader.load())
                files_found = True
        except Exception as e:
            print(f"❌ Erreur sur {filename}: {e}")

    if not files_found:
        print("⚠️ Aucun fichier valide (.txt ou .pdf) trouvé dans le dossier 'data'.")
        return

    # 4. Découpage (Chunking)
    print(f"--- Découpage de {len(documents)} pages brutes ---")
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=100)
    chunks = text_splitter.split_documents(documents)
    print(f"✂️ Résultat : {len(chunks)} morceaux de texte prêts.")

    # 5. Création de la base Vectorielle
    print("--- Génération de la base (Embedding Google) ---")
    print("⏳ Cela peut prendre quelques minutes selon la taille des Codes...")
    
    embeddings = GoogleGenerativeAIEmbeddings(model="models/text-embedding-004")
    
    vectorstore = Chroma.from_documents(
        documents=chunks, 
        embedding=embeddings, 
        persist_directory=DB_PATH
    )
    print("✅ SUCCÈS : Base de connaissances 'chroma_db' générée !")

if __name__ == "__main__":
    create_vector_db()
import os
import shutil
from langchain_chroma import Chroma
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_community.document_loaders import TextLoader, PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter

# Configuration
CHROMA_PATH = "chroma_db"
DATA_PATH = "."  # Le dossier courant

def load_documents():
    documents = []
    print(f"📂 Scan du dossier : {os.getcwd()}")
    
    files = os.listdir(DATA_PATH)
    print(f"🧐 J'ai trouvé {len(files)} fichiers au total dans le dossier.")

    for filename in files:
        file_path = os.path.join(DATA_PATH, filename)
        filename_lower = filename.lower() # On ignore les majuscules/minuscules
        
        # Traitement des fichiers TEXTE
        if filename_lower.endswith(".txt") and filename != "requirements.txt":
            try:
                loader = TextLoader(file_path, encoding="utf-8")
                documents.extend(loader.load())
                print(f"   ✅ Chargé (TXT) : {filename}")
            except Exception as e:
                print(f"   ❌ Erreur sur {filename} : {e}")
        
        # Traitement des fichiers PDF
        elif filename_lower.endswith(".pdf"):
            try:
                loader = PyPDFLoader(file_path)
                documents.extend(loader.load())
                print(f"   ✅ Chargé (PDF) : {filename}")
            except Exception as e:
                print(f"   ❌ Erreur sur {filename} : {e}")
        
        else:
            # On affiche ce qu'on ignore pour comprendre
            pass 
                
    return documents

def split_text(documents):
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1500,
        chunk_overlap=300,
        add_start_index=True,
    )
    return text_splitter.split_documents(documents)

def save_to_chroma(chunks):
    if os.path.exists(CHROMA_PATH):
        shutil.rmtree(CHROMA_PATH)

    if not chunks:
        print("⚠️ ALERTE : Aucun document valide n'a été trouvé ! La base est vide.")
        return

    embeddings = GoogleGenerativeAIEmbeddings(model="models/text-embedding-004")
    
    print(f"💾 Création de la base avec {len(chunks)} morceaux de texte...")
    db = Chroma.from_documents(
        chunks, 
        embeddings, 
        persist_directory=CHROMA_PATH
    )
    print(f"🎉 Base de données générée avec succès dans {CHROMA_PATH}")

if __name__ == "__main__":
    if not os.getenv("GOOGLE_API_KEY"):
        print("❌ ERREUR : Variable GOOGLE_API_KEY manquante.")
    else:
        print("🚀 Démarrage de la construction...")
        docs = load_documents()
        if docs:
            chunks = split_text(docs)
            save_to_chroma(chunks)
        else:
            print("❌ Aucun document chargé. Vérifiez vos fichiers.")
import os
import shutil
from langchain_community.document_loaders import DirectoryLoader, TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_chroma import Chroma
from dotenv import load_dotenv

# Charge les variables d'environnement (si tu as un .env local)
load_dotenv()

# Configuration
DATA_PATH = "./"  # Dossier où sont tes fichiers .txt
DB_PATH = "chroma_db"
API_KEY = os.getenv("GOOGLE_API_KEY")

if not API_KEY:
    # Fallback pour Streamlit secrets si lancé localement sans .env mais avec secrets
    try:
        import streamlit as st
        API_KEY = st.secrets["GOOGLE_API_KEY"]
    except:
        print("❌ ERREUR : Pas de clé API trouvée. Définissez GOOGLE_API_KEY.")
        exit()

def generate_data_store():
    print("🚀 Démarrage de la construction de la base...")
    
    # 1. Chargement des documents
    print(f"📂 Chargement des fichiers depuis {DATA_PATH}...")
    # On charge tous les .txt du dossier
    loader = DirectoryLoader(DATA_PATH, glob="*.txt", loader_cls=TextLoader)
    documents = loader.load()
    print(f"✅ {len(documents)} fichiers chargés.")

    # 2. Découpage (CHUNKING) - C'est ici que la magie opère
    print("✂️ Découpage des textes en morceaux (Chunks)...")
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1500,      # Taille de chaque morceau (env. 3-4 paragraphes)
        chunk_overlap=300,    # Chevauchement pour ne pas couper une phrase au milieu
        add_start_index=True,
    )
    chunks = text_splitter.split_documents(documents)
    print(f"✅ Documents découpés en {len(chunks)} morceaux distincts.")

    # 3. Création de la base Vectorielle
    save_to_chroma(chunks)

def save_to_chroma(chunks):
    # Suppression de l'ancienne base pour repartir à propre
    if os.path.exists(DB_PATH):
        shutil.rmtree(DB_PATH)

    print("💾 Création de la base ChromaDB (Cela peut prendre un moment)...")
    
    embeddings = GoogleGenerativeAIEmbeddings(model="models/text-embedding-004", google_api_key=API_KEY)
    
    # Création et sauvegarde
    db = Chroma.from_documents(
        chunks, 
        embeddings, 
        persist_directory=DB_PATH
    )
    print(f"🎉 Base de données générée avec succès dans le dossier {DB_PATH} !")

if __name__ == "__main__":
    generate_data_store()
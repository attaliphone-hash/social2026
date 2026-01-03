import os
import sys
import shutil

# Importations nécessaires pour LangChain et Chroma
try:
    from langchain_community.document_loaders import PyPDFLoader, DirectoryLoader
    from langchain_text_splitters import RecursiveCharacterTextSplitter
    from langchain_google_genai import GoogleGenerativeAIEmbeddings
    from langchain_chroma import Chroma
except ImportError as e:
    print("❌ Erreur d'importation. Avez-vous bien installé les dépendances ?")
    print(f"   Détail : {e}")
    sys.exit(1)

# --- CONFIGURATION CLÉ API ---
# C'EST ICI LA CORRECTION : On ne fait plus input(), on lit la variable d'environnement
MY_API_KEY = os.environ.get("GOOGLE_API_KEY")

if not MY_API_KEY:
    print("❌ ERREUR CRITIQUE : Clé API introuvable.")
    print("   La variable d'environnement 'GOOGLE_API_KEY' est vide.")
    sys.exit(1)

# On configure la clé pour les outils Google
os.environ["GOOGLE_API_KEY"] = MY_API_KEY

# --- PARAMÈTRES ---
SOURCE_DIRECTORY = "sources_pdf"
PERSIST_DIRECTORY = "chroma_db"

def main():
    print("🚀 Démarrage du script de vectorisation (Mode Cloud)...")

    # 1. Vérification du dossier source
    if not os.path.exists(SOURCE_DIRECTORY):
        print(f"❌ Le dossier '{SOURCE_DIRECTORY}' n'existe pas.")
        sys.exit(1)

    # 2. Nettoyage de l'ancienne base
    if os.path.exists(PERSIST_DIRECTORY):
        print(f"🧹 Suppression de l'ancienne base : {PERSIST_DIRECTORY}")
        shutil.rmtree(PERSIST_DIRECTORY)

    # 3. Chargement des documents
    print(f"📂 Lecture des fichiers PDF dans '{SOURCE_DIRECTORY}'...")
    loader = DirectoryLoader(SOURCE_DIRECTORY, glob="./*.pdf", loader_cls=PyPDFLoader)
    documents = loader.load()
    
    if not documents:
        print("⚠️ Aucun document trouvé !")
        sys.exit(1)
        
    print(f"   ✅ {len(documents)} pages chargées.")

    # 4. Découpage
    print("✂️ Découpage du texte...")
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=200,
        add_start_index=True
    )
    chunks = text_splitter.split_documents(documents)
    print(f"   🧩 {len(chunks)} fragments créés.")

    # 5. Vectorisation
    print("🧠 Génération des embeddings et sauvegarde...")
    embeddings = GoogleGenerativeAIEmbeddings(model="models/text-embedding-004")

    vectorstore = Chroma.from_documents(
        documents=chunks,
        embedding=embeddings,
        persist_directory=PERSIST_DIRECTORY
    )

    print("-" * 50)
    print(f"✅ SUCCÈS : Base de données créée dans '{PERSIST_DIRECTORY}'")
    print("-" * 50)

if __name__ == "__main__":
    main()
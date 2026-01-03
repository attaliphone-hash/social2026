import os
import sys
import shutil

# Importations nécessaires
try:
    from langchain_community.document_loaders import PyPDFLoader
    from langchain_text_splitters import RecursiveCharacterTextSplitter
    from langchain_google_genai import GoogleGenerativeAIEmbeddings
    from langchain_chroma import Chroma
except ImportError as e:
    print(f"❌ Erreur d'importation : {e}")
    sys.exit(1)

# --- CONFIGURATION CLÉ API ---
# On récupère la clé injectée par Google Cloud Build via l'environnement
MY_API_KEY = os.environ.get("GOOGLE_API_KEY")
if not MY_API_KEY:
    print("❌ ERREUR CRITIQUE : Variable GOOGLE_API_KEY introuvable.")
    sys.exit(1)

os.environ["GOOGLE_API_KEY"] = MY_API_KEY

SOURCE_DIRECTORY = "sources_pdf"
PERSIST_DIRECTORY = "chroma_db"

def main():
    print("🚀 Démarrage de la vectorisation optimisée (Mode Batch)...")

    # 1. Vérifications de base
    if not os.path.exists(SOURCE_DIRECTORY):
        print(f"❌ Le dossier '{SOURCE_DIRECTORY}' n'existe pas.")
        sys.exit(1)

    if os.path.exists(PERSIST_DIRECTORY):
        print(f"🧹 Nettoyage de l'ancienne base...")
        shutil.rmtree(PERSIST_DIRECTORY)

    # 2. Chargement détaillé des PDF
    files = [f for f in os.listdir(SOURCE_DIRECTORY) if f.lower().endswith('.pdf')]
    print(f"📂 {len(files)} fichiers trouvés dans '{SOURCE_DIRECTORY}'")

    all_documents = []
    for i, filename in enumerate(files, 1):
        file_path = os.path.join(SOURCE_DIRECTORY, filename)
        print(f"[{i}/{len(files)}] 📖 Lecture de : {filename}...", end=" ", flush=True)
        try:
            loader = PyPDFLoader(file_path)
            docs = loader.load()
            all_documents.extend(docs)
            print(f"✅ ({len(docs)} pages)")
        except Exception as e:
            print(f"❌ Erreur sur ce fichier : {e}")

    if not all_documents:
        print("⚠️ Aucun contenu extrait. Fin du script.")
        sys.exit(1)

    # 3. Découpage en fragments
    print(f"✂️ Découpage de {len(all_documents)} pages en fragments...")
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=200
    )
    chunks = text_splitter.split_documents(all_documents)
    print(f"🧩 {len(chunks)} fragments créés.")

    # 4. Vectorisation par paquets (Batching)
    print("🧠 Génération des embeddings et création de la base...")
    # Utilisation du modèle recommandé text-embedding-004
    embeddings = GoogleGenerativeAIEmbeddings(model="models/text-embedding-004")

    batch_size = 50  # On envoie 50 fragments par 50 pour la stabilité
    vectorstore = None
    
    for i in range(0, len(chunks), batch_size):
        batch = chunks[i : i + batch_size]
        current_batch_num = i // batch_size + 1
        total_batches = (len(chunks) // batch_size) + 1
        
        print(f"   📤 Envoi du paquet {current_batch_num}/{total_batches}... ", end="", flush=True)
        
        try:
            if vectorstore is None:
                vectorstore = Chroma.from_documents(
                    documents=batch,
                    embedding=embeddings,
                    persist_directory=PERSIST_DIRECTORY
                )
            else:
                vectorstore.add_documents(documents=batch)
            print("✅")
        except Exception as e:
            print(f"❌ Erreur lors de l'envoi du paquet : {e}")
            sys.exit(1)

    print("-" * 50)
    print(f"✅ SUCCÈS TOTAL : Base créée avec {len(chunks)} fragments.")
    print("-" * 50)

if __name__ == "__main__":
    main()
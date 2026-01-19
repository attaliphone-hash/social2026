import os
from dotenv import load_dotenv
from pinecone import Pinecone
from langchain_community.document_loaders import PyPDFLoader, TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_pinecone import PineconeVectorStore

load_dotenv()

# Config
PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
INDEX_NAME = "expert-social"

pc = Pinecone(api_key=PINECONE_API_KEY)
index = pc.Index(INDEX_NAME)
embeddings = GoogleGenerativeAIEmbeddings(model="models/text-embedding-004")

def update_dynamic_docs():
    print("⚡ MISE À JOUR RAPIDE (REF & DOC)...")

    # 1. Suppression des anciens REF et DOC uniquement
    print("🧹 Nettoyage des anciens barèmes et docs dans Pinecone...")
    try:
        # On filtre par catégorie pour ne pas toucher aux CODES
        index.delete(filter={"category": {"$in": ["REF", "DOC"]}})
        print("✅ Anciens REF et DOC supprimés.")
    except Exception as e:
        print(f"⚠️ Erreur nettoyage: {e}")

    # 2. Chargement des nouveaux fichiers
    documents = []
    data_path = "./data_clean"
    
    print(f"📂 Lecture des fichiers REF_ et DOC_ dans {data_path}...")
    for root, dirs, files in os.walk(data_path):
        for filename in files:
            if filename.startswith("REF_") or filename.startswith("DOC_"):
                filepath = os.path.join(root, filename)
                category = "REF" if filename.startswith("REF_") else "DOC"
                
                try:
                    if filename.endswith(".pdf"):
                        loader = PyPDFLoader(filepath)
                    else:
                        loader = TextLoader(filepath, encoding="utf-8")
                    
                    docs = loader.load()
                    for d in docs:
                        d.metadata["source"] = filename
                        d.metadata["category"] = category
                    documents.extend(docs)
                    print(f"   -> Prêt : {filename}")
                except Exception as e:
                    print(f"   ❌ Erreur {filename}: {e}")

    if not documents:
        print("ℹ️ Aucun fichier REF_ ou DOC_ trouvé.")
        return

    # 3. Découpage
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=100)
    chunks = text_splitter.split_documents(documents)
    print(f"✂️  {len(chunks)} nouveaux blocs à injecter.")

    # 4. Injection
    print("🧠 Envoi vers Pinecone...")
    PineconeVectorStore.from_documents(
        chunks, 
        embeddings, 
        index_name=INDEX_NAME
    )
    print("🎉 MISE À JOUR TERMINÉE ! (Le Code du Travail n'a pas été touché)")

if __name__ == "__main__":
    update_dynamic_docs()
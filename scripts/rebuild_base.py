import os
from dotenv import load_dotenv
from pinecone import Pinecone
from langchain_community.document_loaders import PyPDFLoader, TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_pinecone import PineconeVectorStore

load_dotenv()

# Config
INDEX_NAME = "expert-social"

# Modèle Gemini 2026 (3072 dimensions)
embeddings = GoogleGenerativeAIEmbeddings(model="models/gemini-embedding-001")

def rebuild_full_index():
    print("\n" + "═"*60)
    print("🏗️  RECONSTRUCTION INTÉGRALE DE LA MÉMOIRE (3072d)")
    print("═"*60)

    # 1. Connexion et Nettoyage TOTAL
    pc = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))
    index = pc.Index(INDEX_NAME)
    
    print("🧹 Vidage complet de l'index Pinecone...")
    index.delete(delete_all=True)
    print("✅ Index prêt et vierge.")

    # 2. Chargement de TOUS les fichiers (Codes + Barèmes + Jurisprudence)
    documents = []
    data_path = "./data_clean"
    
    print(f"\n📂 Lecture du dossier {data_path}...")
    
    for filename in os.listdir(data_path):
        if filename.startswith("."): continue
        
        filepath = os.path.join(data_path, filename)
        
        # Attribution d'une catégorie propre
        if "Travail" in filename: category = "CODE_TRAVAIL"
        elif "Secu" in filename: category = "CODE_SECU"
        elif filename.startswith("REF_"): category = "REF"
        elif filename.startswith("DOC_"): category = "DOC"
        else: category = "AUTRE"

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
            print(f"   ➕ {filename} chargé ({category})")
        except Exception as e:
            print(f"   ❌ Erreur sur {filename}: {e}")

    # 3. Découpage
    print(f"\n✂️  Découpage en blocs de 1000 caractères...")
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=100)
    chunks = text_splitter.split_documents(documents)

    # 4. Envoi massif
    print(f"\n🧠 Envoi de {len(chunks)} blocs vers Pinecone (Modèle 001)...")
    PineconeVectorStore.from_documents(
        chunks, 
        embeddings, 
        index_name=INDEX_NAME
    )
    
    print("\n" + "═"*60)
    print("🎉 BRAVO : BASE DE CONNAISSANCES RÉINITIALISÉE !")
    print("═"*60 + "\n")

if __name__ == "__main__":
    rebuild_full_index()
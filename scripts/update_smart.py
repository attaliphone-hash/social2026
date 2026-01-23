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
    print("\n" + "="*60)
    print("⚡ MISE À JOUR CIBLÉE (JURISPRUDENCE & CHIFFRES)")
    print("="*60)
    print("ℹ️  MODE : Chirurgical")
    print("🛡️  SÉCURITÉ : Le 'Code du Travail' et 'Code Sécu' NE SERONT PAS TOUCHÉS.")
    print("-" * 60)

    # 1. Suppression des anciens REF et DOC uniquement
    print("\n1️⃣  NETTOYAGE PRÉALABLE")
    print("   🧹 Suppression des anciennes versions de REF (Barèmes) et DOC (Jurisprudence)...")
    try:
        # On filtre par catégorie pour ne pas toucher aux CODES
        index.delete(filter={"category": {"$in": ["REF", "DOC"]}})
        print("   ✅ Nettoyage terminé (Les CODES sont restés intacts).")
    except Exception as e:
        print(f"   ⚠️ Erreur nettoyage: {e}")

    # 2. Chargement des nouveaux fichiers
    print("\n2️⃣  LECTURE DES FICHIERS LOCAUX")
    documents = []
    data_path = "./data_clean"
    
    count_skipped = 0
    
    for root, dirs, files in os.walk(data_path):
        for filename in files:
            filepath = os.path.join(root, filename)
            
            # CAS 1 : C'est un fichier à mettre à jour (REF ou DOC)
            if filename.startswith("REF_") or filename.startswith("DOC_"):
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
                    print(f"   📥 Ajouté au panier : {filename}")
                except Exception as e:
                    print(f"   ❌ Erreur lecture {filename}: {e}")
            
            # CAS 2 : C'est un fichier système (DS_Store, gitkeep) -> On ignore silencieusement
            elif filename.startswith("."):
                continue
                
            # CAS 3 : C'est un autre fichier (Probablement un CODE ou autre) -> On le protège
            else:
                count_skipped += 1
                # On l'affiche en gris (ou juste un message simple)
                print(f"   🛡️  PROTECTION (Ignoré) : {filename}")

    if not documents:
        print("\n❌ Aucun fichier REF_ ou DOC_ trouvé à mettre à jour.")
        return

    # 3. Découpage
    print(f"\n3️⃣  DÉCOUPAGE INTELLIGENT")
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=100)
    chunks = text_splitter.split_documents(documents)
    print(f"   ✂️  Préparation de {len(chunks)} fragments de texte.")

    # 4. Injection
    print("\n4️⃣  ENVOI VERS LE CERVEAU (PINECONE)")
    print("   🧠 Synchronisation en cours...")
    PineconeVectorStore.from_documents(
        chunks, 
        embeddings, 
        index_name=INDEX_NAME
    )
    
    print("\n" + "="*60)
    print("🎉 SUCCÈS : BASE DE CONNAISSANCES MISE À JOUR !")
    print(f"📊 Bilan : {len(chunks)} blocs mis à jour | {count_skipped} fichiers protégés (Codes).")
    print("="*60 + "\n")

if __name__ == "__main__":
    update_dynamic_docs()
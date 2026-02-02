import os
import time
from dotenv import load_dotenv
from langchain_community.document_loaders import PyPDFLoader, TextLoader
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_pinecone import PineconeVectorStore
from langchain_text_splitters import RecursiveCharacterTextSplitter
from pinecone import Pinecone

# 1. Chargement Config
load_dotenv()
PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
PINECONE_INDEX_NAME = "expert-social"
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY") 

# --- SÉCURITÉ CRITIQUE (AJOUTÉE) ---
if not PINECONE_API_KEY or not GOOGLE_API_KEY:
    print("❌ ERREUR CRITIQUE : Clés API manquantes dans le fichier .env")
    print("   Arrêt immédiat pour protéger la base de données.")
    exit()

# Dossier des données
DATA_PATH = "data_clean"

# 2. Initialisation Pinecone
print("🚀 DÉMARRAGE DE LA REFONTE TOTALE (SMART SPLIT / 3072d)...")
try:
    pc = Pinecone(api_key=PINECONE_API_KEY)
    index = pc.Index(PINECONE_INDEX_NAME)
    
    # Test de connexion avant suppression
    index.describe_index_stats()
    print("✅ Connexion Pinecone validée.")
except Exception as e:
    print(f"❌ Impossible de se connecter à Pinecone : {e}")
    exit()

print("🗑️  SUPPRESSION TOTALE de l'ancienne mémoire...")
try:
    index.delete(delete_all=True)
    print("✅ Mémoire vierge.")
    time.sleep(5) # Pause vitale pour Pinecone après un delete_all
except Exception as e:
    print(f"⚠️ Index déjà vide ou erreur: {e}")

# 3. Le Découpeur Juridique (Smart Splitter)
text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=1200,       
    chunk_overlap=200,     
    separators=["Article ", "\n\n", ". ", " "]
)

documents = []
stats = {"CODES": 0, "REF": 0, "DOC": 0}

print(f"📂 Scan des fichiers sources dans '{DATA_PATH}'...")

VALID_EXTS = [".pdf", ".txt"]

if not os.path.exists(DATA_PATH):
    print(f"❌ ERREUR : Le dossier '{DATA_PATH}' n'existe pas !")
    exit()

for root, dirs, files in os.walk(DATA_PATH):
    if "venv" in root or ".git" in root: continue
    
    for filename in files:
        filepath = os.path.join(root, filename)
        
        category = None
        if filename.startswith("FULL_") or "Code" in filename: category = "CODES" 
        elif filename.startswith("REF_"): category = "REF"   
        elif filename.startswith("DOC_"): category = "DOC"   
        
        if category and any(filename.lower().endswith(e) for e in VALID_EXTS):
            print(f"   -> Lecture de : {filename} ({category})")
            if category in stats: stats[category] += 1
            
            try:
                docs = []
                if filename.lower().endswith(".pdf"):
                    loader = PyPDFLoader(filepath)
                    docs = loader.load()
                elif filename.lower().endswith(".txt"):
                    loader = TextLoader(filepath, encoding="utf-8")
                    docs = loader.load()
                
                for d in docs:
                    d.metadata["source"] = filename
                    d.metadata["category"] = category
                    if category == "CODES":
                        d.metadata["importance"] = "high"
                
                documents.extend(docs)
                
            except Exception as e:
                print(f"   ❌ Erreur lecture {filename}: {e}")

if not documents:
    print("❌ ALERTE : Aucun fichier (FULL_, REF_, DOC_) trouvé !")
    exit()

print(f"\n📊 Bilan : {stats['CODES']} Codes Complets | {stats['REF']} Barèmes | {stats['DOC']} Docs")

# 4. Traitement
print(f"\n✂️  Découpage intelligent (Cela peut prendre 1-2 minutes)...")
final_chunks = text_splitter.split_documents(documents)
print(f"🧩 RÉSULTAT : {len(final_chunks)} blocs de connaissance haute définition.")

# 5. Injection
print("🧠 Injection dans Pinecone (C'est le moment critique)...")

# Configuration explicite (Sécurisée)
embeddings = GoogleGenerativeAIEmbeddings(
    model="models/gemini-embedding-001",
    google_api_key=GOOGLE_API_KEY, # Clé explicite
    task_type="retrieval_document"
)

batch_size = 50 
total_batches = len(final_chunks) // batch_size + 1

for i in range(0, len(final_chunks), batch_size):
    batch = final_chunks[i:i + batch_size]
    try:
        PineconeVectorStore.from_documents(batch, embeddings, index_name=PINECONE_INDEX_NAME)
        percent = round((i / len(final_chunks)) * 100)
        print(f"   ✓ Progression : {percent}% (Lot {i//batch_size + 1}/{total_batches})")
    except Exception as e:
        print(f"   ❌ Erreur lot {i}: {e}")
        time.sleep(5) 

print("\n🎉 MISSION ACCOMPLIE. Base reconstruite en 3072 dimensions.")
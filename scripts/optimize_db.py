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

# 2. Initialisation Pinecone
print("🚀 DÉMARRAGE DE LA REFONTE TOTALE (VERSION PRO)...")
pc = Pinecone(api_key=PINECONE_API_KEY)
index = pc.Index(PINECONE_INDEX_NAME)

print("🗑️  SUPPRESSION TOTALE de l'ancienne mémoire...")
try:
    index.delete(delete_all=True)
    print("✅ Mémoire vierge.")
    time.sleep(5) # Pause vitale pour Pinecone après un delete_all
except Exception as e:
    print(f"⚠️ Index déjà vide ou erreur: {e}")

# 3. Le Découpeur Juridique (Smart Splitter)
# Configuration spécifique pour les textes de loi
text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=1200,       # Taille d'un article de loi moyen + contexte
    chunk_overlap=200,     # Chevauchement pour lier les paragraphes
    separators=[
        "Article ",   # 🎯 CIBLE PRIORITAIRE : On coupe avant tout aux articles
        "\n\n",       # Puis aux paragraphes
        ". ",         # Puis aux phrases
        " "           # Puis aux mots
    ]
)

documents = []
stats = {"CODES": 0, "REF": 0, "DOC": 0}

print("📂 Scan des fichiers sources...")

# Liste des extensions acceptées
VALID_EXTS = [".pdf", ".txt"]

for root, dirs, files in os.walk("."):
    if "venv" in root or ".git" in root: continue
    
    for filename in files:
        filepath = os.path.join(root, filename)
        
        # LOGIQUE DE TRI STRICTE
        category = None
        if filename.startswith("FULL_"): category = "CODES" # Tes gros PDF
        elif filename.startswith("REF_"): category = "REF"   # Tes barèmes
        elif filename.startswith("DOC_"): category = "DOC"   # Tes docs utilisateurs
        
        if category and any(filename.lower().endswith(e) for e in VALID_EXTS):
            print(f"   -> Lecture de : {filename} ({category})")
            stats[category] += 1
            
            try:
                # Lecture
                docs = []
                if filename.lower().endswith(".pdf"):
                    loader = PyPDFLoader(filepath)
                    docs = loader.load()
                elif filename.lower().endswith(".txt"):
                    loader = TextLoader(filepath, encoding="utf-8")
                    docs = loader.load()
                
                # Métadonnées enrichies
                for d in docs:
                    d.metadata["source"] = filename
                    d.metadata["category"] = category
                    # Pour les gros codes, on précise que c'est du droit dur
                    if category == "CODES":
                        d.metadata["importance"] = "high"
                
                documents.extend(docs)
                
            except Exception as e:
                print(f"   ❌ Erreur lecture {filename}: {e}")

if not documents:
    print("❌ ALERTE : Aucun fichier (FULL_, REF_, DOC_) trouvé à la racine !")
    exit()

print(f"\n📊 Bilan : {stats['CODES']} Codes Complets | {stats['REF']} Barèmes | {stats['DOC']} Docs")

# 4. Traitement
print(f"\n✂️  Découpage intelligent (Cela peut prendre 1-2 minutes pour les gros PDF)...")
final_chunks = text_splitter.split_documents(documents)
print(f"🧩 RÉSULTAT : {len(final_chunks)} blocs de connaissance haute définition.")

# 5. Injection
print("🧠 Injection dans Pinecone (C'est le moment critique)...")
embeddings = GoogleGenerativeAIEmbeddings(model="models/text-embedding-004")

# Batch size réduit pour éviter les timeouts sur les gros textes
batch_size = 50 
total_batches = len(final_chunks) // batch_size + 1

for i in range(0, len(final_chunks), batch_size):
    batch = final_chunks[i:i + batch_size]
    try:
        PineconeVectorStore.from_documents(batch, embeddings, index_name=PINECONE_INDEX_NAME)
        # Petite barre de progression maison
        percent = round((i / len(final_chunks)) * 100)
        print(f"   ✓ Progression : {percent}% (Lot {i//batch_size + 1}/{total_batches})")
    except Exception as e:
        print(f"   ❌ Erreur lot {i}: {e}")
        time.sleep(5) # On attend un peu et on espère que le prochain passe

print("\n🎉 MISSION ACCOMPLIE. Ton IA a maintenant lu le Code complet.")
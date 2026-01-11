import os
import time
from dotenv import load_dotenv

# Imports LangChain & Pinecone
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_pinecone import PineconeVectorStore
from pinecone import Pinecone, ServerlessSpec

# 1. Chargement des clés
load_dotenv()
api_key = os.getenv("GOOGLE_API_KEY")
pinecone_key = os.getenv("PINECONE_API_KEY")

if not api_key or not pinecone_key:
    raise ValueError("⚠️ Clés API manquantes dans le fichier .env")

print("✅ Clés chargées avec succès.")

# 2. Configuration Pinecone
pc = Pinecone(api_key=pinecone_key)
INDEX_NAME = "expert-social"  # Le nom exact que vous avez mis sur le site

# Vérification que l'index existe
existing_indexes = [i.name for i in pc.list_indexes()]
if INDEX_NAME not in existing_indexes:
    print(f"❌ L'index '{INDEX_NAME}' n'existe pas sur votre compte Pinecone.")
    print("👉 Vérifiez le nom ou créez-le sur pinecone.io (Dimension: 768, Metric: cosine)")
    exit()

print(f"✅ Index '{INDEX_NAME}' détecté.")

# 3. Préparation du modèle d'embedding (Le même que dans l'app)
embeddings = GoogleGenerativeAIEmbeddings(
    model="models/text-embedding-004",
    google_api_key=api_key
)

# 4. Lecture des fichiers locaux (Votre dossier "data_clean")
print("📂 Lecture des fichiers locaux...")
texts = []
metadatas = []

if os.path.exists("data_clean"):
    files = [f for f in os.listdir("data_clean") if f.endswith(".txt")]
    print(f"   -> {len(files)} fichiers trouvés.")
    
    for f in files:
        with open(f"data_clean/{f}", "r", encoding="utf-8") as file:
            content = file.read()
            if content.strip():
                # Nettoyage du nom pour la source
                clean_source = f.replace('.txt', '').replace('_', ' ')
                
                texts.append(content)
                metadatas.append({"source": clean_source})
else:
    print("❌ Erreur : Le dossier 'data_clean' est introuvable.")
    exit()

# 5. Envoi vers le Cloud (Pinecone)
if texts:
    print(f"🚀 Démarrage de l'envoi vers Pinecone ({len(texts)} documents)...")
    print("   Cela peut prendre quelques secondes...")
    
    # On utilise la méthode from_texts qui gère l'upload
    vectorstore = PineconeVectorStore.from_texts(
        texts=texts,
        embedding=embeddings,
        metadatas=metadatas,
        index_name=INDEX_NAME
    )
    
    print("🎉 SUCCÈS ! Tous les documents sont maintenant dans le Cloud.")
    print("👉 Vous pouvez désormais supprimer le dossier 'data_clean' de votre futur serveur de prod.")
else:
    print("⚠️ Aucun texte à envoyer.")
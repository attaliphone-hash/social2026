import os
from pinecone import Pinecone
from dotenv import load_dotenv

load_dotenv()

# Connexion
pc = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))
index = pc.Index("expert-social")

# 🎯 CIBLE EXACTE (Basé sur ton dossier data_clean)
# C'est ainsi que ton script d'ingestion nomme les sources
target_source = "data_clean/Structure réponses.txt"

print(f"🔍 Recherche et suppression de : {target_source}")

# La commande magique
index.delete(filter={"source": target_source})

print("✅ Suppression terminée (si le fichier existait, il a disparu).")
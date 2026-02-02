import os
from pinecone import Pinecone
from dotenv import load_dotenv

load_dotenv()

# On utilise la clé configurée localement
api_key = os.getenv("PINECONE_API_KEY")
index_name = "expert-social"

try:
    pc = Pinecone(api_key=api_key)
    index = pc.Index(index_name)
    stats = index.describe_index_stats()
    
    print("\n" + "="*40)
    print("📊 DIAGNOSTIC PINECONE")
    print("="*40)
    print(f"✅ Connexion : OK")
    print(f"📏 Dimension Index : {stats['dimension']}")
    print(f"📦 Total Vecteurs : {stats['total_vector_count']}")
    
    if stats['dimension'] != 768:
        print("\n❌ CONFLIT DÉTECTÉ : Votre index est en 3072 dimensions.")
        print("   Le modèle Google 'embedding-001' ne produit que 768 dimensions.")
        print("   SOLUTION : Supprimez l'index et recréez-le en 768.")
    
    if stats['total_vector_count'] == 0:
        print("\n⚠️ INDEX VIDE : Aucun document n'est chargé dans Pinecone.")
        print("   Lancez votre script d'indexation (ex: scripts/index_data.py).")
    
    print("="*40 + "\n")
        
except Exception as e:
    print(f"\n💥 ERREUR DE CONNEXION : {e}")
    print("Vérifiez que PINECONE_API_KEY est bien dans votre .env local.")

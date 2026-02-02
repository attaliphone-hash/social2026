import os
from dotenv import load_dotenv
from langchain_google_genai import GoogleGenerativeAIEmbeddings

# 1. On charge vos clés
load_dotenv()
api_key = os.getenv("GOOGLE_API_KEY")

if not api_key:
    print("❌ Pas de clé API trouvée. Vérifiez votre .env")
    exit()

print("🕵️‍♂️ ENQUÊTE SUR LA DIMENSION RÉELLE...")

try:
    # 2. On charge EXACTEMENT le modèle que vous avez dans ia_service.py
    embeddings = GoogleGenerativeAIEmbeddings(
        model="models/gemini-embedding-001", 
        google_api_key=api_key
    )
    
    # 3. On génère un vecteur pour un mot simple
    vector = embeddings.embed_query("Test")
    
    # 4. LE VERDICT
    print("\n" + "="*40)
    print(f"📏 DIMENSION GÉNÉRÉE : {len(vector)}")
    print("="*40 + "\n")
    
    if len(vector) == 768:
        print("👉 CONCLUSION : Votre code génère du 768.")
        print("   Votre index Pinecone est en 3072.")
        print("   ❌ C'EST BIEN UNE INCOMPATIBILITÉ DE TAILLE (Clé trop petite pour la serrure).")
    elif len(vector) == 3072:
        print("👉 CONCLUSION : Votre code génère du 3072.")
        print("   Votre index Pinecone est en 3072.")
        print("   ✅ LES TAILLES CORRESPONDENT.")
        print("   (Le problème vient donc juste du fait que la base est vide).")

except Exception as e:
    print(f"❌ ERREUR LORS DU TEST : {e}")
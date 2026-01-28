"""
Script pour lister les modèles d'embedding Google disponibles.
"""
import os
from dotenv import load_dotenv

# Charger les variables d'environnement
load_dotenv()

# Vérifier que la clé API est présente
api_key = os.getenv("GOOGLE_API_KEY")
if not api_key:
    print("❌ ERREUR : GOOGLE_API_KEY non trouvée dans .env")
    exit(1)

print(f"✅ Clé API trouvée : {api_key[:10]}...\n")

# Tester avec langchain_google_genai (celui utilisé dans votre app)
print("=" * 60)
print("TEST 1 : Avec langchain_google_genai (votre config actuelle)")
print("=" * 60)

try:
    from langchain_google_genai import GoogleGenerativeAIEmbeddings
    
    # Liste des modèles à tester
    models_to_test = [
        "models/embedding-001",
        "models/text-embedding-004",
        "embedding-001",
        "text-embedding-004",
        "models/text-embedding-latest",
    ]
    
    print("\n🧪 Test des modèles d'embedding :\n")
    
    for model_name in models_to_test:
        try:
            embeddings = GoogleGenerativeAIEmbeddings(
                model=model_name,
                google_api_key=api_key
            )
            # Tester avec un petit texte
            result = embeddings.embed_query("Test")
            print(f"✅ {model_name:<35} → FONCTIONNE (dim: {len(result)})")
        except Exception as e:
            error_msg = str(e)[:60]
            print(f"❌ {model_name:<35} → ERREUR: {error_msg}")
    
except ImportError as e:
    print(f"❌ Impossible d'importer langchain_google_genai: {e}")

# Tester avec google.generativeai direct
print("\n" + "=" * 60)
print("TEST 2 : Avec google.generativeai (API directe)")
print("=" * 60)

try:
    import google.generativeai as genai
    
    genai.configure(api_key=api_key)
    
    print("\n📋 Tous les modèles disponibles :\n")
    
    embedding_models = []
    other_models = []
    
    for model in genai.list_models():
        model_name = model.name
        supported = ", ".join(model.supported_generation_methods)
        
        if 'embed' in model_name.lower() or 'embedContent' in supported:
            embedding_models.append((model_name, supported))
        else:
            other_models.append((model_name, supported))
    
    if embedding_models:
        print("🎯 MODÈLES D'EMBEDDING (utilisez ces noms) :")
        for name, methods in embedding_models:
            print(f"   ✅ {name}")
            print(f"      Méthodes: {methods}\n")
    else:
        print("⚠️  Aucun modèle d'embedding trouvé avec 'embed' dans le nom")
    
    print("\n📝 Autres modèles (génération de texte) :")
    for name, methods in other_models[:5]:  # Limiter à 5 pour la lisibilité
        print(f"   • {name} ({methods})")
    
    if len(other_models) > 5:
        print(f"   ... et {len(other_models) - 5} autres modèles")

except ImportError:
    print("❌ google.generativeai n'est pas installé")
    print("💡 Installez avec : pip install google-generativeai")
except Exception as e:
    print(f"❌ Erreur : {e}")

print("\n" + "=" * 60)
print("🎯 CONCLUSION")
print("=" * 60)
print("\nUtilisez le premier modèle marqué ✅ dans services/ia_service.py")
print("et dans scripts/update_smart.py\n")
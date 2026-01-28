# test_embeddings.py
import os
from dotenv import load_dotenv
import google.generativeai as genai

load_dotenv()

genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

print("📋 Modèles d'embedding disponibles :\n")
for model in genai.list_models():
    if 'embed' in model.name.lower():
        print(f"✅ {model.name}")
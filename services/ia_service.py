import os
import streamlit as st
from langchain_google_genai import GoogleGenerativeAIEmbeddings, ChatGoogleGenerativeAI
from langchain_pinecone import PineconeVectorStore
from utils.helpers import clean_source_name, logger  # ✅ Import centralisé

class IAService:
    def __init__(self):
        # Initialisation des clés et modèles
        self.google_api_key = os.getenv("GOOGLE_API_KEY")
        self.pinecone_api_key = os.getenv("PINECONE_API_KEY")
        self.index_name = "expert-social"
        
        if not self.google_api_key or not self.pinecone_api_key:
            logger.error("IAService: Clés API manquantes (Google ou Pinecone)")

    def get_llm(self):
        """Retourne l'instance du modèle Gemini 2.0 Flash"""
        return ChatGoogleGenerativeAI(
            model="gemini-2.0-flash", # ✅ Conforme à vos instructions de sauvegarde
            google_api_key=self.google_api_key,
            temperature=0,
            streaming=True
        )

    def search_documents(self, query, k=6):
        """Recherche les documents pertinents dans Pinecone"""
        try:
            # ✅ RÉTABLISSEMENT DE VOTRE SYNTAXE PRÉCISE :
            embeddings = GoogleGenerativeAIEmbeddings(
                model="models/gemini-embedding-001", 
                google_api_key=self.google_api_key,
                task_type="retrieval_query"
            )
            
            vectorstore = PineconeVectorStore(
                index_name=self.index_name,
                embedding=embeddings,
                pinecone_api_key=self.pinecone_api_key
            )
            
            docs = vectorstore.similarity_search(query, k=k)
            
            # ✅ Application du nettoyage centralisé sur chaque document trouvé
            for doc in docs:
                raw_path = doc.metadata.get('source', 'Inconnu')
                category = doc.metadata.get('category', 'AUTRE')
                # Utilisation de la fonction importée de utils.helpers
                doc.metadata['clean_name'] = clean_source_name(raw_path, category)
                
            return docs
            
        except Exception as e:
            logger.error(f"IAService: Erreur lors de la recherche Pinecone : {e}")
            return []

    # ✅ Note : La fonction clean_source_name_internal a été SUPPRIMÉE 
    # pour respecter la règle de non-duplication du code.
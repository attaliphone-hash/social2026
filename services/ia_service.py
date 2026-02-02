import os
from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAIEmbeddings
from langchain_pinecone import PineconeVectorStore
from pinecone import Pinecone

class IAService:
    def __init__(self):
        # On récupère la config depuis le session_state (initialisé dans app.py)
        import streamlit as st
        self.config = st.session_state.config
        
        # 1. Initialisation de Pinecone (La mémoire)
        if self.config.pinecone_api_key:
            try:
                pc = Pinecone(api_key=self.config.pinecone_api_key)
                index_name = "expert-social"
                
                # --- CORRECTION 2026 : Passage au nouveau modèle standard gemini-embedding-001 ---
                # Ce modèle génère 3072 dimensions par défaut.
                embeddings = GoogleGenerativeAIEmbeddings(
                    model="models/gemini-embedding-001", 
                    google_api_key=self.config.google_api_key
                )
                
                # Connexion au VectorStore LangChain
                self.vectorstore = PineconeVectorStore(
                    index_name=index_name,
                    embedding=embeddings
                )
                print("✅ Pinecone connecté avec succès (Modèle 001 - 3072d).")
            except Exception as e:
                print(f"❌ Erreur critique Pinecone : {e}")

        # 2. Initialisation de GEMINI (Le modèle Flash)
        if self.config.google_api_key:
            self.llm = ChatGoogleGenerativeAI(
                model="gemini-2.0-flash", # Votre modèle validé
                temperature=0, # Rigueur maximale pour le droit social
                google_api_key=self.config.google_api_key,
                streaming=True
            )

    def search_documents(self, query, k=4):
        """Recherche les documents pertinents dans Pinecone"""
        if not self.vectorstore:
            return []
        try:
            # Recherche de similarité
            docs = self.vectorstore.similarity_search(query, k=k)
            
            # --- AJOUT DU PONT DE COHÉRENCE ---
            # On applique le label propre (ex: Code du Travail 2026) dès la sortie de base
            from app import clean_source_name
            for doc in docs:
                raw_path = doc.metadata.get('source', 'AUTRE')
                category = doc.metadata.get('category', 'AUTRE')
                # On crée une nouvelle clé 'clean_name' que le prompt utilisera
                doc.metadata['clean_name'] = clean_source_name(raw_path, category)
            # ----------------------------------
            
            return docs
        except Exception as e:
            print(f"Erreur recherche Pinecone: {e}")
            return []
    def get_llm(self):
        """Retourne l'instance du LLM pour LangChain"""
        return self.llm
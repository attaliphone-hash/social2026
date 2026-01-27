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
                
                # Modèle d'embeddings (Vecteur Texte <-> Vecteur)
                embeddings = GoogleGenerativeAIEmbeddings(
                    model="models/text-embedding-004", 
                    google_api_key=self.config.google_api_key
                )
                
                # Connexion au VectorStore LangChain
                self.vectorstore = PineconeVectorStore(
                    index_name=index_name,
                    embedding=embeddings
                )
                print("✅ Pinecone connecté avec succès.")
            except Exception as e:
                print(f"❌ Erreur critique Pinecone : {e}")

        # 2. Initialisation de GEMINI (Le modèle Flash)
        if self.config.google_api_key:
            self.llm = ChatGoogleGenerativeAI(
                model="gemini-2.0-flash-exp", # Votre modèle validé
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
            return docs
        except Exception as e:
            print(f"Erreur recherche Pinecone: {e}")
            return []

    def get_llm(self):
        """Retourne l'instance du LLM pour LangChain"""
        return self.llm
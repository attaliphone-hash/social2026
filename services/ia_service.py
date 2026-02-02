import os
import streamlit as st
from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAIEmbeddings
from langchain_pinecone import PineconeVectorStore
from pinecone import Pinecone

# ✅ CORRECTION 1 : On définit la fonction ICI pour éviter l'import circulaire avec app.py
def clean_source_name_internal(filename, category="AUTRE"):
    """Nettoyage interne pour le service IA - Coupe le cordon avec app.py"""
    filename = os.path.basename(filename).replace('.pdf', '').replace('.txt', '')
    if "Code_Travail" in filename: return "Code du Travail 2026"
    elif "Code_Secu" in filename: return "Code de la Sécurité Sociale 2026"
    elif category == "REF" or filename.startswith("REF_"): return "Barèmes Officiels 2026"
    elif category == "DOC" or filename.startswith("DOC_"): return "BOSS 2026 et Jurisprudences"
    return filename.replace('_', ' ')

class IAService:
    def __init__(self):
        self.config = st.session_state.config
        self.vectorstore = None
        self.llm = None
        
        # 1. Initialisation de Pinecone
        if self.config.pinecone_api_key:
            try:
                pc = Pinecone(api_key=self.config.pinecone_api_key)
                index_name = "expert-social"
                
                # Modèle d'embedding (DOIT ÊTRE LE MÊME QUE update_smart.py)
                embeddings = GoogleGenerativeAIEmbeddings(
                    model="models/gemini-embedding-001", 
                    google_api_key=self.config.google_api_key,
                    task_type="retrieval_query"
                )
                
                self.vectorstore = PineconeVectorStore(
                    index_name=index_name,
                    embedding=embeddings
                )
                print("✅ Service IA : Pinecone connecté (3072d).")
            except Exception as e:
                st.error(f"❌ ERREUR INIT PINECONE : {e}")

        # 2. Initialisation de GEMINI
        if self.config.google_api_key:
            try:
                self.llm = ChatGoogleGenerativeAI(
                    model="gemini-2.0-flash",
                    temperature=0,
                    google_api_key=self.config.google_api_key,
                    streaming=True
                )
            except Exception as e:
                st.error(f"❌ ERREUR INIT GEMINI : {e}")

    def search_documents(self, query, k=4):
        if not self.vectorstore:
            st.error("⚠️ La mémoire (Pinecone) n'est pas connectée.")
            return []
            
        try:
            # Recherche brute
            docs = self.vectorstore.similarity_search(query, k=k)
            
            # ✅ CORRECTION 1 : Utilisation de la fonction locale (plus d'import toxique)
            for doc in docs:
                raw_path = doc.metadata.get('source', 'AUTRE')
                category = doc.metadata.get('category', 'AUTRE')
                # On enrichit l'objet doc directement
                doc.metadata['clean_name'] = clean_source_name_internal(raw_path, category)
            
            return docs

        except Exception as e:
            st.error(f"❌ ERREUR RECHERCHE PINECONE : {str(e)}")
            return []

    def get_llm(self):
        return self.llm
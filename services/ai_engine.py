import os
import streamlit as st
from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAIEmbeddings
from langchain_pinecone import PineconeVectorStore
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from rules.engine import SocialRuleEngine

# ==============================================================================
# CHARGEMENT DES MOTEURS (CACHÉ)
# ==============================================================================

@st.cache_resource
def load_engine():
    """Charge le Cerveau Logique V4 (Règles YAML)"""
    return SocialRuleEngine()

@st.cache_resource
def load_ia_system():
    """Charge le Cerveau Créatif (Gemini + Pinecone CLOUD)"""
    api_key = os.getenv("GOOGLE_API_KEY")
    
    # 1. Modèle d'Embedding
    embeddings = GoogleGenerativeAIEmbeddings(model="models/text-embedding-004", google_api_key=api_key)
    
    # 2. Connexion à PINECONE (Cloud)
    vectorstore = PineconeVectorStore.from_existing_index(
        index_name="expert-social",
        embedding=embeddings
    )
    
    # 3. LLM (Gemini 2.0)
    llm = ChatGoogleGenerativeAI(model="gemini-2.0-flash-exp", temperature=0, google_api_key=api_key)
    
    return vectorstore, llm

# ==============================================================================
# FONCTIONS D'INTERROGATION
# ==============================================================================

def build_context(query, vectorstore):
    """Construction du contexte via Pinecone"""
    raw_docs = vectorstore.similarity_search(query, k=20)
    context_text = ""
    for d in raw_docs:
        raw_src = d.metadata.get('source', 'Source Inconnue')
        clean_name = os.path.basename(raw_src).replace('.pdf', '').replace('.txt', '').replace('.csv', '')
        
        if "REF" in clean_name: pretty_src = "Barème Officiel"
        elif "LEGAL" in clean_name: pretty_src = "Code du Travail"
        else: pretty_src = f"BOSS : {clean_name}"
        
        context_text += f"[DOCUMENT : {pretty_src}]\n{d.page_content}\n\n"
    return context_text

def get_gemini_response(query, context, llm, user_doc_content=None):
    """Prompt Hybride : Gère BOSS + Document Utilisateur"""
    
    user_doc_section = f"\n--- DOCUMENT UTILISATEUR ---\n{user_doc_content}\n" if user_doc_content else ""

    prompt = ChatPromptTemplate.from_template("""
    Tu es l'Expert Social Pro 2026.
    
    CONTEXTE :
    {context}
    """ + user_doc_section + """
    
    MISSION :
    Réponds à la question suivante en t'appuyant EXCLUSIVEMENT sur les documents ci-dessus.
    QUESTION : {question}
    
    CONSIGNES D'AFFICHAGE STRICTES :
    1. CITATIONS DANS LE TEXTE : Utilise la balise HTML <sub> pour les citations précises (ex: <sub>*[BOSS : Barème]*</sub>).
    
    2. FOOTER RÉCAPITULATIF (OBLIGATOIRE) :
       Tu DOIS terminer ta réponse EXACTEMENT par ce bloc (avec la ligne de séparation) :
       
       ---
       **Sources utilisées :**
       * BOSS : [Nom du document]
       * [Autre Source]
    """)
    chain = prompt | llm | StrOutputParser()
    response = chain.invoke({"context": context, "question": query})
    
    # SÉCURITÉ ANTI-ERRATIQUE
    if "Sources utilisées :" in response and "---" not in response[-500:]:
        response = response.replace("**Sources utilisées :**", "\n\n---\n**Sources utilisées :**")
        
    return response
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
    """
    Construction du contexte via Pinecone.
    VERSION GOLDEN PURE : k=20 et AUCUN filtrage.
    On accepte la redondance pour ne rater aucune nuance juridique.
    """
    raw_docs = vectorstore.similarity_search(query, k=20)
    
    context_text = ""
    # RETOUR A LA LOGIQUE SIMPLE : On empile tout, sans filtrer les doublons.
    # C'est ce qui assurait la qualité de l'ancienne version.
    for d in raw_docs:
        raw_src = d.metadata.get('source', 'Source Inconnue')
        clean_name = os.path.basename(raw_src).replace('.pdf', '').replace('.txt', '').replace('.csv', '')
        
        if "REF" in clean_name: pretty_src = "Barème Officiel"
        elif "LEGAL" in clean_name: pretty_src = "Code du Travail / SS"
        else: pretty_src = f"BOSS : {clean_name}"
        
        context_text += f"[DOCUMENT : {pretty_src}]\n{d.page_content}\n\n"
        
    return context_text

def get_gemini_response(query, context, llm, user_doc_content=None):
    """Prompt Hybride : Gère BOSS + Document Utilisateur + Articles de Loi"""
    
    user_doc_section = f"\n--- DOCUMENT UTILISATEUR ---\n{user_doc_content}\n" if user_doc_content else ""

    prompt = ChatPromptTemplate.from_template("""
    Tu es l'Expert Social Pro 2026.
    
    MISSION :
    Réponds aux questions en t'appuyant EXCLUSIVEMENT sur les DOCUMENTS fournis.
    
    CONSIGNES D'AFFICHAGE STRICTES (ACCORD CLIENT) :
    1. CITATIONS DANS LE TEXTE : Utilise la balise HTML <sub> pour les citations précises.
       - Pour le BOSS : <sub>*[BOSS : Nom du document]*</sub>
       - Pour les CODES (Travail / Sécu) : Cherche IMPÉRATIVEMENT le numéro de l'article dans le texte (ex: Art. L.123-1) et affiche-le ainsi : <sub>*[Code du Travail : Art. L.XXXX]*</sub>
       - Pour les documents utilisateurs : <sub>*[Document Utilisateur]*</sub>
       INTERDICTION FORMELLE : Ne jamais mentionner "DATA_CLEAN/" ou des extensions comme ".pdf".
    
    2. FOOTER RÉCAPITULATIF (OBLIGATOIRE) :
       À la toute fin de ta réponse, ajoute une ligne de séparation "---".
       Puis écris "**Sources utilisées :**" en gras.
       Liste chaque source avec précision :
       * BOSS : [Nom du document]
       * Code du Travail : [Numéros des articles cités, ex: Art. L.1234-1]
       * Code de la Sécurité Sociale : [Numéros des articles cités]
    
    CONTEXTE :
    {context}
    """ + user_doc_section + """
    
    QUESTION : 
    {question}
    """)
    chain = prompt | llm | StrOutputParser()
    return chain.invoke({"context": context, "question": query})
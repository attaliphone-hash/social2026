# --- 1. CONFIGURATION SQLITE (CRITIQUE POUR CLOUD RUN) ---
import sys
import os

try:
    __import__('pysqlite3')
    sys.modules['sqlite3'] = sys.modules.pop('pysqlite3')
except ImportError:
    pass

import streamlit as st

# --- 2. IMPORTS DES MODULES (FLUX LCEL - SANS 'CHAINS') ---
try:
    # IA et Vecteurs
    from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAIEmbeddings
    from langchain_chroma import Chroma
    from langchain_core.prompts import ChatPromptTemplate
    from langchain_core.runnables import RunnablePassthrough
    from langchain_core.output_parsers import StrOutputParser
    
except ModuleNotFoundError as e:
    st.error(f"❌ Erreur de module : {e}")
    st.info("Vérifiez que votre requirements.txt contient bien langchain-core et langchain-google-genai.")
    st.stop()

# --- 3. CONFIGURATION INTERFACE ET CLÉ API ---
# Utilisation de la clé "Clé Gemini - Assistants" (Consigne 01-01-26)
os.environ["GOOGLE_API_KEY"] = st.secrets["GEMINI_API_KEY"]

st.set_page_config(page_title="Expert Social Pro 2026", layout="wide")
st.title("🤖 Expert Social Pro 2026")

# --- 4. CHARGEMENT DU SYSTÈME RAG ---
@st.cache_resource
def load_system():
    # Embeddings text-embedding-004 stable
    embeddings = GoogleGenerativeAIEmbeddings(model="models/text-embedding-004")
    
    # Dossier de la base (Golden Index)
    persist_directory = "chroma_db"
    
    vectorstore = Chroma(
        persist_directory=persist_directory,
        embedding_function=embeddings
    )
    
    # Modèle gemini-2.0-flash-exp obligatoire (Consigne 17-12-25)
    llm = ChatGoogleGenerativeAI(
        model="gemini-2.0-flash-exp",
        temperature=0,
    )
    
    return vectorstore, llm

vectorstore, llm = load_system()

# --- 5. CONFIGURATION DU PROMPT ET DE LA CHAÎNE LCEL ---
# Cette syntaxe évite totalement le module 'langchain.chains'
prompt = ChatPromptTemplate.from_template("""
Tu es un assistant expert en droit social français. 
Réponds à la question de manière professionnelle en utilisant le contexte fourni.
Cite tes sources (BOSS, Code du travail, etc.) si elles sont présentes.

Contexte :
{context}

Question : {question}
""")

def format_docs(docs):
    return "\n\n".join(doc.page_content for doc in docs)

# Construction de la chaîne par pipe (LCEL)
retriever = vectorstore.as_retriever(search_kwargs={"k": 3})

rag_chain = (
    {"context": retriever | format_docs, "question": RunnablePassthrough()}
    | prompt
    | llm
    | StrOutputParser()
)

# --- 6. GESTION DU CHAT ---
if "messages" not in st.session_state:
    st.session_state.messages = []

# Affichage de l'historique
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Entrée utilisateur
if query := st.chat_input("Posez votre question juridique..."):
    st.session_state.messages.append({"role": "user", "content": query})
    with st.chat_message("user"):
        st.markdown(query)

    with st.chat_message("assistant"):
        with st.spinner("Analyse des sources en cours..."):
            try:
                # Appel direct de la chaîne LCEL
                answer = rag_chain.invoke(query)
                st.markdown(answer)
                st.session_state.messages.append({"role": "assistant", "content": answer})
            except Exception as e:
                st.error(f"Erreur lors de la génération : {e}")
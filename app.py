# --- 1. CONFIGURATION DES CHEMINS ET SQLITE (CRITIQUE POUR CLOUD RUN) ---
import sys
import os

# Force Python à regarder dans le dossier des paquets installés par le Dockerfile
site_packages = "/usr/local/lib/python3.10/site-packages"
if site_packages not in sys.path:
    sys.path.append(site_packages)

# Correctif SQLite pour Chromadb sur Linux (Google Cloud)
__import__('pysqlite3')
sys.modules['sqlite3'] = sys.modules.pop('pysqlite3')

# --- 2. IMPORTS DES MODULES ---
import streamlit as st
from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAIEmbeddings
from langchain_chroma import Chroma
from langchain.chains import create_retrieval_chain
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain_core.prompts import ChatPromptTemplate

# --- 3. CONFIGURATION DE L'INTERFACE ET CLÉ API ---
# Votre clé API est stockée dans les Secrets de Streamlit
os.environ["GOOGLE_API_KEY"] = st.secrets["GEMINI_API_KEY"]

st.set_page_config(page_title="Expert Social Pro 2026", layout="wide")
st.title("🤖 Expert Social Pro 2026")

# --- 4. CHARGEMENT DU SYSTÈME RAG ---
@st.cache_resource
def load_system():
    # Embeddings optimisés
    embeddings = GoogleGenerativeAIEmbeddings(model="models/text-embedding-004")
    
    # Chemin vers la base téléchargée depuis Google Storage
    persist_directory = "chroma_db"
    
    vectorstore = Chroma(
        persist_directory=persist_directory,
        embedding_function=embeddings
    )
    
    # Modèle Gemini 2.0 Flash (Version de référence)
    llm = ChatGoogleGenerativeAI(
        model="gemini-2.0-flash-exp",
        temperature=0,
    )
    
    return vectorstore, llm

vectorstore, llm = load_system()

# --- 5. CONFIGURATION DU PROMPT ET DES CHAÎNES ---
system_prompt = (
    "Tu es un assistant expert en droit social français. "
    "Réponds à la question en utilisant uniquement les extraits fournis. "
    "Cite tes sources si possible. Si la réponse n'est pas dans le contexte, dis-le. "
    "\n\n"
    "{context}"
)

prompt = ChatPromptTemplate.from_messages(
    [
        ("system", system_prompt),
        ("human", "{input}"),
    ]
)

# Création des chaînes LangChain
question_answer_chain = create_stuff_documents_chain(llm, prompt)
rag_chain = create_retrieval_chain(vectorstore.as_retriever(), question_answer_chain)

# --- 6. GESTION DU CHAT ---
if "messages" not in st.session_state:
    st.session_state.messages = []

# Affichage de l'historique des messages
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Zone de saisie utilisateur
if query := st.chat_input("Posez votre question juridique..."):
    st.session_state.messages.append({"role": "user", "content": query})
    with st.chat_message("user"):
        st.markdown(query)

    with st.chat_message("assistant"):
        with st.spinner("Recherche dans les sources officielles..."):
            # Exécution de la recherche et génération
            response = rag_chain.invoke({"input": query})
            answer = response["answer"]
            st.markdown(answer)
            st.session_state.messages.append({"role": "assistant", "content": answer})
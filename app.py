import streamlit as st
import os
import tempfile
from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAIEmbeddings
from langchain_chroma import Chroma
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_community.document_loaders import PyPDFLoader, TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter

# --- CONFIGURATION DE LA PAGE ---
st.set_page_config(
    page_title="Expert Social Pro 2026",
    page_icon="⚖️",
    layout="wide"
)

# --- DICTIONNAIRE DE RENOMMAGE (Le "Maquillage" des sources) ---
# C'est ici qu'on transforme les noms de fichiers techniques en noms clairs pour l'IA et l'utilisateur
NOMS_PROS = {
    "MEMO_CHIFFRES": "🔢 Barèmes Sociaux Officiels 2026",
    "MEMO_JURISPRUDENCE": "⚖️ Jurisprudence de Référence (Socle)",
    "JURISPRUDENCE_SOCLE": "⚖️ Jurisprudence de Référence (Socle)",
    "Code_du_Travail": "📕 Code du Travail",
    "Code_Securite_Sociale": "📗 Code de la Sécurité Sociale",
    "BOSS": "🌐 Doctrine Administrative (BOSS)",
    "Indemnites_Rupture": "🌐 BOSS - Indemnités",
    "Protection_sociale": "🌐 BOSS - Protection Sociale",
    "Frais_professionnels": "🌐 BOSS - Frais Pros"
}

def nettoyer_nom_source(raw_source):
    """Transforme 'data/MEMO_CHIFFRES.txt' en '🔢 Barèmes Sociaux Officiels 2026'"""
    if not raw_source:
        return "Source Inconnue"
        
    # On nettoie le chemin
    nom_fichier = os.path.basename(raw_source)
    
    # On cherche si un mot-clé connu est dans le nom
    for cle, nom_pro in NOMS_PROS.items():
        if cle in nom_fichier:
            return nom_pro
            
    # Sinon on renvoie le nom du fichier nettoyé
    return nom_fichier.replace('.txt', '').replace('.pdf', '').replace('_', ' ')

# --- STYLES CSS ---
st.markdown("""
<style>
    .main { background-color: #f8f9fa; }
    .stChatMessage { background-color: white; border-radius: 10px; padding: 15px; box-shadow: 0 2px 5px rgba(0,0,0,0.05); }
    .stButton>button { width: 100%; border-radius: 5px; }
    h1 { color: #2c3e50; }
    .source-box { font-size: 0.85em; color: #555; border-left: 3px solid #2980b9; padding-left: 10px; margin-top: 5px; }
</style>
""", unsafe_allow_html=True)

# --- INITIALISATION SESSION ---
if "session_id" not in st.session_state:
    st.session_state.session_id = os.urandom(4).hex()
if "messages" not in st.session_state:
    st.session_state.messages = []
if "uploader_key" not in st.session_state:
    st.session_state.uploader_key = 0

# --- CHARGEMENT DU CERVEAU (MODEL & DB) ---
api_key = os.getenv("GOOGLE_API_KEY")
if not api_key:
    st.error("❌ CLÉ API MANQUANTE. Vérifiez vos variables d'environnement.")
    st.stop()

llm = ChatGoogleGenerativeAI(
    model="gemini-2.0-flash-exp",
    temperature=0,
    api_key=api_key
)

embeddings = GoogleGenerativeAIEmbeddings(model="models/text-embedding-004", google_api_key=api_key)
vectorstore = Chroma(persist_directory="chroma_db", embedding_function=embeddings)

# --- BARRE LATÉRALE (UPLOAD) ---
with st.sidebar:
    st.image("avatar-logo.png", width=80)
    st.title("Expert Social 2026")
    st.markdown("---")
    
    uploaded_file = st.file_uploader(
        "📎 Analyser un document (PDF/TXT)", 
        type=["pdf", "txt"],
        key=f"uploader_{st.session_state.uploader_key}"
    )
    
    if uploaded_file:
        with st.status("📥 Lecture en cours...", expanded=True):
            try:
                with tempfile.NamedTemporaryFile(delete=False, suffix=f".{uploaded_file.name.split('.')[-1]}") as tmp:
                    tmp.write(uploaded_file.getvalue())
                    tmp_path = tmp.name
                
                if uploaded_file.name.endswith(".pdf"):
                    loader = PyPDFLoader(tmp_path)
                else:
                    loader = TextLoader(tmp_path)
                    
                docs = loader.load()
                
                # Ajout de métadonnées pour identifier que c'est CE document utilisateur
                for doc in docs:
                    doc.metadata["session_id"] = st.session_state.session_id
                    doc.metadata["source"] = f"📁 {uploaded_file.name}" # Nom explicite
                
                text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=100)
                chunks = text_splitter.split_documents(docs)
                
                vectorstore.add_documents(chunks)
                os.unlink(tmp_path)
                st.success("✅ Document mémorisé !")
                
            except Exception as e:
                st.error(f"Erreur : {e}")

    st.markdown("---")
    if st.button("🧹 Nouvelle Conversation"):
        st.session_state.messages = []
        st.session_state.uploader_key += 1
        st.rerun()

# --- INTERFACE DE CHAT ---
st.title("⚖️ Assistant Juridique & RH")
st.caption("Expertise fiable basée sur le Code du Travail, le BOSS et la Jurisprudence 2026.")

for msg in st.session_state.messages:
    with st.chat_message(msg["role"], avatar="avatar-logo.png" if msg["role"] == "assistant" else None):
        st.markdown(msg["content"])

# --- LOGIQUE DE RÉPONSE ---
if query := st.chat_input("Posez votre question juridique..."):
    # 1. Affichage utilisateur
    st.session_state.messages.append({"role": "user", "content": query})
    with st.chat_message("user"):
        st.markdown(query)

    # 2. Traitement IA
    with st.chat_message("assistant", avatar="avatar-logo.png"):
        with st.status("🔍 Analyse juridique en cours...", expanded=True) as status:
            
            # A. RECHERCHE DANS LE DOCUMENT UTILISATEUR (Filtré par session)
            user_results = vectorstore.similarity_search(
                query, 
                k=10, 
                filter={"session_id": st.session_state.session_id}
            )
            
            # B. RECHERCHE DANS LA LOI (Tout sauf la session actuelle)
            # On cherche large (k=20) pour être sûr de trouver la jurisprudence
            all_results = vectorstore.similarity_search(query, k=20)
            
            # On filtre manuellement pour ne garder que les documents "Officiels" (ceux qui n'ont PAS le session_id actuel)
            law_results = [
                doc for doc in all_results 
                if doc.metadata.get("session_id") != st.session_state.session_id
            ]

            # C. CONSTRUCTION DU CONTEXTE "ÉTIQUETÉ"
            context_parts = []
            
            # Bloc 1 : Le document de l'utilisateur (s'il existe)
            if user_results:
                context_parts.append("\n=== 📂 DOCUMENT SOUMIS PAR L'UTILISATEUR ===")
                for doc in user_results:
                    context_parts.append(f"{doc.page_content}")
            
            # Bloc 2 : Les sources officielles (Loi, Jurisprudence, Chiffres)
            context_parts.append("\n=== 🏛️ RÉFÉRENCES LÉGALES ET BARÈMES OFFICIELS ===")
            for doc in law_results:
                nom_source_pro = nettoyer_nom_source(doc.metadata.get("source", ""))
                # On injecte l'étiquette [SOURCE OFFICIELLE : ...] juste avant le texte
                context_parts.append(f"[SOURCE OFFICIELLE : {nom_source_pro}]\n{doc.page_content}")

            final_context = "\n".join(context_parts)

            # D. PROMPT STRICT
            prompt_template = ChatPromptTemplate.from_template("""
            Tu es l'Expert Social Pro 2026, un assistant juridique de haut niveau.
            
            RÈGLES ABSOLUES :
            1. Tes réponses doivent être juridiquement précises et basées PRIORITAIREMENT sur les [RÉFÉRENCES LÉGALES ET BARÈMES OFFICIELS].
            2. Si l'information provient d'un bloc marqué "[SOURCE OFFICIELLE : ...]", tu dois citer cette source explicitement.
            3. Ne confonds JAMAIS le "DOCUMENT SOUMIS PAR L'UTILISATEUR" avec les sources officielles.
            4. Si la réponse contient des chiffres (montants, taux), vérifie-les dans les Barèmes Officiels fournis.
            
            CONTEXTE :
            {context}
            
            QUESTION DE L'UTILISATEUR :
            {question}
            """)
            
            chain = prompt_template | llm | StrOutputParser()
            response = chain.invoke({"context": final_context, "question": query})
            
            status.update(label="✅ Expertise terminée !", state="complete", expanded=False)

        # 3. Affichage Réponse
        st.markdown(response)
        
        # 4. Affichage des Sources (Proprement)
        with st.expander("📚 Sources et bases juridiques consultées"):
            # Sources Utilisateur
            if user_results:
                st.markdown("#### 📂 Document Utilisateur")
                for doc in user_results:
                    st.caption(f"Extrait : *{doc.page_content[:150]}...*")
            
            # Sources Officielles (Dédoublonnées par nom)
            if law_results:
                st.markdown("#### 🏛️ Sources Officielles")
                sources_affichees = set()
                for doc in law_results:
                    nom = nettoyer_nom_source(doc.metadata.get("source", ""))
                    if nom not in sources_affichees:
                        st.markdown(f"**🔹 {nom}**")
                        # Petit extrait pour prouver la source
                        st.caption(f"_{doc.page_content[:200]}..._") 
                        sources_affichees.add(nom)

    st.session_state.messages.append({"role": "assistant", "content": response})
import streamlit as st
import os
import tempfile
import base64
from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAIEmbeddings
from langchain_chroma import Chroma
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_community.document_loaders import PyPDFLoader, TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter

# --- 1. CONFIGURATION DE LA PAGE ---
st.set_page_config(
    page_title="Expert Social Pro 2026",
    page_icon="⚖️",
    layout="wide"
)

# --- 2. GESTION DU FOND D'ÉCRAN (REMIS EN PLACE) ---
def get_base64(bin_file):
    with open(bin_file, 'rb') as f:
        data = f.read()
    return base64.b64encode(data).decode()

def set_background(png_file):
    bin_str = get_base64(png_file)
    page_bg_img = '''
    <style>
    .stApp {
    background-image: url("data:image/png;base64,%s");
    background-size: cover;
    }
    </style>
    ''' % bin_str
    st.markdown(page_bg_img, unsafe_allow_html=True)

# On cherche l'image de fond (supporte png ou webp comme dans ta structure)
if os.path.exists("background.png"):
    set_background("background.png")
elif os.path.exists("background.webp"):
    set_background("background.webp")

# --- 3. DICTIONNAIRE DE RENOMMAGE (Pour des sources propres) ---
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
    """Transforme un chemin technique en nom lisible."""
    if not raw_source:
        return "Source Inconnue"
    nom_fichier = os.path.basename(raw_source)
    for cle, nom_pro in NOMS_PROS.items():
        if cle in nom_fichier:
            return nom_pro
    return nom_fichier.replace('.txt', '').replace('.pdf', '').replace('_', ' ')

# --- 4. STYLES CSS COMPLÉMENTAIRES ---
st.markdown("""
<style>
    .stChatMessage { background-color: white; border-radius: 10px; padding: 15px; box-shadow: 0 2px 5px rgba(0,0,0,0.05); }
    .stButton>button { width: 100%; border-radius: 5px; }
    h1 { color: #2c3e50; }
</style>
""", unsafe_allow_html=True)

# --- 5. INITIALISATION SESSION ---
if "session_id" not in st.session_state:
    st.session_state.session_id = os.urandom(4).hex()
if "messages" not in st.session_state:
    st.session_state.messages = []
if "uploader_key" not in st.session_state:
    st.session_state.uploader_key = 0

# --- 6. CHARGEMENT DU CERVEAU ---
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

# --- 7. BARRE LATÉRALE (UPLOAD) ---
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
                for doc in docs:
                    doc.metadata["session_id"] = st.session_state.session_id
                    doc.metadata["source"] = f"📁 {uploaded_file.name}"
                
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

# --- 8. INTERFACE DE CHAT ---
st.title("⚖️ Assistant Juridique & RH")
st.caption("Expertise fiable basée sur le Code du Travail, le BOSS et la Jurisprudence 2026.")

for msg in st.session_state.messages:
    with st.chat_message(msg["role"], avatar="avatar-logo.png" if msg["role"] == "assistant" else None):
        st.markdown(msg["content"])

# --- 9. LOGIQUE DE RÉPONSE ET FILTRAGE ---
if query := st.chat_input("Posez votre question juridique..."):
    # Affichage User
    st.session_state.messages.append({"role": "user", "content": query})
    with st.chat_message("user"):
        st.markdown(query)

    # Traitement IA
    with st.chat_message("assistant", avatar="avatar-logo.png"):
        with st.status("🔍 Analyse juridique en cours...", expanded=True) as status:
            
            # Recherche
            user_results = vectorstore.similarity_search(query, k=10, filter={"session_id": st.session_state.session_id})
            all_results = vectorstore.similarity_search(query, k=20)
            law_results = [d for d in all_results if d.metadata.get("session_id") != st.session_state.session_id]

            # Contexte
            context_parts = []
            if user_results:
                context_parts.append("\n=== 📂 DOCUMENT SOUMIS PAR L'UTILISATEUR ===")
                for doc in user_results:
                    context_parts.append(doc.page_content)
            
            context_parts.append("\n=== 🏛️ RÉFÉRENCES LÉGALES ET BARÈMES OFFICIELS ===")
            for doc in law_results:
                nom_pro = nettoyer_nom_source(doc.metadata.get("source", ""))
                context_parts.append(f"[SOURCE OFFICIELLE : {nom_pro}]\n{doc.page_content}")

            final_context = "\n".join(context_parts)

            # Prompt Strict
            prompt_template = ChatPromptTemplate.from_template("""
            Tu es l'Expert Social Pro 2026.
            
            CONSIGNE CRUCIALE :
            1. Base ta réponse sur les [RÉFÉRENCES LÉGALES ET BARÈMES OFFICIELS].
            2. Quand tu utilises une info, tu DOIS citer explicitement le nom de la source entre crochets.
            3. Exemple : "Selon les [🔢 Barèmes Sociaux Officiels 2026]...".
            
            CONTEXTE :
            {context}
            
            QUESTION :
            {question}
            """)
            
            chain = prompt_template | llm | StrOutputParser()
            full_response = chain.invoke({"context": final_context, "question": query})
            status.update(label="✅ Expertise terminée !", state="complete", expanded=False)

        # Affichage Réponse
        st.markdown(full_response)
        
        # --- FILTRE D'AFFICHAGE DES SOURCES ---
        with st.expander("📚 Sources réellement utilisées"):
            if user_results:
                st.markdown("#### 📂 Votre Document")
                for doc in user_results:
                    st.caption(f"Extrait : *{doc.page_content[:150]}...*")
            
            sources_affichees = set()
            header_displayed = False
            
            if law_results:
                for doc in law_results:
                    nom = nettoyer_nom_source(doc.metadata.get("source", ""))
                    
                    # On affiche SI cité dans la réponse OU SI c'est la jurisprudence (souvent implicite)
                    est_cite = nom in full_response
                    est_jurisprudence = "Jurisprudence" in nom and "jurisprudence" in full_response.lower()
                    
                    if (est_cite or est_jurisprudence) and (nom not in sources_affichees):
                        if not header_displayed:
                            st.markdown("#### 🏛️ Références Officielles Citées")
                            header_displayed = True
                        st.markdown(f"**🔹 {nom}**")
                        st.caption(f"_{doc.page_content[:200]}..._") 
                        sources_affichees.add(nom)
            
            if not header_displayed and not user_results:
                st.caption("Analyse basée sur le contexte juridique général.")

    st.session_state.messages.append({"role": "assistant", "content": full_response})
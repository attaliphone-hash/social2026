import streamlit as st
import google.generativeai as genai
import chromadb
import re

# --- Configuration de la Page ---
st.set_page_config(page_title="Payroll Bot", page_icon="⚖️")
st.title("French Payroll Expert - Assistant IA 🧠")
st.caption("Moteur de Recherche Sémantique (RAG) alimenté par Gemini & ChromaDB")

# --- Gestion de la Clé API ---
if "api_key" not in st.session_state:
    st.session_state.api_key = ""

with st.sidebar:
    st.header("🔐 Configuration")
    api_input = st.text_input("Collez votre clé Google API ici", type="password", value=st.session_state.api_key)
    if api_input:
        st.session_state.api_key = api_input
        genai.configure(api_key=api_input)
    
    st.markdown("---")
    st.info("Ce modèle utilise la **recherche vectorielle**. Il comprend le sens des mots (ex: 'repas' = 'nourriture').")

# Arrêt si pas de clé
if not st.session_state.api_key:
    st.warning("⬅️ Veuillez entrer votre clé API dans la barre latérale pour activer l'intelligence.")
    st.stop()

# --- Cœur du Réacteur : Base Vectorielle ---
@st.cache_resource(show_spinner=False)
def build_vector_db():
    """Lit le fichier, vectorise chaque paragraphe et indexe dans ChromaDB."""
    
    # 1. Initialisation de ChromaDB (Mémoire volatile pour la démo)
    chroma_client = chromadb.Client()
    try:
        chroma_client.delete_collection("payroll_docs") # Nettoyage si existe
    except:
        pass
    collection = chroma_client.create_collection(name="payroll_docs")

    # 2. Lecture du fichier source
    try:
        with open("accidents du travail.txt", "r", encoding="utf-8") as f:
            text = f.read()
    except FileNotFoundError:
        st.error("❌ Fichier 'accidents du travail.txt' introuvable à la racine.")
        return None

    # 3. Découpage intelligent par balise 
    # On sépare le texte à chaque fois qu'on voit "
    metadatas = []
    ids = []
    
    total_parts = len(parts)
    
    # Boucle sur chaque morceau de texte
    for i, part in enumerate(parts):
        if not part.strip(): continue # On saute les vides
        
        try:
            # On récupère l'ID et le texte (ex: " 259] Le texte de loi...")
            if "]" in part:
                source_id, content = part.split("]", 1)
                source_id = source_id.strip()
                content = content.strip()
                
                if len(content) > 10: # On ignore les fragments trop courts
                    # GÉNÉRATION DU VECTEUR (L'étape magique)
                    # On demande à Google : "Transforme ce texte en coordonnées mathématiques"
                    embedding_result = genai.embed_content(
                        model="models/embedding-001",
                        content=content,
                        task_type="retrieval_document",
                        title="Payroll Rule"
                    )
                    
                    documents.append(content)
                    metadatas.append({"source": source_id})
                    ids.append(f"doc_{source_id}")
                    
                    # Ajout dans la base vectorielle
                    collection.add(
                        documents=[content],
                        embeddings=[embedding_result['embedding']],
                        metadatas=[{"source": source_id}],
                        ids=[f"doc_{source_id}"]
                    )
        except Exception as e:
            print(f"Erreur sur le chunk {i}: {e}")
            
        # Mise à jour barre de progression
        my_bar.progress(min((i + 1) / total_parts, 1.0), text=progress_text)

    my_bar.empty() # On cache la barre quand c'est fini
    return collection

# Lancement de l'indexation (se fait une seule fois grâce au cache)
with st.spinner("Chargement du cerveau numérique..."):
    collection = build_vector_db()

if collection:
    st.success("✅ Mémento Social indexé et prêt !")

# --- Interface de Chat ---
if "messages" not in st.session_state:
    st.session_state.messages = [{"role": "assistant", "content": "Bonjour ! Je suis votre expert RH. Posez-moi une question sur les accidents du travail."}]

# Affichage de l'historique
for msg in st.session_state.messages:
    st.chat_message(msg["role"]).write(msg["content"])

# Zone de saisie
if user_query := st.chat_input("Ex: Est-ce que je suis couvert si je me blesse à la cantine ?"):
    
    # 1. Affiche la question utilisateur
    st.session_state.messages.append({"role": "user", "content": user_query})
    st.chat_message("user").write(user_query)

    # 2. Recherche Vectorielle (Retrieval)
    # On transforme la question en vecteur pour trouver les concepts proches
    query_embedding = genai.embed_content(
        model="models/embedding-001",
        content=user_query,
        task_type="retrieval_query"
    )
    
    results = collection.query(
        query_embeddings=[query_embedding['embedding']],
        n_results=4 # On prend les 4 meilleurs paragraphes
    )
    
    # 3. Construction du contexte
    context_text = ""
    for doc, meta in zip(results['documents'][0], results['metadatas'][0]):
        context_text += f"[Source {meta['source']}] : {doc}\n\n"

    # 4. Génération de la réponse (Generation)
    prompt = f"""Tu es un expert juridique Senior en droit social.
    Ta mission est de répondre à la question de l'utilisateur en te basant EXCLUSIVEMENT sur les extraits du Mémento fournis ci-dessous.
    
    Règles :
    1. Sois précis et pédagogue.
    2. Cite systématiquement tes sources entre parenthèses ou crochets (ex: [Source 12]).
    3. Si la réponse n'est pas dans le texte, dis "Je ne trouve pas cette information dans le Mémento". Ne l'invente pas.
    
    CONTEXTE DU MÉMENTO :
    {context_text}
    
    QUESTION UTILISATEUR :
    {user_query}
    """

    # Appel à Gemini Pro
    model = genai.GenerativeModel('gemini-1.5-flash')
    with st.chat_message("assistant"):
        with st.spinner("Analyse juridique en cours..."):
            response = model.generate_content(prompt)
            st.markdown(response.text)
            
            # Sauvegarde historique
            st.session_state.messages.append({"role": "assistant", "content": response.text})
            
            # Bonus : Afficher les sources brutes (Preuve)
            with st.expander("🔍 Voir les extraits juridiques utilisés"):
                st.markdown(context_text)

__import__('pysqlite3')
import sys
sys.modules['sqlite3'] = sys.modules.pop('pysqlite3')

import streamlit as st
import google.generativeai as genai
import chromadb
import os

st.set_page_config(page_title="Expert RH", page_icon="🧠")
st.title("Assistant Paie & RH 🧠")

# --- 1. CONNEXION ---
with st.sidebar:
    st.header("🔐 Connexion")
    api_key = st.text_input("Clé API Google", type="password")
    if api_key:
        genai.configure(api_key=api_key)

if not api_key:
    st.warning("⬅️ Veuillez entrer votre clé API pour démarrer.")
    st.stop()

# --- 2. INTELLIGENCE ---
@st.cache_resource(show_spinner=False)
def charger_cerveau():
    # Préparation de la mémoire
    client = chromadb.Client()
    try:
        client.delete_collection("paie")
    except:
        pass
    collection = client.create_collection("paie")

    # NOM CONFIRMÉ PAR LE DÉTECTIVE
    nom_fichier = "accidents-du-travail.txt"
    
    if not os.path.exists(nom_fichier):
        return None

    # Lecture
    with open(nom_fichier, "r", encoding="utf-8") as f:
        contenu = f.read()

    # Découpage sécurisé (Anti-bug copie)
    partie_a = "["
    partie_b = "source:"
    balise = partie_a + partie_b
    parts = contenu.split(balise)

    docs = []
    ids = []
    
    # Barre de chargement
    barre = st.progress(0, text="Lecture du Mémento...")
    total = len(parts)

    for i, part in enumerate(parts):
        if "]" in part:
            try:
                morceaux = part.split("]", 1)
                ref = morceaux[0]
                texte = morceaux[1].strip()
                
                if len(texte) > 10:
                    docs.append(f"Source {ref}: {texte}")
                    ids.append(f"doc_{i}")
            except:
                pass
        
        if total > 0 and i % 10 == 0:
            barre.progress(min(i / total, 1.0))
    
    barre.empty()

    # Création des vecteurs
    if docs:
        embeddings = []
        for doc in docs:
            try:
                res = genai.embed_content(model="models/embedding-001", content=doc, task_type="retrieval_document")
                embeddings.append(res['embedding'])
            except:
                pass
        
        if len(embeddings) > 0:
            taille_min = min(len(docs), len(embeddings))
            collection.add(
                documents=docs[:taille_min], 
                ids=ids[:taille_min], 
                embeddings=embeddings[:taille_min]
            )
            return collection
            
    return None

# --- 3. DÉMARRAGE ---
with st.spinner("Initialisation du système..."):
    # On force le rechargement si besoin
    db = charger_cerveau()

if not db:
    st.error(f"❌ Erreur : Le fichier 'accidents-du-travail.txt' est illisible ou vide.")
else:
    st.success("✅ Système prêt !")

    # --- 4. CHAT ---
    if "messages" not in st.session_state:
        st.session_state.messages = [{"role": "assistant", "content": "Bonjour ! Je suis votre expert RH."}]

    for msg in st.session_state.messages:
        st.chat_message(msg["role"]).write(msg["content"])

    if question := st.chat_input("Votre question..."):
        st.session_state.messages.append({"role": "user", "content": question})
        st.chat_message("user").write(question)

        try:
            q_vec = genai.embed_content(model="models/embedding-001", content=question, task_type="retrieval_query")
            res = db.query(query_embeddings=[q_vec['embedding']], n_results=3)
            
            if res['documents'] and res['documents'][0]:
                contexte = "\n\n".join(res['documents'][0])
                prompt = f"Expert RH. Contexte : {contexte}. Question : {question}"
                model = genai.GenerativeModel('gemini-1.5-flash')
                reponse = model.generate_content(prompt)
                
                st.chat_message("assistant").write(reponse.text)
                st.session_state.messages.append({"role": "assistant", "content": reponse.text})
            else:
                st.warning("Je n'ai rien trouvé de pertinent dans le document.")
            
        except Exception as e:
            st.error(f"Erreur : {e}")

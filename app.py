__import__('pysqlite3')
import sys
sys.modules['sqlite3'] = sys.modules.pop('pysqlite3')

import streamlit as st
import google.generativeai as genai
import chromadb
import os
import time

st.set_page_config(page_title="Expert RH", page_icon="🧠")
st.title("Assistant Paie & RH 🧠")

# --- 1. CONNEXION ---
with st.sidebar:
    st.header("🔐 Connexion")
    st.info("💡 Le système est bridé pour protéger votre quota gratuit.")
    api_key = st.text_input("Clé API Google", type="password")
    if api_key:
        genai.configure(api_key=api_key)

if not api_key:
    st.warning("⬅️ Veuillez entrer votre clé API.")
    st.stop()

# --- 2. CERVEAU (Version Sécurisée) ---
@st.cache_resource(show_spinner=False)
def charger_cerveau():
    client = chromadb.Client()
    try:
        client.delete_collection("paie")
    except:
        pass
    collection = client.create_collection("paie")

    fichier = "accidents-du-travail.txt"
    
    if not os.path.exists(fichier):
        st.error(f"❌ Fichier '{fichier}' introuvable.")
        return None

    with open(fichier, "r", encoding="utf-8") as f:
        contenu = f.read()

    # Découpage (Chunking)
    taille_bloc = 1000
    chevauchement = 100
    docs = []
    ids = []
    
    for i in range(0, len(contenu), taille_bloc - chevauchement):
        morceau = contenu[i : i + taille_bloc]
        if len(morceau.strip()) > 10:
            docs.append(f"Extrait {i//taille_bloc + 1}: {morceau}")
            ids.append(f"doc_{i}")

    if not docs:
        st.error("❌ Le fichier est vide.")
        return None

    # --- LIMITE DE SÉCURITÉ ---
    # On indexe seulement les 50 premiers blocs pour la démo
    if len(docs) > 50:
        docs = docs[:50]
        ids = ids[:50]
        st.toast("⚠️ Mode Éco : Seuls les 50 premiers extraits sont chargés.", icon="🛡️")

    # --- VECTORISATION LENTE ---
    embeddings = []
    barre = st.progress(0, text="Chargement lent (Anti-blocage)...")
    
    # Test de connexion
    try:
        genai.embed_content(model="models/embedding-001", content="Test", task_type="retrieval_document")
    except Exception as e:
        barre.empty()
        st.error(f"⛔️ ERREUR QUOTA : {e}")
        st.info("Revenez demain après 9h00 ou changez de clé API.")
        return None

    total = len(docs)
    for i, doc in enumerate(docs):
        try:
            res = genai.embed_content(model="models/embedding-001", content=doc, task_type="retrieval_document")
            embeddings.append(res['embedding'])
            
            # PAUSE OBLIGATOIRE (1.5 secondes)
            time.sleep(1.5) 
            
        except Exception as e:
            st.warning(f"Pause forcée (Quota atteint à {i/total:.0%}). On continue avec ce qu'on a.")
            break
        
        if total > 0:
            barre.progress(min((i + 1) / total, 1.0))
    
    barre.empty()
    
    if len(embeddings) > 0:
        taille = len(embeddings)
        collection.add(
            documents=docs[:taille], 
            ids=ids[:taille], 
            embeddings=embeddings[:taille]
        )
        return collection
            
    return None

# --- 3. LANCEMENT ---
with st.spinner("Démarrage..."):
    db = charger_cerveau()

if db:
    st.success("✅ Assistant prêt !")

    if "messages" not in st.session_state:
        st.session_state.messages = [{"role": "assistant", "content": "Bonjour ! Je suis prêt."}]

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
                prompt = f"Expert RH. Utilise ce contexte pour répondre.\nCONTEXTE: {contexte}\nQUESTION: {question}"
                model = genai.GenerativeModel('gemini-1.5-flash')
                reponse = model.generate_content(prompt)
                
                st.chat_message("assistant").write(reponse.text)
                st.session_state.messages.append({"role": "assistant", "content": reponse.text})
            else:
                st.warning("Info non trouvée dans les extraits chargés.")
        except Exception as e:
            st.error(f"Erreur : {e}")

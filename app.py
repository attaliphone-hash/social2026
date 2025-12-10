__import__('pysqlite3')
import sys
sys.modules['sqlite3'] = sys.modules.pop('pysqlite3')

import streamlit as st
import google.generativeai as genai
import chromadb
import os
import time

# --- CONFIGURATION ---
st.set_page_config(page_title="Expert RH", page_icon="🧠")
st.title("Assistant Paie & RH 🧠")
st.caption("Moteur : Gemini 2.5 Flash + Text-Embedding-004")

# --- 1. SÉCURITÉ & CONNEXION ---
with st.sidebar:
    st.header("🔐 Connexion")
    api_key = st.text_input("Clé API Google", type="password")
    if api_key:
        genai.configure(api_key=api_key)

if not api_key:
    st.warning("⬅️ Veuillez entrer votre clé API pour démarrer.")
    st.stop()

# --- 2. FONCTION D'INDEXATION ---
@st.cache_resource(show_spinner=False)
def charger_cerveau():
    # Initialisation DB
    client = chromadb.Client()
    try:
        client.delete_collection("paie")
    except:
        pass
    collection = client.create_collection("paie")

    # Vérification fichier
    fichier = "accidents-du-travail.txt"
    if not os.path.exists(fichier):
        st.error(f"❌ Fichier '{fichier}' introuvable sur le serveur.")
        return None

    # Lecture
    with open(fichier, "r", encoding="utf-8") as f:
        contenu = f.read()

    # Découpage (Chunking)
    taille_bloc = 1000
    chevauchement = 100
    docs = []
    ids = []
    
    # Découpage mathématique
    for i in range(0, len(contenu), taille_bloc - chevauchement):
        morceau = contenu[i : i + taille_bloc]
        if len(morceau.strip()) > 10:
            docs.append(f"Extrait {i//taille_bloc + 1}: {morceau}")
            ids.append(f"doc_{i}")

    if not docs:
        st.error("❌ Le fichier est vide.")
        return None

    # Vectorisation (Nouveau Modèle 2025)
    embeddings = []
    total = len(docs)
    msg = f"Analyse intégrale de {total} extraits avec Gemini 2.5..."
    barre = st.progress(0, text=msg)
    
    # --- CHANGEMENT 1 : Modèle d'embedding à jour ---
    modele_embedding = "models/text-embedding-004" 

    # Test de connexion
    try:
        genai.embed_content(model=modele_embedding, content="Test", task_type="retrieval_document")
    except Exception as e:
        barre.empty()
        st.error(f"⛔️ ERREUR API : {e}")
        return None

    for i, doc in enumerate(docs):
        try:
            res = genai.embed_content(model=modele_embedding, content=doc, task_type="retrieval_document")
            embeddings.append(res['embedding'])
            
            # Pause de sécurité conservée (même si 2.5 est plus rapide, prudence sur le quota)
            time.sleep(1.0) 
            
        except Exception as e:
            st.error(f"Erreur sur l'extrait {i} : {e}")
            break
        
        if total > 0:
            barre.progress(min((i + 1) / total, 1.0))
    
    barre.empty()
    
    # Sauvegarde
    if len(embeddings) > 0:
        taille = len(embeddings)
        collection.add(documents=docs[:taille], ids=ids[:taille], embeddings=embeddings[:taille])
        return collection
            
    return None

# --- 3. DÉMARRAGE ---
with st.spinner("Mise à jour du cerveau vers Gemini 2.5..."):
    db = charger_cerveau()

if db:
    st.success("✅ Assistant opérationnel (Moteur v2.5) !")

    # --- 4. CHAT ---
    if "messages" not in st.session_state:
        st.session_state.messages = [{"role": "assistant", "content": "Bonjour ! Je suis à jour et prêt."}]

    for msg in st.session_state.messages:
        st.chat_message(msg["role"]).write(msg["content"])

    if question := st.chat_input("Votre question..."):
        st.session_state.messages.append({"role": "user", "content": question})
        st.chat_message("user").write(question)

        try:
            # 1. Recherche (Mémoire)
            q_vec = genai.embed_content(model="models/text-embedding-004", content=question, task_type="retrieval_query")
            res = db.query(query_embeddings=[q_vec['embedding']], n_results=4)
            
            if res['documents'] and res['documents'][0]:
                contexte = "\n\n".join(res['documents'][0])
                
                # --- CHANGEMENT 2 : Le modèle de Chat à jour ---
                prompt = f"Tu es un expert RH. Réponds via ce contexte UNIQUEMENT.\nCONTEXTE: {contexte}\nQUESTION: {question}"
                model = genai.GenerativeModel('gemini-2.5-flash') 
                reponse = model.generate_content(prompt)
                
                st.chat_message("assistant").write(reponse.text)
                st.session_state.messages.append({"role": "assistant", "content": reponse.text})
            else:
                st.warning("Information non trouvée dans le document.")
        except Exception as e:
            st.error(f"Erreur : {e}")

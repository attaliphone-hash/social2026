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
st.caption("Version Intégrale - Analyse complète")

# --- 1. CONNEXION ---
with st.sidebar:
    st.header("🔐 Connexion")
    api_key = st.text_input("Clé API Google", type="password")
    if api_key:
        genai.configure(api_key=api_key)

if not api_key:
    st.warning("⬅️ Veuillez entrer votre clé API.")
    st.stop()

# --- 2. CERVEAU (Version ILLIMITÉE) ---
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

    # --- VECTORISATION COMPLÈTE ---
    embeddings = []
    
    # On affiche le nombre total de blocs à traiter
    total = len(docs)
    msg_chargement = f"Lecture intégrale de {total} extraits... (Patience requise)"
    barre = st.progress(0, text=msg_chargement)
    
    # Test de connexion
    try:
        genai.embed_content(model="models/embedding-001", content="Test", task_type="retrieval_document")
    except Exception as e:
        barre.empty()
        st.error(f"⛔️ ERREUR QUOTA : {e}")
        return None

    for i, doc in enumerate(docs):
        try:
            res = genai.embed_content(model="models/embedding-001", content=doc, task_type="retrieval_document")
            embeddings.append(res['embedding'])
            
            # PAUSE TECHNIQUE : Indispensable pour ne pas griller la vitesse autorisée
            # C'est ce qui permet de charger tout le fichier sans planter.
            time.sleep(1.5) 
            
        except Exception as e:
            st.error(f"Erreur sur l'extrait {i} : {e}")
            # En cas d'erreur critique (quota jour atteint), on sauve ce qu'on a déjà fait
            break
        
        # Mise à jour barre
        if total > 0:
            pourcentage = (i + 1) / total
            barre.progress(min(pourcentage, 1.0), text=f"Analyse : {i+1}/{total} extraits traités...")
    
    barre.empty()
    
    # Enregistrement en base
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
with st.spinner("Démarrage du système..."):
    db = charger_cerveau()

if db:
    st.success("✅ Mémento chargé à 100% !")

    if "messages" not in st.session_state:
        st.session_state.messages = [{"role": "assistant", "content": "Bonjour ! Je connais tout le document. Posez votre question."}]

    for msg in st.session_state.messages:
        st.chat_message(msg["role"]).write(msg["content"])

    if question := st.chat_input("Votre question..."):
        st.session_state.messages.append({"role": "user", "content": question})
        st.chat_message("user").write(question)

        try:
            q_vec = genai.embed_content(model="models/embedding-001", content=question, task_type="retrieval_query")
            res = db.query(query_embeddings=[q_vec['embedding']], n_results=4) # On récupère 4 extraits pour être précis
            
            if res['documents'] and res['documents'][0]:
                contexte = "\n\n".join(res['documents'][0])
                prompt = f"Tu es un expert RH. Réponds en te basant UNIQUEMENT sur ce contexte.\nCONTEXTE: {contexte}\nQUESTION: {question}"
                model = genai.GenerativeModel('gemini-1.5-flash')
                reponse = model.generate_content(prompt)
                
                st.chat_message("assistant").write(reponse.text)
                st.session_state.messages.append({"role": "assistant", "content": reponse.text})
            else:
                st.warning("Je n'ai pas trouvé la réponse dans le document.")
        except Exception as e:
            st.error(f"Erreur : {e}")

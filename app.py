__import__('pysqlite3')
import sys
sys.modules['sqlite3'] = sys.modules.pop('pysqlite3')

import streamlit as st
import google.generativeai as genai
import chromadb
import os
import time

# --- CONFIGURATION ---
st.set_page_config(page_title="Agent expert RH", page_icon="")
st.title("Notre spécialiste métier")
st.caption("Base de connaissance centralisée")

# --- 1. SÉCURITÉ & CONNEXION ---
with st.sidebar:
    st.header("🔐 Connexion")
    api_key = st.text_input("Clé API Google", type="password")
    if api_key:
        genai.configure(api_key=api_key)

if not api_key:
    st.warning("⬅️ Veuillez entrer votre clé API pour démarrer.")
    st.stop()

# --- 2. FONCTION D'INDEXATION (MULTI-FICHIERS) ---
@st.cache_resource(show_spinner=False)
def charger_cerveau():
    # Initialisation DB
    client = chromadb.Client()
    try:
        client.delete_collection("paie")
    except:
        pass
    collection = client.create_collection("paie")

    # 1. Repérage de TOUS les fichiers .txt
    tous_les_fichiers = [f for f in os.listdir('.') if f.endswith('.txt') and f != 'requirements.txt']
    
    if not tous_les_fichiers:
        st.error("❌ Aucun fichier '.txt' trouvé à la racine.")
        return None

    docs_globaux = []
    ids_globaux = []
    
    # 2. Boucle sur chaque fichier trouvé
    total_fichiers = len(tous_les_fichiers)
    msg_global = st.empty() # Zone pour afficher quel fichier est en cours
    
    compteur_id = 0
    
    for index_f, fichier in enumerate(tous_les_fichiers):
        msg_global.info(f"📂 Lecture du fichier {index_f+1}/{total_fichiers} : {fichier}...")
        
        with open(fichier, "r", encoding="utf-8") as f:
            contenu = f.read()

        # Découpage (Chunking)
        taille_bloc = 1000
        chevauchement = 100
        
        for i in range(0, len(contenu), taille_bloc - chevauchement):
            morceau = contenu[i : i + taille_bloc]
            if len(morceau.strip()) > 10:
                # Astuce : On ajoute le NOM du fichier dans le texte pour que l'IA sache d'où ça vient
                docs_globaux.append(f"Source [{fichier}] : {morceau}")
                ids_globaux.append(f"doc_{compteur_id}")
                compteur_id += 1

    msg_global.empty()

    if not docs_globaux:
        st.error("❌ Les fichiers semblent vides.")
        return None

    # 3. Vectorisation Globale
    embeddings = []
    total_docs = len(docs_globaux)
    
    # Barre de progression unique pour tout le processus
    barre = st.progress(0, text=f"Apprentissage de {total_docs} extraits (Total)...")
    
    # Test de connexion
    try:
        genai.embed_content(model="models/embedding-001", content="Test", task_type="retrieval_document")
    except Exception as e:
        barre.empty()
        st.error(f"⛔️ ERREUR QUOTA : {e}")
        st.info("Revenez demain matin (Quota journalier épuisé).")
        return None

    for i, doc in enumerate(docs_globaux):
        try:
            res = genai.embed_content(model="models/embedding-001", content=doc, task_type="retrieval_document")
            embeddings.append(res['embedding'])
            
            # PAUSE DE SÉCURITÉ (Toujours indispensable)
            time.sleep(1.5) 
            
        except Exception as e:
            st.error(f"Erreur sur l'extrait {i} : {e}")
            break
        
        if total_docs > 0:
            barre.progress(min((i + 1) / total_docs, 1.0))
    
    barre.empty()
    
    # Sauvegarde finale
    if len(embeddings) > 0:
        taille = len(embeddings)
        collection.add(documents=docs_globaux[:taille], ids=ids_globaux[:taille], embeddings=embeddings[:taille])
        return collection
            
    return None

# --- 3. DÉMARRAGE ---
with st.spinner("Analyse de tous les documents RH... (Patience ☕️)"):
    db = charger_cerveau()

if db:
    st.success("✅ Super-Cerveau opérationnel !")

    # --- 4. CHAT ---
    if "messages" not in st.session_state:
        st.session_state.messages = [{"role": "assistant", "content": "Bonjour ! Je connais tous vos documents. Posez votre question."}]

    for msg in st.session_state.messages:
        st.chat_message(msg["role"]).write(msg["content"])

    if question := st.chat_input("Votre question..."):
        st.session_state.messages.append({"role": "user", "content": question})
        st.chat_message("user").write(question)

        try:
            # Recherche élargie (on prend les 5 meilleurs extraits car il y a plus de matière)
            q_vec = genai.embed_content(model="models/embedding-001", content=question, task_type="retrieval_query")
            res = db.query(query_embeddings=[q_vec['embedding']], n_results=5)
            
            if res['documents'] and res['documents'][0]:
                contexte = "\n\n".join(res['documents'][0])
                prompt = f"Tu es un expert RH Senior. Réponds en te basant UNIQUEMENT sur ce contexte. Cite le nom du fichier source si possible.\nCONTEXTE: {contexte}\nQUESTION: {question}"
                
                model = genai.GenerativeModel('gemini-1.5-flash')
                reponse = model.generate_content(prompt)
                
                st.chat_message("assistant").write(reponse.text)
                st.session_state.messages.append({"role": "assistant", "content": reponse.text})
            else:
                st.warning("Information non trouvée dans les documents fournis.")
        except Exception as e:
            st.error(f"Erreur : {e}")

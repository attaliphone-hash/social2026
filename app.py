import streamlit as st
import sqlite3
import re
import google.generativeai as genai

# Configuration
DB_NAME = "ingestion.db"

# French Stop Words & Configuration (Reused from V2)
STOP_WORDS = {
    "le", "la", "les", "de", "des", "du", "un", "une", "et", "ou", "à", "en", 
    "pour", "par", "sur", "dans", "ce", "cette", "ces", "je", "tu", "il", "elle", 
    "nous", "vous", "ils", "elles", "est", "sont", "a", "ont", "l", "d", "qu", 
    "que", "qui", "aux", "avec", "sans", "sous"
}

# Weighted Keywords Categories (Reused from V2 for Retrieval)
ACTION_KEYWORDS = {"déclarer", "envoyer", "transmettre", "payer", "verser", "licencier", "rompre", "avertir", "remplir", "saisir"}
TIME_KEYWORDS = {"délai", "délais", "temps", "durée", "heure", "heures", "jour", "jours", "mois", "an", "année", "quand", "date"}
DECLARATION_TRIGGER = {"déclarer", "déclaration"}
DECLARATION_BOOST_TERMS = ["48 heures", "net-entreprises", "formulaire", "cerfa"]

def get_connection():
    return sqlite3.connect(DB_NAME)

def get_documents_list():
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT DISTINCT filename FROM documents")
        files = [row[0] for row in cursor.fetchall()]
    except sqlite3.OperationalError:
        files = []
    conn.close()
    return files

def clean_and_tokenize(text):
    text = re.sub(r'[^\w\s]', ' ', text.lower())
    tokens = text.split()
    return [t for t in tokens if t not in STOP_WORDS and len(t) > 1]

def calculate_score_v2(query_tokens, chunk_text, original_query):
    # Reuse V2 Scoring logic for good retrieval
    chunk_tokens = set(clean_and_tokenize(chunk_text))
    score = 0
    
    for token in query_tokens:
        if token in chunk_tokens:
            if token in ACTION_KEYWORDS:
                score += 5
            elif token in TIME_KEYWORDS:
                score += 3
            else:
                score += 1
            
    if any(trigger in original_query.lower() for trigger in DECLARATION_TRIGGER):
        for term in DECLARATION_BOOST_TERMS:
            if term in chunk_text.lower():
                score += 50
                break 

    return score

def search_documents(query, limit=3):
    """Retrieve top N chunks."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT filename, text FROM documents")
    all_chunks = cursor.fetchall()
    conn.close()
    
    query_tokens = clean_and_tokenize(query)
    if not query_tokens:
        return []

    scored_results = []
    for filename, text in all_chunks:
        score = calculate_score_v2(query_tokens, text, query)
        if score > 0:
            scored_results.append((score, filename, text))
            
    scored_results.sort(key=lambda x: x[0], reverse=True)
    return scored_results[:limit]

def main():
    st.set_page_config(page_title="Payroll Bot", page_icon="🤖")
    st.title("French Payroll Expert - Assistant IA")
    st.subheader("Votre assistant conformité basé sur le Mémento Social 2023.")
    
    # Sidebar
    st.sidebar.header("Configuration")
    
    # Authentification
    access_password = st.sidebar.text_input("Mot de passe d'accès", type="password")
    if access_password != "socialpro2026":
        st.sidebar.warning("Accès Restreint 🔒")
        st.stop()
        
    api_key = st.sidebar.text_input("Collez votre clé Google API ici", type="password")
    
    selected_model_name = "gemini-pro" # Default
    
    if api_key:
        try:
            genai.configure(api_key=api_key)
            # Fetch available models
            model_list = []
            for m in genai.list_models():
                if 'generateContent' in m.supported_generation_methods:
                    model_list.append(m.name)
            
            if model_list:
                selected_model_name = st.sidebar.selectbox("Choisir le modèle", model_list, index=0)
            else:
                st.sidebar.error("Aucun modèle compatible trouvé pour cette clé.")
        except Exception as e:
            st.sidebar.error(f"Erreur API Key : {e}")
            
        if st.sidebar.button("Tester la connexion"):
            try:
                model_test = genai.GenerativeModel(selected_model_name)
                with st.spinner(f"Test de connexion avec {selected_model_name}..."):
                    response_test = model_test.generate_content("Coucou via API Test")
                st.sidebar.success(f"Connexion OK ! Réponse : {response_test.text}")
            except Exception as e:
                st.sidebar.error(f"Échec connexion : {e}")

    st.sidebar.header("Documents Indexés")
    docs = get_documents_list()
    if docs:
        for doc in docs:
            st.sidebar.text(f"📄 {doc}")
    else:
        st.sidebar.warning("Aucun document trouvé.")

    # Chat Interface
    if "messages" not in st.session_state:
        st.session_state.messages = []

    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    if prompt := st.chat_input("Posez votre question..."):
        st.chat_message("user").markdown(prompt)
        st.session_state.messages.append({"role": "user", "content": prompt})
        
        if not api_key:
            response = "🚫 **Veuillez entrer une clé API Google dans la barre latérale pour activer l'intelligence.**"
            st.chat_message("assistant").markdown(response)
            st.session_state.messages.append({"role": "assistant", "content": response})
            return

        with st.chat_message("assistant"):
            try:
                genai.configure(api_key=api_key)
                # print("DEBUG: Clé API reçue") # Removed to reduce noise or keep if user wants
                model = genai.GenerativeModel(selected_model_name)
                # print(f"DEBUG: Modèle utilisé : {selected_model_name}")
                
                with st.spinner("Recherche d'informations et analyse..."):
                    # 1. Retrieval
                    results = search_documents(prompt, limit=3)
                    print("DEBUG: Recherche en base terminée")
                    
                    if not results:
                        response = "Je n'ai pas trouvé d'information pertinente dans les documents pour répondre à cette question."
                    else:
                        # 2. Augmented Generation
                        context_text = ""
                        for idx, (score, fname, text) in enumerate(results):
                            context_text += f"Extrait {idx+1} (Source: {fname}):\n{text}\n\n"
                            
                        rag_prompt = f"""Tu es un expert RH. Voici des extraits du Mémento Social :
{context_text}

Réponds à la question : '{prompt}' en utilisant ces extraits.
Sois clair, pédagogique et cite la source entre parenthèses lorsque tu utilises une information.
Si les extraits ne contiennent pas la réponse, dis-le honnêtement.
"""
                        # Call Gemini
                        print("DEBUG: Envoi à Gemini...")
                        try:
                            ai_response = model.generate_content(rag_prompt)
                            response = ai_response.text
                        except Exception as e_gemini:
                            raise Exception(f"Erreur lors de l'appel Gemini : {e_gemini}")
                        
                st.markdown(response)
                st.session_state.messages.append({"role": "assistant", "content": response})
                
            except Exception as e:
                error_msg = f"❌ Erreur technique : {e}"
                st.error(error_msg)
                print(f"DEBUG ERROR: {e}")

if __name__ == "__main__":
    main()

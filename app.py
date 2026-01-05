import streamlit as st
import os
import google.generativeai as genai
from pypdf import PdfReader

# --- 1. CONFIGURATION DE LA PAGE ---
st.set_page_config(
    page_title="Expert Social Pro 2026",
    page_icon="⚖️",
    layout="centered"
)

# --- 2. SÉCURITÉ & API ---
# On récupère la clé depuis les variables d'environnement (définies dans Google Cloud Run ou .env)
api_key = os.environ.get("GOOGLE_API_KEY")

if not api_key:
    st.error("⚠️ Clé API introuvable. Assurez-vous d'avoir défini GOOGLE_API_KEY dans les variables d'environnement.")
    st.stop()

# Configuration du modèle
genai.configure(api_key=api_key)

# Définition du modèle spécifique demandé
MODEL_NAME = "gemini-2.0-flash-exp"

# --- 3. BASE DE CONNAISSANCES (MEMO_CHIFFRES) ---
# Données de référence intégrées (PPV 2026, SMIC, Plafonds...)
MEMO_CHIFFRES = """
RÈGLES ET CHIFFRES CLÉS 2026 - SOCIAL FRANCE

1. PRIME DE PARTAGE DE LA VALEUR (PPV) 2024-2026
- Plafond d'exonération : 3 000 € (cas général) ou 6 000 € (si accord d'intéressement/participation).
- Régime Social/Fiscal (Distinction seuil 3 SMIC) :
  * Salaire < 3 SMIC : Exonération totale (Cotisations, CSG/CRDS, Taxe salaires, Impôt revenu).
  * Salaire >= 3 SMIC : Exonération cotisations sociales uniquement. Assujettissement CSG/CRDS et Impôt sur le revenu (sauf si affectation plan épargne).
- Forfait Social :
  * < 250 salariés : Exonéré.
  * >= 250 salariés : 20%.

2. CHIFFRES CLÉS (Estimations/Provisoires pour contexte 2026)
- SMIC Horaire (référence) : ~11,65 € (valeur indicative, vérifier arrêté).
- Plafond Sécurité Sociale (PASS) : Référence 2025 ~47 100 € (à ajuster selon publication officielle).

INSTRUCTION : Tu es un Expert Social. Tu dois toujours citer tes sources (Code du travail, BOSS, URSSAF) quand tu réponds.
Si l'utilisateur pose une question sur un document fourni, base-toi PRIORITAIREMENT sur ce document.
"""

# --- 4. GESTION DE LA SESSION (MÉMOIRE) ---
if "messages" not in st.session_state:
    st.session_state.messages = []

if "context_analyzed" not in st.session_state:
    st.session_state.context_analyzed = ""

if "last_uploaded_file" not in st.session_state:
    st.session_state.last_uploaded_file = None

# --- 5. FONCTIONS UTILES ---
def get_gemini_response(user_input, document_content=""):
    """Envoie le contexte et la question à Gemini"""
    try:
        model = genai.GenerativeModel(MODEL_NAME)
        
        # Construction du prompt système dynamique
        system_prompt = f"""
        {MEMO_CHIFFRES}
        
        [CONTEXTE SUPPLÉMENTAIRE - DOCUMENT UTILISATEUR]
        {document_content if document_content else "Aucun document fourni."}
        
        [HISTORIQUE DE LA CONVERSATION]
        Prends en compte les échanges précédents si nécessaire.
        """
        
        # On combine l'historique pour le chat (simplifié ici pour l'exemple)
        # Idéalement, on envoie l'historique structuré à l'API, 
        # mais ici on concatène pour s'assurer que le document est bien pris en compte à chaque tour.
        full_prompt = f"{system_prompt}\n\nQuestion utilisateur : {user_input}"
        
        response = model.generate_content(full_prompt)
        return response.text
    except Exception as e:
        return f"Une erreur technique est survenue avec le modèle IA : {e}"

# --- 6. INTERFACE UTILISATEUR ---

# Titre principal
st.title("Bienvenue sur votre expert social dédié.")

# BLOC INFORMATION ET ACTIONS (Le fameux cadre bleu/gris)
with st.container(border=True):
    
    # Ligne d'info Année Fiscale
    col_ico, col_txt = st.columns([0.5, 5])
    with col_ico:
        st.write("📅")
    with col_txt:
        st.write("**Année Fiscale : 2026**")
        st.caption("Base à jour.")

    st.write("") # Espaceur

    # ACTION 1 : Nouvelle conversation (Remplace la corbeille)
    if st.button("Nouvelle conversation", use_container_width=True):
        st.session_state.messages = []
        st.session_state.context_analyzed = ""
        st.session_state.last_uploaded_file = None
        st.rerun()

    # ACTION 2 : Upload de document (Analyse pypdf)
    uploaded_file = st.file_uploader(
        "Télécharger un document pour analyse", 
        type=['pdf', 'txt'],
        label_visibility="collapsed"
    )

    # Traitement du fichier uploadé
    if uploaded_file is not None:
        # On ne retraite que si c'est un nouveau fichier
        if st.session_state.last_uploaded_file != uploaded_file.name:
            with st.spinner("Analyse du document en cours..."):
                text_extracted = ""
                try:
                    if uploaded_file.type == "application/pdf":
                        reader = PdfReader(uploaded_file)
                        for page in reader.pages:
                            text_extracted += (page.extract_text() or "") + "\n"
                    else: # TXT
                        text_extracted = uploaded_file.getvalue().decode("utf-8")
                    
                    st.session_state.context_analyzed = text_extracted
                    st.session_state.last_uploaded_file = uploaded_file.name
                    st.toast(f"Document '{uploaded_file.name}' mémorisé !", icon="✅")
                except Exception as e:
                    st.error(f"Erreur lors de la lecture du fichier : {e}")

# Affichage si un document est actif
if st.session_state.context_analyzed:
    st.info(f"📂 Document actif : {st.session_state.last_uploaded_file}", icon="ℹ️")

# --- 7. ZONE DE CHAT ---
# Affichage de l'historique
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Zone de saisie
if prompt := st.chat_input("Posez votre question sociale..."):
    # 1. Afficher le message utilisateur
    with st.chat_message("user"):
        st.markdown(prompt)
    st.session_state.messages.append({"role": "user", "content": prompt})

    # 2. Générer la réponse
    with st.chat_message("assistant"):
        with st.spinner("Recherche dans les textes officiels..."):
            response_text = get_gemini_response(prompt, st.session_state.context_analyzed)
            st.markdown(response_text)
    
    st.session_state.messages.append({"role": "assistant", "content": response_text})
import streamlit as st
import os

st.set_page_config(page_title="Détective", page_icon="🕵️")
st.title("🕵️ Mode Détective de Fichiers")

st.write("Je scanne le disque dur du serveur...")

# 1. Lister la racine (là où est app.py)
fichiers_racine = os.listdir('.')
st.subheader("📂 Fichiers à la racine :")
st.code(fichiers_racine)

# 2. Lister le dossier 'documents' (s'il existe)
if "documents" in fichiers_racine:
    st.subheader("📂 Fichiers dans le dossier 'documents' :")
    try:
        fichiers_doc = os.listdir('documents')
        st.code(fichiers_doc)
    except Exception as e:
        st.error(f"Erreur d'accès au dossier : {e}")
else:
    st.info("Pas de dossier 'documents' trouvé à la racine.")

st.write("---")
st.write("Copiez le nom EXACT que vous voyez dans la liste ci-dessus.")

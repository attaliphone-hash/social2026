__import__('pysqlite3')
import sys
sys.modules['sqlite3'] = sys.modules.pop('pysqlite3')

import streamlit as st
import os

st.set_page_config(page_title="Test Diagnostic", page_icon="🛠️")

st.title("🛠️ Mode Diagnostic")
st.write("Démarrage de l'application...")

# 1. TEST DES BIBLIOTHEQUES
try:
    import google.generativeai as genai
    import chromadb
    st.success("✅ Étape 1 : Les librairies (ChromaDB & Google) sont bien installées.")
except Exception as e:
    st.error(f"❌ Étape 1 ÉCHEC : Une librairie manque. Vérifiez requirements.txt. Erreur : {e}")
    st.stop()

# 2. TEST DU FICHIER
st.write("---")
st.write("Recherche du fichier texte...")

fichiers_possibles = ["accidents du travail.txt", "documents/accidents du travail.txt"]
fichier_trouve = None

# On liste ce qu'il y a sur le serveur pour voir
st.info(f"Fichiers présents à la racine : {os.listdir('.')}")

for f in fichiers_possibles:
    if os.path.exists(f):
        fichier_trouve = f
        st.success(f"✅ Étape 2 : Fichier trouvé : '{f}'")
        break

if not fichier_trouve:
    st.error("❌ Étape 2 ÉCHEC : Le fichier 'accidents du travail.txt' est introuvable.")
    st.stop()

# 3. TEST DE LECTURE ET DECOUPAGE
try:
    with open(fichier_trouve, "r", encoding="utf-8") as f:
        contenu = f.read()
    st.write(f"Taille du fichier : {len(contenu)} caractères.")
    
    # Test découpage avec le code ASCII pour éviter le bug de copier-coller
    balise = chr(91) + "source:" 
    parts = contenu.split(balise)
    
    st.write(f"Nombre de paragraphes détectés : {len(parts)}")
    
    if len(parts) < 2:
        st.warning("⚠️ Attention : Le fichier est lu mais aucune balise '

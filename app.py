__import__('pysqlite3')
import sys
sys.modules['sqlite3'] = sys.modules.pop('pysqlite3')

import streamlit as st
import google.generativeai as genai
import chromadb
import os

st.set_page_config(page_title="Mode Diagnostic", page_icon="🔧")
st.title("🔧 Mode Diagnostic & Réparation")

# 1. Vérification des fichiers présents
st.header("1. Vérification des fichiers")
fichiers_presents = os.listdir('.')
st.write("📂 Fichiers trouvés sur le serveur :", fichiers_presents)

nom_fichier_attendu = "accidents du travail.txt"

if nom_fichier_attendu in fichiers_presents:
    st.success(f"✅ Le fichier '{nom_fichier_attendu}' est bien là !")
    fichier_a_lire = nom_fichier_attendu
else:
    st.error(f"❌ Le fichier '{nom_fichier_attendu}' est ABSENT.")
    # On cherche si un fichier ressemble (casse différente)
    candidat = None
    for f in fichiers_presents:
        if f.lower() == nom_fichier_attendu.lower():
            candidat = f
    
    if candidat:
        st.warning(f"⚠️ J'ai trouvé '{candidat}'. Le nom exact est important (Majuscules/Minuscules) !")
        fichier_a_lire = candidat
    else:
        st.stop()

# 2. Test de lecture
st.header("2. Lecture du contenu")
try:
    with open(fichier_a_lire, "r", encoding="utf-8") as f:
        contenu = f.read()
    st.info(f"Taille du fichier : {len(contenu)} caractères.")
    st.text_area("Aperçu du début du fichier (100 premiers caractères) :", contenu[:200])
except Exception as e:
    st.error(f"Erreur de lecture : {e}")
    st.stop()

# 3. Test de découpage
st.header("3. Test de découpage (Balises)")
balise = "

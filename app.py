import streamlit as st
import os

st.set_page_config(page_title="Inspecteur", page_icon="🕵️‍♂️")
st.title("Inspecteur de Fichier 🕵️‍♂️")

# Nom du fichier à tester
nom_fichier = "accidents-du-travail.txt"

st.write(f"Je cherche le fichier : **{nom_fichier}**")

# 1. Vérifier s'il existe
if os.path.exists(nom_fichier):
    st.success(f"✅ Fichier trouvé !")
    
    # 2. Vérifier son poids (Taille)
    taille = os.path.getsize(nom_fichier)
    st.metric(label="Poids du fichier", value=f"{taille} octets")
    
    if taille == 0:
        st.error("⛔️ ALERTE : Le fichier pèse 0 octet. Il est VIDE.")
    else:
        # 3. Essayer de lire le début
        try:
            with open(nom_fichier, "r", encoding="utf-8") as f:
                contenu = f.read()
            
            st.info("Voici ce que je lis à l'intérieur (500 premiers caractères) :")
            st.code(contenu[:500])
            
            st.write("---")
            if len(contenu) < 50:
                 st.warning("⚠️ C'est très court... Êtes-vous sûr d'avoir collé tout le texte ?")
            else:
                 st.balloons()
                 st.success("Le contenu semble OK ! Le problème venait du code d'IA.")

        except Exception as e:
            st.error(f"❌ Impossible de lire le texte (Problème d'encodage ?) : {e}")

else:
    st.error("❌ Fichier introuvable.")
    st.write("Voici ce que je vois sur le disque :")
    st.write(os.listdir('.'))

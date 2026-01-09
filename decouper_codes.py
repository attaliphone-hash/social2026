import os

def chunk_file(file_path, output_folder, chunk_size=3000):
    """Découpe un fichier lourd en morceaux digestibles par l'IA."""
    if not os.path.exists(file_path):
        print(f"❌ Erreur : {file_path} introuvable.")
        return

    print(f"⏳ Lecture de {file_path}...")
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    base_name = os.path.basename(file_path).replace('.txt', '')
    # On découpe par blocs de 3000 caractères
    chunks = [content[i:i+chunk_size] for i in range(0, len(content), chunk_size)]

    print(f"⚙️ Création de {len(chunks)} morceaux pour {base_name}...")
    for i, chunk in enumerate(chunks):
        # Format du nom : LEGAL_Code_du_Travail_001.txt
        chunk_filename = f"LEGAL_{base_name}_{i+1:03d}.txt"
        with open(os.path.join(output_folder, chunk_filename), 'w', encoding='utf-8') as f:
            f.write(f"SOURCE : {base_name} (Partie {i+1})\n\n{chunk}")
    
    print(f"✅ Terminé pour {base_name} !")

# --- EXÉCUTION ---
os.makedirs("data_clean", exist_ok=True)

# Lancement pour les deux codes
chunk_file("archives/Code_du_Travail.txt", "data_clean")
chunk_file("archives/Code_Securite_Sociale.txt", "data_clean")
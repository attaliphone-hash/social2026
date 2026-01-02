# 1. Image de base légère
FROM python:3.10-slim

# 2. Dossier de travail
WORKDIR /app

# 3. Installation des dépendances système (sqlite3 et curl pour le téléchargement)
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# 4. Préparation du dossier pour la base de données
RUN mkdir -p /app/chroma_db

# 5. Téléchargement du Golden Index (Base SQLite)
# ATTENTION : Si le fichier fait moins de 100 Mo dans les logs, vérifiez l'accès public du Bucket.
RUN curl -L -o /app/chroma_db/chroma.sqlite3 "https://storage.googleapis.com/social2026-data/chroma.sqlite3"

# 6. Copie des fichiers de configuration
COPY requirements.txt .

# 7. Installation des bibliothèques Python
RUN pip install --no-cache-dir -r requirements.txt

# 8. Copie du code source (app.py)
COPY app.py .

# 9. Exposition du port Streamlit
EXPOSE 8080

# 10. Lancement de l'application
CMD ["streamlit", "run", "app.py", "--server.port=8080", "--server.address=0.0.0.0"]
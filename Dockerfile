FROM python:3.10-slim

WORKDIR /app

# Installation des outils de base (curl est nécessaire pour télécharger la base)
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# 1. Création du dossier de destination
RUN mkdir -p chroma_db

# 2. Téléchargement de la base de données depuis votre Bucket Google Storage
# Cette étape remplace l'envoi manuel par Git
RUN curl -L -o ./chroma_db/chroma.sqlite3 "https://storage.googleapis.com/social2026-data/chroma.sqlite3"

COPY requirements.txt .

# Installation des dépendances (incluant LangChain maintenant que Git est débloqué)
RUN pip3 install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8080

ENTRYPOINT ["streamlit", "run", "app.py", "--server.port=8080", "--server.address=0.0.0.0"]
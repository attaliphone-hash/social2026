FROM python:3.10-slim
WORKDIR /app

# Outils système
RUN apt-get update && apt-get install -y build-essential curl && rm -rf /var/lib/apt/lists/*

# Création du dossier et téléchargement de la base (Golden Index)
RUN mkdir -p chroma_db
RUN curl -L -o ./chroma_db/chroma.sqlite3 "https://storage.googleapis.com/social2026-data/chroma.sqlite3"

# Installation des dépendances
# On utilise pip3 pour être plus précis sur Debian
COPY requirements.txt .
RUN pip3 install --no-cache-dir -U pip
RUN pip3 install --no-cache-dir -r requirements.txt

# Copie du reste du code (app.py)
COPY . .

EXPOSE 8080
ENTRYPOINT ["streamlit", "run", "app.py", "--server.port=8080", "--server.address=0.0.0.0"]
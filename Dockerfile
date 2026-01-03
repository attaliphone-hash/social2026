# 1. Image de base légère
FROM python:3.10-slim

# 2. Dossier de travail
WORKDIR /app

# 3. Installation des dépendances système (indispensable pour curl)
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# 4. Préparation du dossier pour la base de données
RUN mkdir -p /app/chroma_db

# 5. Téléchargement du Golden Index (VOTRE TRÉSOR)
RUN curl -L -o /app/chroma_db/chroma.sqlite3 "https://storage.googleapis.com/social2026-data/chroma.sqlite3"

# 6. Copie des requirements
COPY requirements.txt .

# 7. Installation des bibliothèques Python
RUN pip install --no-cache-dir -r requirements.txt

# --- C'EST ICI QUE C'ETAIT BLOQUANT ---
# 8. Copie de TOUT le code (app.py ET les images .png)
COPY . .
# --------------------------------------

# 9. Exposition du port Streamlit
EXPOSE 8080

# 10. Lancement de l'application
CMD ["streamlit", "run", "app.py", "--server.port=8080", "--server.address=0.0.0.0"]
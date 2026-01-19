# Dockerfile - Version Nettoyée & Optimisée

# Utilisation d'une image Python légère et récente
FROM python:3.10-slim

# Configuration des variables d'environnement pour Python
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Répertoire de travail
WORKDIR /app

# Installation des dépendances système nécessaires (si besoin pour certaines libs)
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copie des fichiers de dépendances
COPY requirements.txt .

# Installation des dépendances Python
RUN pip install --no-cache-dir -r requirements.txt

# Copie du reste du code de l'application
COPY . .

# Exposition du port standard Cloud Run
EXPOSE 8080

# Commande de démarrage avec healthcheck natif de Streamlit
CMD ["streamlit", "run", "app.py", "--server.port=8080", "--server.address=0.0.0.0"]
FROM python:3.10-slim
WORKDIR /app

RUN apt-get update && apt-get install -y build-essential curl && rm -rf /var/lib/apt/lists/*

# Force l'installation des modules critiques AVANT le reste
RUN pip install --no-cache-dir langchain==0.3.7 langchain-community==0.3.7 langchain-core==0.3.15 langchain-google-genai langchain-chroma

# Téléchargement de la base
RUN mkdir -p chroma_db
RUN curl -L -o ./chroma_db/chroma.sqlite3 "https://storage.googleapis.com/social2026-data/chroma.sqlite3"

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .
EXPOSE 8080
ENTRYPOINT ["streamlit", "run", "app.py", "--server.port=8080", "--server.address=0.0.0.0"]
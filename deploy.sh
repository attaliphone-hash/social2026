#!/bin/bash

# 1. Activation de l'environnement virtuel
source venv/bin/activate

# 2. Déploiement vers Google Cloud Run
gcloud run deploy socialpro2026 \
  --source . \
  --region europe-west1 \
  --memory 2Gi \
  --cpu 1 \
  --min-instances 1 \
  --max-instances 10 \
  --set-env-vars GOOGLE_API_KEY="AIzaSyDUCD43hX3QXgGv92gExuJXbUcEo1RzsMA",STRIPE_SECRET_KEY="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",ADMIN_PASSWORD="0145781261_,Aa@",APP_PASSWORD="SocialPro2026SeptHuit"
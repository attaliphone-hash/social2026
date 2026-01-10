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
  --set-env-vars GOOGLE_API_KEY="AIzaSyAli01QSJSBnfF8-FqI80L5JkBNYJvzsqw",STRIPE_SECRET_KEY="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",ADMIN_PASSWORD="0145781261Aa@",APP_PASSWORD="SocialPro2026SeptHuit"
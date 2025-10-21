#!/usr/bin/env bash
# Google Cloud Run quick deploy (requires gcloud + a GCP project)
# Usage:
#   1) unzip subtitle-mvp-omakase-v7.zip
#   2) copy this deploy pack into the project root (same folder as requirements.txt)
#   3) run: bash cloudrun_deploy.sh your-gcp-project your-service-name

set -euo pipefail

PROJECT=${1:-}
SERVICE=${2:-subtitle-mvp}
REGION=${REGION:-asia-northeast1}

if [ -z "$PROJECT" ]; then
  echo "Usage: bash cloudrun_deploy.sh <GCP_PROJECT_ID> [SERVICE_NAME]"
  exit 1
fi

gcloud config set project "$PROJECT"
gcloud builds submit --tag "gcr.io/$PROJECT/subtitle-mvp:v7"

gcloud run deploy "$SERVICE" \
  --image "gcr.io/$PROJECT/subtitle-mvp:v7" \
  --region "$REGION" \
  --platform managed \
  --allow-unauthenticated \
  --set-env-vars OPENAI_API_KEY=$OPENAI_API_KEY,CORS_ORIGINS="*",ASR_MODEL=whisper-1,CROSSFADE_SEC=0.2 \
  --port 8000

echo "Done. Visit the URL shown above. Check /diag and /config"
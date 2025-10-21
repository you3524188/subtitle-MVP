# Deployable Docker image for Subtitle MVP (FastAPI + ffmpeg)
FROM python:3.11-slim

# Install system deps (ffmpeg, curl)
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg curl \
 && rm -rf /var/lib/apt/lists/*

# Workdir
WORKDIR /app

# Copy app (expecting project ZIP contents mounted/copied here)
# Users should unzip subtitle-mvp-omakase-v7.zip and copy its content here.
COPY . /app

# Install Python deps
# If requirements.txt does not exist, comment the next line or update path accordingly.
RUN pip install --no-cache-dir -r requirements.txt

# Env (can be overridden by platform)
ENV PORT=8000 \
    HOST=0.0.0.0 \
    CORS_ORIGINS=* \
    ASR_MODEL=whisper-1 \
    CROSSFADE_SEC=0.2

# Expose port
EXPOSE 8000

# Start
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
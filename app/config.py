"""
Configuration module for subtitle-mvp
"""
import os

# ASR Model
MODEL_NAME = os.getenv("ASR_MODEL", "whisper-1")

# File upload limits
MAX_SIZE_MB = int(os.getenv("MAX_SIZE_MB", "25"))
ALLOWED_EXTS = {".mp4", ".mp3", ".wav", ".m4a", ".webm", ".avi", ".mov"}

# CORS
CORS_ORIGINS = os.getenv("CORS_ORIGINS", "*").split(",") if os.getenv("CORS_ORIGINS") else ["*"]

# Crossfade
CROSSFADE_SEC = float(os.getenv("CROSSFADE_SEC", "0.2"))

# Profile directory
PROFILE_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "profiles")


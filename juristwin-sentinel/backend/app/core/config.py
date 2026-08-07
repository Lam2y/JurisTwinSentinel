from functools import lru_cache
from pathlib import Path
import os

BASE_DIR = Path(__file__).resolve().parents[2]

class Settings:
    APP_NAME = "JurisTwin Sentinel"
    API_PREFIX = "/api"
    SECRET_KEY = os.getenv("SECRET_KEY", "juristwin-finals-local-secret-change-me")
    ACCESS_TOKEN_MINUTES = int(os.getenv("ACCESS_TOKEN_MINUTES", "480"))
    DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite:///{BASE_DIR / 'juristwin.db'}")
    CORS_ORIGINS = os.getenv("CORS_ORIGINS", "http://127.0.0.1:5173,http://localhost:5173").split(",")
    DEMO_PASSWORD = os.getenv("DEMO_PASSWORD", "Finals2026!")
    VECTOR_BACKEND = os.getenv("VECTOR_BACKEND", "local")

@lru_cache
def get_settings():
    return Settings()

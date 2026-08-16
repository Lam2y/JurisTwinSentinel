from functools import lru_cache
from pathlib import Path
import os
import secrets
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parents[2]
ROOT_DIR = BASE_DIR.parent
load_dotenv(ROOT_DIR / ".env", override=False)


def _secret(name: str) -> tuple[str, bool]:
    value = os.getenv(name)
    if value:
        return value, False
    # Clean-clone tests remain self-contained without shipping static secrets. Finals setup creates
    # .env, while an unconfigured development process receives an ephemeral per-process secret.
    return secrets.token_urlsafe(48), True


_SECRET_KEY, _secret_ephemeral = _secret("SECRET_KEY")
_WEBHOOK_SECRET, _webhook_ephemeral = _secret("WEBHOOK_SECRET")
_PROOF_SIGNING_SECRET, _proof_ephemeral = _secret("PROOF_SIGNING_SECRET")


class Settings:
    APP_NAME = "JurisTwin Sentinel"
    API_PREFIX = "/api"
    SECRET_KEY = _SECRET_KEY
    ACCESS_TOKEN_MINUTES = int(os.getenv("ACCESS_TOKEN_MINUTES", "480"))
    DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite:///{BASE_DIR / 'juristwin.db'}")
    CORS_ORIGINS = os.getenv("CORS_ORIGINS", "http://127.0.0.1:5173,http://localhost:5173,http://127.0.0.1:8000,http://localhost:8000").split(",")
    DEMO_PASSWORD = os.getenv("DEMO_PASSWORD", "Finals2026!")
    VECTOR_BACKEND = os.getenv("VECTOR_BACKEND", "local")
    WEBHOOK_SECRET = _WEBHOOK_SECRET
    PROOF_SIGNING_SECRET = _PROOF_SIGNING_SECRET
    SECURITY_SECRET_MODE = "ephemeral-dev" if any((_secret_ephemeral, _webhook_ephemeral, _proof_ephemeral)) else "local-env"


@lru_cache
def get_settings():
    return Settings()

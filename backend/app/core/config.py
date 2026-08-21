from functools import lru_cache
from pathlib import Path
import os
import secrets
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parents[2]
ROOT_DIR = BASE_DIR.parent
load_dotenv(ROOT_DIR / ".env", override=False)

_SECRET_FILES = {
    "SECRET_KEY": ".juristwin_local_secret",
    "EXPORT_ENCRYPTION_KEY": ".juristwin_export_secret",
    "INTEGRATION_API_KEY": ".juristwin_integration_key",
}


def _secret(name: str) -> tuple[str, str]:
    """Return a stable local secret without hardcoding production credentials.

    Priority: environment/.env -> locally generated ignored file -> process-only fallback.
    Production deployments should inject all secrets through a secret manager.
    """
    value = os.getenv(name)
    if value:
        return value, "environment"

    secret_path = ROOT_DIR / _SECRET_FILES.get(name, f".juristwin_{name.lower()}_secret")
    try:
        if secret_path.exists():
            value = secret_path.read_text(encoding="utf-8").strip()
            if len(value) >= 32:
                return value, "local-generated"
        value = secrets.token_urlsafe(48)
        secret_path.write_text(value, encoding="utf-8")
        try:
            os.chmod(secret_path, 0o600)
        except OSError:
            pass
        return value, "local-generated"
    except OSError:
        return secrets.token_urlsafe(48), "ephemeral-fallback"


_SECRET_KEY, _secret_mode = _secret("SECRET_KEY")
_EXPORT_KEY, _export_key_mode = _secret("EXPORT_ENCRYPTION_KEY")
_INTEGRATION_API_KEY, _integration_key_mode = _secret("INTEGRATION_API_KEY")


class Settings:
    APP_NAME = "JurisTwin Sentinel"
    API_PREFIX = "/api"
    VERSION = "11.0.0-mastery-ui"
    SECRET_KEY = _SECRET_KEY
    SECRET_MODE = _secret_mode
    EXPORT_ENCRYPTION_KEY = _EXPORT_KEY
    EXPORT_KEY_MODE = _export_key_mode
    INTEGRATION_API_KEY = _INTEGRATION_API_KEY
    INTEGRATION_KEY_MODE = _integration_key_mode
    ENVIRONMENT = os.getenv("ENVIRONMENT", "demo").lower()
    REQUIRE_HTTPS = os.getenv("REQUIRE_HTTPS", "false").lower() in {"1", "true", "yes"}
    ACCESS_TOKEN_MINUTES = int(os.getenv("ACCESS_TOKEN_MINUTES", "240"))
    DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite:///{BASE_DIR / 'juristwin_mastery.db'}")
    DEMO_PASSWORD = os.getenv("DEMO_PASSWORD", "Finals2026!")
    DEMO_MODE = os.getenv("DEMO_MODE", "true").lower() in {"1", "true", "yes"}
    CORS_ORIGINS = [x.strip() for x in os.getenv(
        "CORS_ORIGINS",
        "http://127.0.0.1:8000,http://localhost:8000,http://127.0.0.1:5173,http://localhost:5173",
    ).split(",") if x.strip()]
    DOMAIN_CONFIDENCE_THRESHOLD = float(os.getenv("DOMAIN_CONFIDENCE_THRESHOLD", "0.56"))
    EVIDENCE_COVERAGE_THRESHOLD = float(os.getenv("EVIDENCE_COVERAGE_THRESHOLD", "0.10"))
    GROUP_CHAT_RELEVANCE_THRESHOLD = float(os.getenv("GROUP_CHAT_RELEVANCE_THRESHOLD", "0.55"))
    PATTERN_MATCH_THRESHOLD = float(os.getenv("PATTERN_MATCH_THRESHOLD", "0.62"))
    MAX_QUESTION_LENGTH = int(os.getenv("MAX_QUESTION_LENGTH", "1200"))
    MAX_REQUEST_BYTES = int(os.getenv("MAX_REQUEST_BYTES", str(1024 * 1024)))
    RESOLVED_GAP_RETENTION_DAYS = int(os.getenv("RESOLVED_GAP_RETENTION_DAYS", "30"))
    TRANSFER_MAX_CLOCK_SKEW_SECONDS = int(os.getenv("TRANSFER_MAX_CLOCK_SKEW_SECONDS", "300"))


@lru_cache
def get_settings():
    return Settings()

"""Create a local JurisTwin .env with cryptographically random secrets.

The file is intentionally generated locally and excluded from release provenance/version control.
Existing values are never overwritten.
"""
from pathlib import Path
import secrets

ROOT = Path(__file__).resolve().parents[1]
ENV = ROOT / ".env"

if ENV.exists():
    print(f"[OK] Existing {ENV.name} preserved")
    raise SystemExit(0)

values = {
    "SECRET_KEY": secrets.token_urlsafe(48),
    "WEBHOOK_SECRET": secrets.token_urlsafe(48),
    "PROOF_SIGNING_SECRET": secrets.token_urlsafe(48),
    "POSTGRES_PASSWORD": secrets.token_urlsafe(32),
}
text = "\n".join([
    "# Auto-generated JurisTwin local secrets. Do not commit this file.",
    f"SECRET_KEY={values['SECRET_KEY']}",
    "DEMO_PASSWORD=Finals2026!",
    "ACCESS_TOKEN_MINUTES=480",
    "CORS_ORIGINS=http://127.0.0.1:5173,http://localhost:5173,http://127.0.0.1:8000,http://localhost:8000",
    f"WEBHOOK_SECRET={values['WEBHOOK_SECRET']}",
    f"PROOF_SIGNING_SECRET={values['PROOF_SIGNING_SECRET']}",
    f"POSTGRES_PASSWORD={values['POSTGRES_PASSWORD']}",
    "",
])
ENV.write_text(text, encoding="utf-8")
print(f"[OK] Generated {ENV.name} with independent random JWT, webhook, Proof Pack and optional PostgreSQL secrets")

from __future__ import annotations

import base64
import hashlib
import hmac
import json
import os
import time
from datetime import datetime, timezone

from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

from ..core.config import get_settings

EXPORT_FORMAT = "JURISTWIN-EXPORT-V1"
EXPORT_KDF_ITERATIONS = 310_000


def _b64(data: bytes) -> str:
    return base64.b64encode(data).decode("ascii")


def _unb64(data: str) -> bytes:
    return base64.b64decode(data.encode("ascii"))


def _derive_export_key(passphrase: str, salt: bytes) -> bytes:
    kdf = PBKDF2HMAC(algorithm=hashes.SHA256(), length=32, salt=salt, iterations=EXPORT_KDF_ITERATIONS)
    return kdf.derive(passphrase.encode("utf-8"))


def encrypt_export_payload(payload: dict, passphrase: str) -> tuple[dict, bytes]:
    """Encrypt a customer export with an operator-supplied passphrase.

    The passphrase is never persisted. AES-GCM gives confidentiality + integrity. The returned
    envelope contains only ciphertext and cryptographic metadata, never plaintext customer rows.
    """
    if len(passphrase) < 10:
        raise ValueError("Export passphrase must contain at least 10 characters.")
    salt = os.urandom(16)
    nonce = os.urandom(12)
    key = _derive_export_key(passphrase, salt)
    aad = f"{EXPORT_FORMAT}|{payload.get('export_ref','unknown')}".encode("utf-8")
    plaintext = json.dumps(payload, ensure_ascii=False, separators=(",", ":"), sort_keys=True).encode("utf-8")
    ciphertext = AESGCM(key).encrypt(nonce, plaintext, aad)
    envelope = {
        "format": EXPORT_FORMAT,
        "cipher": "AES-256-GCM",
        "kdf": "PBKDF2-HMAC-SHA256",
        "kdf_iterations": EXPORT_KDF_ITERATIONS,
        "salt_b64": _b64(salt),
        "nonce_b64": _b64(nonce),
        "aad": aad.decode("utf-8"),
        "ciphertext_b64": _b64(ciphertext),
    }
    file_bytes = json.dumps(envelope, ensure_ascii=False, indent=2, sort_keys=True).encode("utf-8")
    return envelope, file_bytes


def decrypt_export_payload(envelope: dict, passphrase: str) -> dict:
    """Test/support helper used by automated verification; not exposed as a browser endpoint."""
    salt = _unb64(envelope["salt_b64"])
    nonce = _unb64(envelope["nonce_b64"])
    key = _derive_export_key(passphrase, salt)
    plaintext = AESGCM(key).decrypt(nonce, _unb64(envelope["ciphertext_b64"]), envelope["aad"].encode("utf-8"))
    return json.loads(plaintext.decode("utf-8"))


def integration_key_fingerprint() -> str:
    digest = hashlib.sha256(get_settings().INTEGRATION_API_KEY.encode("utf-8")).hexdigest().upper()
    return f"SHA256:{digest[:6]}…{digest[-6:]}"


def sign_transfer_payload(raw_body: bytes, timestamp: str, key: str | None = None) -> str:
    secret = (key or get_settings().INTEGRATION_API_KEY).encode("utf-8")
    return hmac.new(secret, timestamp.encode("ascii") + b"." + raw_body, hashlib.sha256).hexdigest()


def verify_transfer_auth(raw_body: bytes, timestamp: str | None, api_key: str | None, signature: str | None, now: int | None = None) -> tuple[bool, str]:
    settings = get_settings()
    if not api_key or not hmac.compare_digest(api_key, settings.INTEGRATION_API_KEY):
        return False, "API_KEY_REJECTED"
    if not timestamp or not signature:
        return False, "SIGNATURE_REQUIRED"
    try:
        ts = int(timestamp)
    except (TypeError, ValueError):
        return False, "INVALID_TIMESTAMP"
    now = int(now if now is not None else time.time())
    if abs(now - ts) > settings.TRANSFER_MAX_CLOCK_SKEW_SECONDS:
        return False, "REPLAY_WINDOW_REJECTED"
    expected = sign_transfer_payload(raw_body, timestamp)
    if not hmac.compare_digest(signature, expected):
        return False, "SIGNATURE_REJECTED"
    return True, "AUTHENTICATED"


def transfer_security_self_test() -> dict:
    """Exercise key/HMAC/replay properties without exposing the integration secret to the browser."""
    sample = b'{"transfer_ref":"SELF-TEST","ciphertext_b64":"opaque"}'
    ts = str(int(time.time()))
    good_sig = sign_transfer_payload(sample, ts)
    good, _ = verify_transfer_auth(sample, ts, get_settings().INTEGRATION_API_KEY, good_sig)
    bad_key, _ = verify_transfer_auth(sample, ts, "wrong-key", good_sig)
    tampered, _ = verify_transfer_auth(sample + b"x", ts, get_settings().INTEGRATION_API_KEY, good_sig)
    replay_ts = str(int(time.time()) - get_settings().TRANSFER_MAX_CLOCK_SKEW_SECONDS - 20)
    replay_sig = sign_transfer_payload(sample, replay_ts)
    replay, _ = verify_transfer_auth(sample, replay_ts, get_settings().INTEGRATION_API_KEY, replay_sig)
    return {
        "status": "PASS" if good and not bad_key and not tampered and not replay else "FAIL",
        "api_key_gate": good and not bad_key,
        "hmac_integrity": good and not tampered,
        "replay_window": not replay,
        "api_key_fingerprint": integration_key_fingerprint(),
        "api_key_exposed_to_browser": False,
        "transport_policy": "HTTPS/TLS required when REQUIRE_HTTPS=true; localhost demo uses loopback HTTP only.",
        "production_https_enforced": bool(get_settings().REQUIRE_HTTPS),
        "key_mode": get_settings().INTEGRATION_KEY_MODE,
    }

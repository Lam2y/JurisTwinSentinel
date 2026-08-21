from __future__ import annotations

import hashlib
from fastapi import APIRouter, Depends, Header, HTTPException, Request
from sqlalchemy.orm import Session

from ..db.database import get_db
from ..schemas import SecureTransferPacket
from ..services.ledger import append_entry
from ..services.secure_exchange import verify_transfer_auth

router = APIRouter(prefix="/integration", tags=["integration"])


@router.post("/secure-packet")
async def receive_secure_packet(
    body: SecureTransferPacket,
    request: Request,
    db: Session = Depends(get_db),
    x_juristwin_api_key: str | None = Header(default=None, alias="X-JurisTwin-API-Key"),
    x_juristwin_timestamp: str | None = Header(default=None, alias="X-JurisTwin-Timestamp"),
    x_juristwin_signature: str | None = Header(default=None, alias="X-JurisTwin-Signature"),
):
    """Server-to-server encrypted-packet boundary.

    Raw customer plaintext is not accepted here. The body contains ciphertext only and is protected
    by an API key + HMAC request signature. Production deployments additionally enable HTTPS-only
    middleware with REQUIRE_HTTPS=true.
    """
    raw = await request.body()
    ok, reason = verify_transfer_auth(raw, x_juristwin_timestamp, x_juristwin_api_key, x_juristwin_signature)
    if not ok:
        append_entry(db, "SYSTEM_TRANSFER_BLOCKED", "integration-gateway", {"reason": reason, "source_system": body.source_system})
        db.commit()
        raise HTTPException(401, f"Secure transfer authentication failed: {reason}")

    try:
        import base64
        ciphertext = base64.b64decode(body.ciphertext_b64.encode("ascii"), validate=True)
    except Exception:
        raise HTTPException(422, "ciphertext_b64 is not valid Base64")
    if hashlib.sha256(ciphertext).hexdigest().lower() != body.payload_sha256.lower():
        raise HTTPException(422, "Encrypted payload checksum does not match")

    entry = append_entry(db, "SYSTEM_TRANSFER_ACCEPTED", "integration-gateway", {
        "transfer_ref": body.transfer_ref,
        "source_system": body.source_system,
        "purpose": body.purpose,
        "cipher": body.cipher,
        "ciphertext_bytes": len(ciphertext),
        "payload_sha256": body.payload_sha256.lower(),
        "plaintext_received": False,
        "api_key_authenticated": True,
        "hmac_verified": True,
    })
    db.commit()
    return {"status": "ACCEPTED", "transfer_ref": body.transfer_ref, "audit_txid": entry.txid, "plaintext_received": False}

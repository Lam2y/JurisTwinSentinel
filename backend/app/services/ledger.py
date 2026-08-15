import hashlib
from sqlalchemy import select
from sqlalchemy.orm import Session
from ..db.models import LedgerEntry
from .common import dumps, loads, iso, utcnow


def _hash(previous_hash: str | None, txid: str, action: str, actor: str, payload_json: str, created_at) -> str:
    raw = "|".join([previous_hash or "GENESIS", txid, action, actor, payload_json, iso(created_at) or ""])
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def append_entry(db: Session, action: str, actor: str, payload: dict, decision_ref: str | None = None) -> LedgerEntry:
    previous = db.execute(select(LedgerEntry).order_by(LedgerEntry.id.desc()).limit(1)).scalar_one_or_none()
    created_at = utcnow()
    seq = (previous.id + 1) if previous else 0
    prefix = hashlib.sha256((decision_ref or "system").encode()).hexdigest()[:8]
    txid = f"{prefix}_{seq:03d}"
    payload_json = dumps(payload)
    previous_hash = previous.entry_hash if previous else None
    entry_hash = _hash(previous_hash, txid, action, actor, payload_json, created_at)
    entry = LedgerEntry(
        txid=txid, decision_ref=decision_ref, action=action, actor=actor,
        payload_json=payload_json, previous_hash=previous_hash, entry_hash=entry_hash,
        created_at=created_at,
    )
    db.add(entry)
    db.flush()
    return entry


def verify_chain(db: Session) -> dict:
    entries = db.execute(select(LedgerEntry).order_by(LedgerEntry.id.asc())).scalars().all()
    previous = None
    errors = []
    for e in entries:
        expected = _hash(previous, e.txid, e.action, e.actor, e.payload_json, e.created_at)
        if e.previous_hash != previous:
            errors.append({"txid": e.txid, "error": "previous_hash mismatch"})
        if e.entry_hash != expected:
            errors.append({"txid": e.txid, "error": "entry_hash mismatch"})
        previous = e.entry_hash
    return {"ok": not errors, "entries": len(entries), "errors": errors, "head_hash": previous}


def serialize_entry(e: LedgerEntry):
    return {
        "txid": e.txid, "decision_ref": e.decision_ref, "action": e.action,
        "actor": e.actor, "payload": loads(e.payload_json, {}),
        "previous_hash": e.previous_hash, "entry_hash": e.entry_hash,
        "created_at": iso(e.created_at),
    }

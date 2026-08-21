import hashlib
import hmac
from sqlalchemy import select
from sqlalchemy.orm import Session
from ..core.config import get_settings
from ..db.models import LedgerEntry
from .common import dumps, loads, iso, utcnow


def _raw(previous_hash, txid, action, actor, payload_json, created_at):
    return "|".join([previous_hash or "GENESIS", txid, action, actor, payload_json, iso(created_at) or ""]).encode("utf-8")


def _hash_v2(previous_hash, txid, action, actor, payload_json, created_at):
    """Keyed HMAC chain: a DB-only attacker cannot silently recompute valid history."""
    key = get_settings().SECRET_KEY.encode("utf-8")
    return hmac.new(key, _raw(previous_hash, txid, action, actor, payload_json, created_at), hashlib.sha256).hexdigest()


def _hash_legacy(previous_hash, txid, action, actor, payload_json, created_at):
    # Kept only so v8 demo databases can migrate without invalidating old entries.
    return hashlib.sha256(_raw(previous_hash, txid, action, actor, payload_json, created_at)).hexdigest()


def append_entry(db: Session, action: str, actor: str, payload: dict):
    previous = db.execute(select(LedgerEntry).order_by(LedgerEntry.id.desc()).limit(1)).scalar_one_or_none()
    created_at = utcnow()
    seq = (previous.id + 1) if previous else 1
    txid = f"JT-{seq:06d}"
    payload_json = dumps(payload)
    previous_hash = previous.entry_hash if previous else None
    entry = LedgerEntry(
        txid=txid,
        action=action,
        actor=actor,
        payload_json=payload_json,
        previous_hash=previous_hash,
        entry_hash=_hash_v2(previous_hash, txid, action, actor, payload_json, created_at),
        created_at=created_at,
    )
    db.add(entry)
    db.flush()
    return entry


def verify_chain(db: Session):
    rows = db.execute(select(LedgerEntry).order_by(LedgerEntry.id)).scalars().all()
    previous = None
    errors = []
    legacy_entries = 0
    for row in rows:
        expected_v2 = _hash_v2(previous, row.txid, row.action, row.actor, row.payload_json, row.created_at)
        expected_legacy = _hash_legacy(previous, row.txid, row.action, row.actor, row.payload_json, row.created_at)
        valid_hash = hmac.compare_digest(row.entry_hash, expected_v2)
        if not valid_hash and hmac.compare_digest(row.entry_hash, expected_legacy):
            valid_hash = True
            legacy_entries += 1
        if row.previous_hash != previous or not valid_hash:
            errors.append(row.txid)
        previous = row.entry_hash
    return {
        "ok": not errors,
        "entries": len(rows),
        "errors": errors,
        "head_hash": previous,
        "algorithm": "HMAC-SHA256 chained ledger",
        "legacy_entries": legacy_entries,
    }


def serialize_entry(row: LedgerEntry):
    return {
        "txid": row.txid,
        "action": row.action,
        "actor": row.actor,
        "payload": loads(row.payload_json, {}),
        "previous_hash": row.previous_hash,
        "entry_hash": row.entry_hash,
        "created_at": iso(row.created_at),
    }

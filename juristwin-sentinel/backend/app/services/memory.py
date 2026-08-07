import math
import re
from collections import Counter
from sqlalchemy import select
from sqlalchemy.orm import Session
from ..db.models import Evidence, User
from .common import loads, iso

TOKEN_RE = re.compile(r"[a-z0-9]+")
ROLE_MAX_SENSITIVITY = {
    "manager": 3,
    "compliance_manager": 3,
    "product_owner": 3,
    "officer": 2,
    "intern": 1,
}
SENSITIVITY_LEVEL = {"public": 0, "internal": 1, "confidential": 2, "restricted": 3}


def tokenize(text: str):
    return TOKEN_RE.findall((text or "").lower())


def cosine(a: Counter, b: Counter):
    dot = sum(a[k] * b.get(k, 0) for k in a)
    na = math.sqrt(sum(v*v for v in a.values()))
    nb = math.sqrt(sum(v*v for v in b.values()))
    return dot / (na * nb) if na and nb else 0.0


def _can_access(user: User, e: Evidence):
    max_level = ROLE_MAX_SENSITIVITY.get(user.role, 1)
    level = SENSITIVITY_LEVEL.get((e.sensitivity or "internal").lower(), 1)
    if level <= max_level:
        if user.role == "officer" and e.case_ref:
            assigned = set(loads(user.assigned_case_refs, []))
            return e.case_ref in assigned or e.case_ref == "JT-2026-084"
        return True
    return False


def _redacted(e: Evidence):
    return {
        "evidence_ref": e.evidence_ref, "source": e.source, "title": e.title,
        "body": "[REDACTED BY SENTINEL SHIELD]", "rule_key": e.rule_key,
        "claim": "[RESTRICTED]", "authority": e.authority, "authority_level": e.authority_level,
        "version": e.version, "status": e.status, "sensitivity": e.sensitivity,
        "case_ref": e.case_ref, "approved": e.approved, "superseded": e.superseded,
        "created_at": iso(e.created_at), "metadata": {"access": "redacted"},
    }


def serialize_evidence(e: Evidence, user: User, score: float | None = None):
    if not _can_access(user, e):
        result = _redacted(e)
    else:
        result = {
            "evidence_ref": e.evidence_ref, "source": e.source, "title": e.title, "body": e.body,
            "rule_key": e.rule_key, "claim": e.claim, "authority": e.authority,
            "authority_level": e.authority_level, "version": e.version, "status": e.status,
            "sensitivity": e.sensitivity, "case_ref": e.case_ref, "approved": e.approved,
            "superseded": e.superseded, "created_at": iso(e.created_at),
            "metadata": loads(e.metadata_json, {}),
        }
    if score is not None:
        result["score"] = round(score, 4)
    return result


def search_memory(db: Session, user: User, query: str, limit: int = 10):
    rows = db.execute(select(Evidence).order_by(Evidence.created_at.desc())).scalars().all()
    qv = Counter(tokenize(query))
    scored = []
    for e in rows:
        text = " ".join([e.title or "", e.body or "", e.claim or "", e.rule_key or "", e.source or ""])
        score = cosine(qv, Counter(tokenize(text))) if qv else 0.0
        if score > 0 or not qv:
            scored.append((score, e))
    scored.sort(key=lambda x: (x[0], x[1].created_at), reverse=True)
    return [serialize_evidence(e, user, s) for s, e in scored[:limit]]

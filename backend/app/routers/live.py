from fastapi import APIRouter, Depends, HTTPException, Header
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..core.security import current_user, require_roles
from ..db.database import get_db
from ..db.models import LiveChallenge, User, Integration
from ..schemas import LiveChallengeRequest, EvidenceDropRequest, SignedWebhookRequest
from ..services.live_challenge import run_live_challenge, serialize_challenge
from ..services.impact_graph import build_impact_graph
from ..services.red_team import run_red_team
from ..services.policy_ml import get_policy_ai
from ..core.config import get_settings

router = APIRouter(prefix="/live", tags=["live-challenge"])


@router.post("/challenge")
def challenge(
    body: LiveChallengeRequest,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles("manager", "compliance_manager", "product_owner")),
):
    return run_live_challenge(db, body, user)


@router.get("/challenges")
def challenges(
    limit: int = 10,
    db: Session = Depends(get_db),
    user: User = Depends(current_user),
):
    limit = max(1, min(limit, 50))
    rows = db.execute(select(LiveChallenge).order_by(LiveChallenge.id.desc()).limit(limit)).scalars().all()
    return [serialize_challenge(x) for x in rows]


_ALLOWED_TEXT_EXTENSIONS = {".txt", ".md", ".csv", ".json", ".eml", ".log"}

@router.post("/evidence-drop")
def evidence_drop(
    body: EvidenceDropRequest,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles("manager", "compliance_manager", "product_owner")),
):
    from pathlib import Path
    suffix = Path(body.filename).suffix.lower()
    if suffix not in _ALLOWED_TEXT_EXTENSIONS:
        raise HTTPException(415, f"Unsupported finals file type '{suffix or 'none'}'. Use TXT, MD, CSV, JSON, EML or LOG for deterministic offline parsing.")
    content = body.content.strip()
    if suffix == ".json":
        import json
        try:
            parsed = json.loads(content)
            content = json.dumps(parsed, ensure_ascii=False, indent=2)
        except Exception:
            raise HTTPException(422, "JSON evidence is malformed; Sentinel refused to infer policy from invalid structured data")
    req = LiveChallengeRequest(
        source=f"Judge Evidence Drop · {body.filename}",
        title=f"Unseen file: {body.filename}",
        body=content,
        authority=body.authority,
        authority_level=body.authority_level,
        sensitivity=body.sensitivity,
    )
    result = run_live_challenge(db, req, user)
    result["file_ingestion"] = {
        "filename": body.filename, "mime_type": body.mime_type, "bytes": len(body.content.encode("utf-8")),
        "parser": "deterministic-text-gateway", "network_required": False,
    }
    return result

@router.get("/challenges/{challenge_ref}/impact")
def challenge_impact(
    challenge_ref: str,
    db: Session = Depends(get_db),
    user: User = Depends(current_user),
):
    c = db.execute(select(LiveChallenge).where(LiveChallenge.challenge_ref == challenge_ref)).scalar_one_or_none()
    if not c:
        raise HTTPException(404, "Live challenge not found")
    return build_impact_graph(db, c.inferred_rule_key, c.conflict_ref)

@router.get("/ai-model")
def ai_model(user: User = Depends(current_user)):
    """Expose the learned component and its honest development benchmark to judges."""
    return get_policy_ai().model_card()


@router.post("/red-team")
def red_team(
    db: Session = Depends(get_db),
    user: User = Depends(require_roles("manager", "compliance_manager", "product_owner")),
):
    return run_red_team(db)


@router.post("/webhook")
def signed_webhook(
    body: SignedWebhookRequest,
    x_juristwin_signature: str | None = Header(default=None, alias="X-JurisTwin-Signature"),
    db: Session = Depends(get_db),
):
    """Real machine-to-machine evidence ingress secured by HMAC-SHA256.

    Signature material is UTF-8: ``event_id + "|" + body``. This route intentionally does not
    depend on an interactive JWT because connectors authenticate with a shared signing secret.
    """
    import hashlib, hmac
    from types import SimpleNamespace
    from ..db.models import Evidence
    settings=get_settings()
    material=f"{body.event_id}|{body.body}".encode("utf-8")
    expected=hmac.new(settings.WEBHOOK_SECRET.encode("utf-8"),material,hashlib.sha256).hexdigest()
    supplied=(x_juristwin_signature or "").strip().lower()
    if not supplied or not hmac.compare_digest(expected,supplied):
        raise HTTPException(401,"Webhook signature verification failed")
    # Idempotency: a signed replay of the exact source/body returns the existing governed record
    # instead of creating duplicate evidence or duplicate conflicts.
    prior=db.execute(select(Evidence).where(Evidence.source==f"LIVE WEBHOOK · {body.source}",Evidence.body==body.body)).scalars().first()
    if prior:
        return {
            "status":"DUPLICATE_IGNORED", "event_id":body.event_id, "evidence_ref":prior.evidence_ref,
            "idempotent":True, "message":"Signed replay matched existing evidence; no duplicate state was created.",
        }
    req=LiveChallengeRequest(
        source=f"LIVE WEBHOOK · {body.source}", title=body.title, body=body.body,
        authority=body.authority, authority_level=body.authority_level, sensitivity=body.sensitivity,
    )
    actor=SimpleNamespace(email=f"connector:{body.source.lower().replace(' ','_')}")
    result=run_live_challenge(db,req,actor)
    gateway=db.execute(select(Integration).where(Integration.key=="webhook")).scalar_one_or_none()
    if gateway:
        details=__import__("json").loads(gateway.details_json or "{}")
        gateway.object_count=int(gateway.object_count or 0)+1
        from ..services.common import utcnow, dumps
        gateway.last_sync_at=utcnow(); details["last_event_id"]=body.event_id; details["errors"]=0
        gateway.details_json=dumps(details); db.commit(); db.refresh(gateway)
    result["connector"]={
        "mode":"HMAC-SHA256 signed webhook", "event_id":body.event_id, "authenticated":True,
        "idempotent":True, "network_ingress":"real HTTP POST",
    }
    return result

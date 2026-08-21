import hashlib
import statistics
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from ..core.config import get_settings
from ..core.security import require_superadmin
from ..db.database import get_db
from ..db.models import AnswerFeedback, Evidence, EvidenceOrigin, Interaction, KnowledgeGap, ResolutionPattern, User
from ..schemas import EvidenceIngestRequest, PatternStateRequest, PublishResolutionRequest, TwinRunRequest
from ..services.common import iso, loads
from ..services.ledger import append_entry
from ..services.policy_ml import get_policy_ai
from ..services.policy_reasoner import compare_policy_atoms, extract_policy_atoms
from ..services.decision_twin import run_decision_twin
from ..services.resolution_engine import (
    analyse_question,
    contains_sensitive,
    content_fingerprint,
    gap_detail,
    publish_gap,
)

router = APIRouter(prefix="/admin", tags=["admin"])


@router.get("/overview")
def overview(db: Session = Depends(get_db), user: User = Depends(require_superadmin)):
    open_count = db.execute(select(func.count(KnowledgeGap.id)).where(KnowledgeGap.status == "open")).scalar_one()
    resolved_count = db.execute(select(func.count(KnowledgeGap.id)).where(KnowledgeGap.status == "resolved")).scalar_one()
    pattern_count = db.execute(select(func.count(ResolutionPattern.id)).where(ResolutionPattern.active.is_(True))).scalar_one()
    feedback_review = db.execute(select(func.count(AnswerFeedback.id)).where(AnswerFeedback.helpful.is_(False))).scalar_one()
    return {"open_gaps": open_count, "resolved_gaps": resolved_count, "active_patterns": pattern_count, "negative_feedback": feedback_review}


@router.get("/gaps")
def gaps(status: str = Query(default="open", pattern="^(open|resolved|all)$"), db: Session = Depends(get_db), user: User = Depends(require_superadmin)):
    stmt = select(KnowledgeGap)
    if status != "all":
        stmt = stmt.where(KnowledgeGap.status == status)
    rows = db.execute(stmt.order_by(KnowledgeGap.last_seen_at.desc())).scalars().all()
    return [{
        "gap_ref": r.gap_ref, "question": r.question, "predicted_domain": r.predicted_domain,
        "domain_confidence": round(r.domain_confidence or 0, 4), "reason": r.reason,
        "status": r.status, "occurrence_count": r.occurrence_count,
        "last_seen_at": iso(r.last_seen_at), "resolution_ref": r.resolution_ref,
    } for r in rows]


@router.get("/gaps/{gap_ref}")
def get_gap(gap_ref: str, db: Session = Depends(get_db), user: User = Depends(require_superadmin)):
    gap = db.execute(select(KnowledgeGap).where(KnowledgeGap.gap_ref == gap_ref)).scalar_one_or_none()
    if not gap:
        raise HTTPException(404, "Knowledge gap not found")
    return gap_detail(db, gap)


@router.post("/gaps/{gap_ref}/publish")
def publish(gap_ref: str, body: PublishResolutionRequest, db: Session = Depends(get_db), user: User = Depends(require_superadmin)):
    gap = db.execute(select(KnowledgeGap).where(KnowledgeGap.gap_ref == gap_ref)).scalar_one_or_none()
    if not gap:
        raise HTTPException(404, "Knowledge gap not found")
    try:
        p = publish_gap(db, gap, user, body.answer, body.source_refs, body.uncertainty_note, body.match_threshold)
    except ValueError as exc:
        raise HTTPException(422, str(exc))
    return {
        "ok": True, "resolution_ref": p.resolution_ref, "answer": p.answer,
        "rule_key": p.rule_key, "source_refs": loads(p.source_refs_json, []),
        "uncertainty_note": p.uncertainty_note, "match_threshold": p.match_threshold,
    }


@router.post("/evidence/ingest")
def ingest_evidence(body: EvidenceIngestRequest, db: Session = Depends(get_db), user: User = Depends(require_superadmin)):
    """Live evidence intake without a separate 'test evidence' page.

    New evidence is deliberately quarantined (unapproved) so ingesting a document can never silently
    change the answer that regular users receive.
    """
    if body.source_scope == "private_message":
        append_entry(db, "PRIVATE_MESSAGE_INGEST_BLOCKED", user.email, {"source": body.source, "title": body.title})
        db.commit()
        raise HTTPException(422, "Private/direct messages are outside JurisTwin's approved collection scope. Use an approved group channel, formal approval or shared repository instead.")
    if contains_sensitive(body.body):
        raise HTTPException(422, "Potential personal identifier detected. Redact personal data before ingesting policy evidence.")

    existing = db.execute(select(Evidence)).scalars().all()
    incoming_fp = content_fingerprint(body.source, body.title, body.body)
    for e in existing:
        if content_fingerprint(e.source, e.title, e.body) == incoming_fp:
            return {"ok": True, "duplicate": True, "evidence_ref": e.evidence_ref, "rule_key": e.rule_key, "quarantined": not e.approved}

    rule_key = body.rule_key
    model_trace = None
    prediction = get_policy_ai().predict(body.body)
    collection_domain = prediction.get("domain", {})
    if not rule_key:
        model_trace = collection_domain
        if model_trace.get("abstain") or model_trace.get("label") == "general_policy_rule":
            raise HTTPException(422, "The domain classifier is uncertain. Select the policy domain manually before ingesting this evidence.")
        rule_key = model_trace.get("label")

    # Collaboration privacy minimisation: a group-channel message is collected only when it is
    # relevant to the selected policy domain. Generic group chatter is not retained 'just in case'.
    collection_relevance = float(collection_domain.get("confidence") or 0.0)
    if body.source_scope == "group_channel":
        if collection_domain.get("label") != rule_key or collection_relevance < get_settings().GROUP_CHAT_RELEVANCE_THRESHOLD:
            append_entry(db, "IRRELEVANT_GROUP_CHAT_BLOCKED", user.email, {
                "source": body.source, "title": body.title, "selected_domain": rule_key,
                "predicted_domain": collection_domain.get("label"), "confidence": round(collection_relevance, 4),
            })
            db.commit()
            raise HTTPException(422, "This group-channel message is outside the relevant policy scope and was not stored. JurisTwin does not collect unrelated group chatter.")

    ref = f"EV-LIVE-{uuid4().hex[:10].upper()}"
    claim = (body.claim or f"candidate_{hashlib.sha256(body.body.encode('utf-8')).hexdigest()[:10]}").strip()
    row = Evidence(
        evidence_ref=ref,
        source=body.source.strip(),
        title=body.title.strip(),
        body=body.body.strip(),
        rule_key=rule_key,
        claim=claim,
        authority=body.authority.strip(),
        authority_level=body.authority_level,
        version=(body.version or "live submission").strip(),
        status="active",
        sensitivity=body.sensitivity,
        approved=False,
        superseded=False,
    )

    current = db.execute(select(Evidence).where(
        Evidence.rule_key == rule_key,
        Evidence.approved.is_(True),
        Evidence.superseded.is_(False),
        Evidence.status == "active",
    ).order_by(Evidence.authority_level.desc())).scalars().all()
    collisions = []
    incoming_atoms = extract_policy_atoms(row.body, rule_key)
    for canonical in current:
        comparison = compare_policy_atoms(extract_policy_atoms(canonical.body, canonical.rule_key), incoming_atoms)
        if comparison.get("collision"):
            collisions.extend(comparison.get("collisions", []))

    db.add(row)
    db.flush()
    db.add(EvidenceOrigin(
        evidence_ref=row.evidence_ref,
        connector=("Microsoft Teams" if body.source_scope == "group_channel" else body.source.strip()),
        source_scope=body.source_scope,
        collection_reason=("Approved group-channel content passed the policy relevance gate." if body.source_scope == "group_channel" else "Superadmin-submitted evidence accepted within the approved relevant-source boundary."),
        private_message_excluded=True,
        relevance_score=collection_relevance if body.source_scope == "group_channel" else 1.0,
    ))
    append_entry(db, "EVIDENCE_INGESTED_QUARANTINED", user.email, {
        "evidence_ref": row.evidence_ref,
        "rule_key": row.rule_key,
        "source": row.source,
        "content_sha256": hashlib.sha256(row.body.encode("utf-8")).hexdigest(),
        "collision_count": len(collisions),
        "approved": False,
        "source_scope": body.source_scope,
        "private_message_excluded": True,
        "collection_relevance": round(collection_relevance, 4),
    })
    db.commit()
    return {
        "ok": True,
        "duplicate": False,
        "evidence_ref": row.evidence_ref,
        "rule_key": row.rule_key,
        "quarantined": True,
        "approval_state": "candidate_only",
        "source_scope": body.source_scope,
        "private_message_excluded": True,
        "collection_relevance": round(collection_relevance, 4),
        "collisions": collisions[:8],
        "model_trace": model_trace,
        "message": "Evidence stored as a quarantined candidate. It cannot silently replace governed policy.",
    }


@router.get("/compare/{rule_key}")
def compare(rule_key: str, db: Session = Depends(get_db), user: User = Depends(require_superadmin)):
    if not db.execute(select(Evidence).where(Evidence.rule_key == rule_key).limit(1)).scalar_one_or_none():
        raise HTTPException(404, "Policy domain not found")
    question = {
        "income_document_rule": "What income evidence is accepted for gig workers?",
        "loan_restructure_rule": "What is the loan restructuring approval threshold?",
        "notification_deadline": "What is the customer notification deadline?",
    }.get(rule_key, rule_key.replace("_", " "))
    return analyse_question(db, question, predicted_domain=rule_key)


@router.post("/compare/{rule_key}/simulate")
def simulate_compare(rule_key: str, body: TwinRunRequest, db: Session = Depends(get_db), user: User = Depends(require_superadmin)):
    if not db.execute(select(Evidence).where(Evidence.rule_key == rule_key).limit(1)).scalar_one_or_none():
        raise HTTPException(404, "Policy domain not found")
    try:
        result = run_decision_twin(rule_key, {"delay": body.delay, "complaint": body.complaint, "alignment": body.alignment})
    except ValueError as exc:
        raise HTTPException(422, str(exc))
    append_entry(db, "DECISION_TWIN_RUN", user.email, {
        "rule_key": rule_key,
        "scenario_count": result["scenario_count"],
        "recommended_option": result["recommended_option"],
        "certificate": result["decision_certificate"],
    })
    db.commit()
    return result


@router.get("/patterns")
def patterns(db: Session = Depends(get_db), user: User = Depends(require_superadmin)):
    rows = db.execute(select(ResolutionPattern).order_by(ResolutionPattern.created_at.desc())).scalars().all()
    return [{
        "resolution_ref": r.resolution_ref, "example_question": r.example_question, "answer": r.answer,
        "rule_key": r.rule_key, "source_refs": loads(r.source_refs_json, []), "uncertainty_note": r.uncertainty_note,
        "match_threshold": r.match_threshold, "active": r.active, "created_by": r.created_by, "created_at": iso(r.created_at),
    } for r in rows]


@router.patch("/patterns/{resolution_ref}")
def set_pattern_state(resolution_ref: str, body: PatternStateRequest, db: Session = Depends(get_db), user: User = Depends(require_superadmin)):
    pattern = db.execute(select(ResolutionPattern).where(ResolutionPattern.resolution_ref == resolution_ref)).scalar_one_or_none()
    if not pattern:
        raise HTTPException(404, "Governed decision memory not found")
    if pattern.active == body.active:
        return {"ok": True, "resolution_ref": pattern.resolution_ref, "active": pattern.active, "unchanged": True}
    pattern.active = body.active
    linked_gap = db.execute(select(KnowledgeGap).where(KnowledgeGap.resolution_ref == resolution_ref)).scalar_one_or_none()
    if linked_gap and not body.active:
        linked_gap.status = "open"
        linked_gap.resolved_at = None
    append_entry(db, "DECISION_MEMORY_STATE_CHANGED", user.email, {
        "resolution_ref": resolution_ref,
        "active": body.active,
        "reason": body.reason or "not provided",
        "reopened_gap": linked_gap.gap_ref if linked_gap and not body.active else None,
    })
    db.commit()
    return {"ok": True, "resolution_ref": pattern.resolution_ref, "active": pattern.active, "reopened_gap": linked_gap.gap_ref if linked_gap and not body.active else None}


@router.get("/metrics")
def metrics(db: Session = Depends(get_db), user: User = Depends(require_superadmin)):
    interactions = db.execute(select(Interaction).order_by(Interaction.id)).scalars().all()
    feedback = db.execute(select(AnswerFeedback)).scalars().all()
    total = len(interactions)
    answered = sum(1 for x in interactions if x.status == "ANSWERED")
    review = sum(1 for x in interactions if x.status == "REVIEW_PENDING")
    reused = sum(1 for x in interactions if x.handled_by == "governed_pattern_memory")
    helpful = sum(1 for x in feedback if x.helpful)
    negative = sum(1 for x in feedback if not x.helpful)
    latencies = [float(x.latency_ms or 0) for x in interactions]
    median_ms = round(statistics.median(latencies), 2) if latencies else 0.0
    p95_ms = round(sorted(latencies)[max(0, int(len(latencies) * .95) - 1)], 2) if latencies else 0.0
    return {
        "live_validation": {
            "interactions": total,
            "answered": answered,
            "review_pending": review,
            "answer_rate": round(answered / total, 4) if total else 0.0,
            "safe_abstention_rate": round(review / total, 4) if total else 0.0,
            "pattern_reuse_count": reused,
            "pattern_reuse_rate": round(reused / answered, 4) if answered else 0.0,
            "feedback_count": len(feedback),
            "helpful_count": helpful,
            "needs_review_count": negative,
            "helpfulness_rate": round(helpful / len(feedback), 4) if feedback else None,
            "median_latency_ms": median_ms,
            "p95_latency_ms": p95_ms,
        },
        "operational": {
            "open_gaps": db.execute(select(func.count(KnowledgeGap.id)).where(KnowledgeGap.status == "open")).scalar_one(),
            "resolved_gaps": db.execute(select(func.count(KnowledgeGap.id)).where(KnowledgeGap.status == "resolved")).scalar_one(),
            "active_patterns": db.execute(select(func.count(ResolutionPattern.id)).where(ResolutionPattern.active.is_(True))).scalar_one(),
            "evidence_records": db.execute(select(func.count(Evidence.id))).scalar_one(),
        },
        "adoption_readiness": {
            "api_first": True,
            "database_portable": "SQLite demo / PostgreSQL via DATABASE_URL",
            "internet_required_for_core": False,
            "enterprise_sso_integration_point": "Replace demo login with identity-provider/OIDC adapter",
            "note": "These are live prototype telemetry and deployment-readiness signals, not claimed production market validation.",
        },
    }

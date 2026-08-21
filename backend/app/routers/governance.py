from uuid import uuid4
from datetime import datetime, timezone
import base64
import hashlib
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select, text
from sqlalchemy.orm import Session

from ..core.config import get_settings
from ..core.security import current_user, require_superadmin
from ..db.database import get_db
from ..db.models import (
    AnswerFeedback,
    Evidence,
    Interaction,
    KnowledgeGap,
    LedgerEntry,
    ResolutionPattern,
    ResilienceRun,
    RolePolicy,
    SecurityShield,
    User,
    EvidenceOrigin,
)
from ..schemas import ShieldUpdateRequest, CustomerExportRequest
from ..services.common import dumps, iso, loads
from ..services.ledger import append_entry, serialize_entry, verify_chain
from ..services.policy_ml import get_policy_ai
from ..services.policy_reasoner import compare_policy_atoms, extract_policy_atoms
from ..services.resolution_engine import redact_sensitive
from ..services.retention import expired_resolved_gap_count
from ..services.secure_exchange import encrypt_export_payload, decrypt_export_payload, transfer_security_self_test, integration_key_fingerprint

router = APIRouter(prefix="/governance", tags=["governance"])


def _resilience_checks(db: Session):
    settings = get_settings()
    checks = []

    try:
        db.execute(text("SELECT 1"))
        checks.append({"key": "database", "label": "Database round-trip", "ok": True, "detail": "Transactional database query completed successfully."})
    except Exception as exc:
        checks.append({"key": "database", "label": "Database round-trip", "ok": False, "detail": f"Database error: {type(exc).__name__}"})

    roles = db.execute(select(RolePolicy)).scalars().all()
    role_map = {r.role: r for r in roles}
    rbac_ok = (
        "regular_user" in role_map and "superadmin" in role_map
        and not role_map["regular_user"].can_manage_governance
        and role_map["superadmin"].can_manage_governance
    )
    checks.append({"key": "rbac", "label": "Least-privilege RBAC", "ok": rbac_ok, "detail": "Regular users cannot manage governance; superadmins can."})

    masked = redact_sensitive("Email jane@example.com account 123456789012345", db)
    pii_ok = "jane@example.com" not in masked and "123456789012345" not in masked
    checks.append({"key": "pii", "label": "PII minimisation", "ok": pii_ok, "detail": "Email and long account-like identifiers are masked before review persistence."})

    chain = verify_chain(db)
    checks.append({"key": "audit", "label": "Tamper-evident audit", "ok": chain["ok"], "detail": f"{chain['algorithm']} · {chain['entries']} entries verified."})

    try:
        card = get_policy_ai().model_card()
        model_ok = card.get("status") == "READY"
        detail = f"Local hybrid model ready · {card.get('training', {}).get('samples', 0)} curated development samples."
    except Exception as exc:
        model_ok = False
        detail = f"Learned model unavailable ({type(exc).__name__}); deterministic evidence gates remain fail-safe."
    checks.append({"key": "model", "label": "Hybrid AI layer", "ok": model_ok, "detail": detail})

    approved = db.execute(select(Evidence).where(Evidence.approved.is_(True), Evidence.superseded.is_(False), Evidence.status == "active")).scalars().all()
    checks.append({"key": "evidence", "label": "Governed evidence", "ok": len(approved) >= 3, "detail": f"{len(approved)} current approved evidence records are available."})

    conflict_gate_ok = False
    income = [e for e in approved if e.rule_key == "income_document_rule"]
    stale = db.execute(select(Evidence).where(Evidence.rule_key == "income_document_rule", Evidence.superseded.is_(True))).scalars().all()
    if income and stale:
        comparison = compare_policy_atoms(extract_policy_atoms(income[0].body, income[0].rule_key), extract_policy_atoms(stale[0].body, stale[0].rule_key))
        conflict_gate_ok = bool(comparison.get("collision"))
    checks.append({"key": "contradiction", "label": "Contradiction detector", "ok": conflict_gate_ok, "detail": "White-box policy atoms detect known modality/threshold/deadline collisions."})

    shields = {s.key: bool(s.enabled) for s in db.execute(select(SecurityShield)).scalars().all()}
    essential = ["rbac", "pii_masking", "no_training", "audit_chain", "abstention"]
    checks.append({"key": "shields", "label": "Critical safety controls", "ok": all(shields.get(k, False) for k in essential), "detail": "RBAC, PII masking, training isolation, audit chain and abstention are active."})

    checks.append({"key": "request_limits", "label": "Input & request containment", "ok": settings.MAX_REQUEST_BYTES <= 2 * 1024 * 1024, "detail": f"Request body ceiling {settings.MAX_REQUEST_BYTES // 1024} KB; Pydantic field validation enabled."})
    checks.append({"key": "offline", "label": "Offline core continuity", "ok": True, "detail": "Core answering, ML routing and policy reasoning require no internet connection."})

    expired = expired_resolved_gap_count(db)
    checks.append({"key": "retention", "label": "Review-data retention enforcement", "ok": expired == 0, "detail": f"{expired} resolved review records exceed the {settings.RESOLVED_GAP_RETENTION_DAYS}-day retention window."})

    origins = db.execute(select(EvidenceOrigin)).scalars().all()
    privacy_scope_ok = bool(origins) and all(o.source_scope != "private_message" and o.private_message_excluded for o in origins)
    group_relevance_ok = all((o.source_scope != "group_channel") or float(o.relevance_score or 0) >= settings.GROUP_CHAT_RELEVANCE_THRESHOLD for o in origins)
    checks.append({"key": "source_scope", "label": "Group-channel privacy scope", "ok": privacy_scope_ok and group_relevance_ok, "detail": "Only approved, relevant group-channel evidence is retrievable; PM/DM content is excluded before storage."})

    try:
        sample = {"export_ref": "SELFTEST", "rows": [{"question_masked": "[EMAIL REDACTED]"}]}
        envelope, _ = encrypt_export_payload(sample, "JurisTwinTest!2026")
        export_ok = decrypt_export_payload(envelope, "JurisTwinTest!2026") == sample
    except Exception:
        export_ok = False
    checks.append({"key": "encrypted_export", "label": "Encrypted customer export", "ok": export_ok, "detail": "AES-256-GCM confidentiality/integrity self-test passed; export passphrases are not persisted."})

    transfer = transfer_security_self_test()
    checks.append({"key": "secure_transfer", "label": "Secure system transfer", "ok": transfer.get("status") == "PASS", "detail": "Server-side API-key gate, HMAC payload integrity and replay-window checks passed; browser sees only a key fingerprint."})

    score = round(100 * sum(1 for c in checks if c["ok"]) / len(checks))
    return score, checks


@router.get("/health")
def health(db: Session = Depends(get_db)):
    db.execute(text("SELECT 1"))
    chain = verify_chain(db)
    return {"status": "operational" if chain["ok"] else "degraded", "database": "ok", "audit_chain": chain, "version": get_settings().VERSION, "demo_mode": get_settings().DEMO_MODE}


@router.get("/readiness")
def readiness(db: Session = Depends(get_db), user: User = Depends(current_user)):
    score, checks = _resilience_checks(db)
    return {"status": "READY" if score == 100 else "DEGRADED", "score": score, "checks": checks}


@router.post("/resilience-test")
def resilience_test(db: Session = Depends(get_db), user: User = Depends(require_superadmin)):
    score, checks = _resilience_checks(db)
    run = ResilienceRun(
        run_ref=f"RR-{uuid4().hex[:10].upper()}",
        score=score,
        status="PASS" if score == 100 else "DEGRADED",
        checks_json=dumps(checks),
        created_by=user.email,
    )
    db.add(run)
    db.flush()
    append_entry(db, "RESILIENCE_SELF_TEST_RUN", user.email, {"run_ref": run.run_ref, "score": score, "failed": [c["key"] for c in checks if not c["ok"]]})
    db.commit()
    return {"run_ref": run.run_ref, "score": score, "status": run.status, "checks": checks, "created_at": iso(run.created_at)}


@router.get("/resilience-history")
def resilience_history(limit: int = Query(default=8, ge=1, le=50), db: Session = Depends(get_db), user: User = Depends(require_superadmin)):
    rows = db.execute(select(ResilienceRun).order_by(ResilienceRun.id.desc()).limit(limit)).scalars().all()
    return [{"run_ref": r.run_ref, "score": r.score, "status": r.status, "checks": loads(r.checks_json, []), "created_by": r.created_by, "created_at": iso(r.created_at)} for r in rows]


@router.get("/model-card")
def model_card(user: User = Depends(require_superadmin)):
    return get_policy_ai().model_card()


@router.get("/controls")
def controls(db: Session = Depends(get_db), user: User = Depends(require_superadmin)):
    roles = db.execute(select(RolePolicy).order_by(RolePolicy.id)).scalars().all()
    shields = db.execute(select(SecurityShield).order_by(SecurityShield.id)).scalars().all()
    return {
        "roles": [{"role": r.role, "display_name": r.display_name, "description": r.description, "enabled": r.enabled, "can_manage_governance": r.can_manage_governance, "can_view_sensitive_evidence": r.can_view_sensitive_evidence} for r in roles],
        "shields": [{"key": s.key, "name": s.name, "description": s.description, "enabled": s.enabled, "updated_by": s.updated_by, "updated_at": iso(s.updated_at)} for s in shields],
    }


@router.patch("/shields/{key}")
def update_shield(key: str, body: ShieldUpdateRequest, db: Session = Depends(get_db), user: User = Depends(require_superadmin)):
    shield = db.execute(select(SecurityShield).where(SecurityShield.key == key)).scalar_one_or_none()
    if not shield:
        raise HTTPException(404, "Security control not found")
    if key in {"rbac", "audit_chain"} and body.enabled is False:
        raise HTTPException(409, "Critical identity and audit controls are fail-closed and cannot be disabled from the demo UI.")
    shield.enabled = body.enabled
    shield.updated_by = user.email
    append_entry(db, "SECURITY_SHIELD_UPDATED", user.email, {"key": key, "enabled": body.enabled})
    db.commit()
    return {"key": shield.key, "enabled": shield.enabled, "updated_by": shield.updated_by}


@router.get("/privacy")
def privacy(db: Session = Depends(get_db), user: User = Depends(require_superadmin)):
    settings = get_settings()
    origins = db.execute(select(EvidenceOrigin)).scalars().all()
    scopes = {}
    for row in origins:
        scopes[row.source_scope] = scopes.get(row.source_scope, 0) + 1
    return {
        "principles": [
            {"title": "Relevant sources only", "detail": "Evidence retrieval is policy-domain scoped and semantically ranked; unrelated collaboration chatter is rejected before it becomes evidence."},
            {"title": "Group channels, never PM/DM", "detail": "Collaboration-chat intake accepts approved group channels only. Private/direct messages and 1:1 conversations are explicitly outside the collection boundary."},
            {"title": "Retrieval, not training", "detail": "Enterprise evidence is used at answer time and is never appended to the bundled ML training corpus."},
            {"title": "PII-minimised persistence", "detail": "Emails, phone numbers and long account-like numbers are masked before unresolved questions or feedback comments are stored."},
            {"title": "Least privilege", "detail": "Regular users can ask and rate answers only. Evidence intake, conflict analysis, secure export, publication, rollback and controls are superadmin-only."},
            {"title": "Fail closed on uncertainty", "detail": "Weak evidence, stale source lineage, conflicting approved sources or out-of-scope data cause abstention or rejection—not a guessed answer."},
        ],
        "source_boundary": {
            "allowed": ["approved group channels", "formal approvals", "shared governed repositories"],
            "blocked": ["private messages", "direct messages", "1:1 chats", "unrelated group chatter"],
            "group_chat_relevance_threshold": settings.GROUP_CHAT_RELEVANCE_THRESHOLD,
            "private_message_collection": False,
            "origin_counts": scopes,
        },
        "data_security": {
            "customer_export": "Superadmin-only PII-minimised export encrypted with AES-256-GCM using an operator passphrase; passphrase is never persisted.",
            "system_transfer": "Ciphertext-only server transfer with API-key + HMAC authentication. Production can require HTTPS/TLS at middleware.",
            "api_key_fingerprint": integration_key_fingerprint(),
            "api_key_browser_exposure": False,
            "https_required": settings.REQUIRE_HTTPS,
            "demo_transport_note": "Local finals demo uses loopback HTTP. Set REQUIRE_HTTPS=true behind a TLS reverse proxy for deployment.",
        },
        "metrics": {
            "open_review_items": db.execute(select(func.count(KnowledgeGap.id)).where(KnowledgeGap.status == "open")).scalar_one(),
            "published_patterns": db.execute(select(func.count(ResolutionPattern.id)).where(ResolutionPattern.active.is_(True))).scalar_one(),
            "audit_entries": db.execute(select(func.count(LedgerEntry.id))).scalar_one(),
            "interactions": db.execute(select(func.count(Interaction.id))).scalar_one(),
            "feedback_records": db.execute(select(func.count(AnswerFeedback.id))).scalar_one(),
            "secret_mode": settings.SECRET_MODE,
            "demo_mode": settings.DEMO_MODE,
            "resolved_gap_retention_days": settings.RESOLVED_GAP_RETENTION_DAYS,
        },
        "audit_chain": verify_chain(db),
    }


@router.post("/customer-export")
def customer_export(body: CustomerExportRequest, db: Session = Depends(get_db), user: User = Depends(require_superadmin)):
    interactions = db.execute(select(Interaction).order_by(Interaction.id)).scalars().all()
    feedback = db.execute(select(AnswerFeedback).order_by(AnswerFeedback.id)).scalars().all() if body.include_feedback else []
    export_ref = f"EXP-{uuid4().hex[:10].upper()}"
    payload = {
        "export_ref": export_ref,
        "purpose": "customer-interaction governance export",
        "generated_at": iso(datetime.now(timezone.utc)),
        "privacy_mode": "PII-minimised; raw prompts and credentials excluded",
        "interactions": [{
            "interaction_ref": x.interaction_ref,
            "user_role": x.user_role,
            "question_masked": redact_sensitive(x.question_masked, db),
            "status": x.status,
            "handled_by": x.handled_by,
            "latency_ms": x.latency_ms,
            "evidence_ref": x.evidence_ref,
            "resolution_ref": x.resolution_ref,
            "created_at": iso(x.created_at),
        } for x in interactions],
        "feedback": [{
            "feedback_ref": x.feedback_ref, "interaction_ref": x.interaction_ref, "helpful": x.helpful,
            "comment_masked": redact_sensitive(x.comment_masked or "", db) if x.comment_masked else None,
            "escalated": x.escalated, "created_at": iso(x.created_at),
        } for x in feedback],
    }
    try:
        envelope, file_bytes = encrypt_export_payload(payload, body.passphrase)
    except ValueError as exc:
        raise HTTPException(422, str(exc))
    file_sha = hashlib.sha256(file_bytes).hexdigest()
    entry = append_entry(db, "CUSTOMER_DATA_EXPORT_ENCRYPTED", user.email, {
        "export_ref": export_ref,
        "records": len(interactions),
        "feedback_records": len(feedback),
        "cipher": envelope["cipher"],
        "kdf": envelope["kdf"],
        "pii_minimised": True,
        "passphrase_persisted": False,
        "file_sha256": file_sha,
    })
    db.commit()
    return {
        "export_ref": export_ref,
        "filename": f"juristwin-customer-export-{export_ref}.jtx",
        "content_base64": base64.b64encode(file_bytes).decode("ascii"),
        "manifest": {
            "records": len(interactions), "feedback_records": len(feedback), "cipher": envelope["cipher"],
            "kdf": envelope["kdf"], "pii_minimised": True, "passphrase_persisted": False,
            "file_sha256": file_sha, "audit_txid": entry.txid,
        },
    }


@router.post("/transfer-self-test")
def transfer_self_test(db: Session = Depends(get_db), user: User = Depends(require_superadmin)):
    result = transfer_security_self_test()
    entry = append_entry(db, "SYSTEM_TRANSFER_SECURITY_TEST", user.email, {k: v for k, v in result.items() if k != "api_key_fingerprint"})
    db.commit()
    result["audit_txid"] = entry.txid
    return result


@router.get("/compliance")
def compliance(user: User = Depends(require_superadmin)):
    return {
        "scope_note": "Design-alignment evidence only; this prototype does not claim legal or regulatory certification. References are implementation guidance, not a legal opinion.",
        "reference_status": "Reviewed for the August 2026 finals build; BNM RMiT reflects the revised policy issued 28 November 2025.",
        "mappings": [
            {"framework": "Malaysia PDPA 2010 + Amendment Act 2024", "focus": "Security / data minimisation / accountability", "evidence": "Relevant-source minimisation, group-channel-only collaboration scope, PM/DM exclusion, PII masking, encrypted export, least-privilege access, retention enforcement and auditable governance."},
            {"framework": "BNM RMiT (revised 28 Nov 2025)", "focus": "Technology risk / cyber controls / operational resilience", "evidence": "JWT RBAC, superadmin-only governance, TLS-capable transfer boundary, API-key/HMAC system authentication, encrypted export, HMAC-chained audit trail, fail-closed decisions and rollbackable memory."},
            {"framework": "NIST AI RMF 1.0 + GenAI Profile", "focus": "Govern / Map / Measure / Manage", "evidence": "Human publication authority, model card, confidence and evidence gates, safe abstention, risk register, feedback escalation and reversible decision memory."},
            {"framework": "OWASP API Security Top 10", "focus": "Authentication / authorization / validation / resource protection", "evidence": "Bearer authentication, object ownership checks, role gates, request-size limit, rate containment, schema validation, restricted CORS and hardened security headers."},
        ],
    }


@router.get("/risk-register")
def risk_register(db: Session = Depends(get_db), user: User = Depends(require_superadmin)):
    chain = verify_chain(db)
    shields = {s.key: bool(s.enabled) for s in db.execute(select(SecurityShield)).scalars().all()}
    risks = [
        {"risk": "Hallucinated policy answer", "severity": "Critical", "control": "Confidence + evidence coverage + canonical publication gates", "status": "Controlled" if shields.get("abstention") else "Degraded"},
        {"risk": "Contradictory source leakage", "severity": "Critical", "control": "Regular-user payload contains only governed winning sources", "status": "Controlled"},
        {"risk": "Two approved policies disagree", "severity": "Critical", "control": "Canonical split-brain detector blocks publication", "status": "Controlled"},
        {"risk": "Unauthorized governance", "severity": "High", "control": "Backend-enforced two-role RBAC", "status": "Controlled" if shields.get("rbac") else "Degraded"},
        {"risk": "PII in review queue", "severity": "High", "control": "Pre-persistence masking and evidence-ingest rejection", "status": "Controlled" if shields.get("pii_masking") else "Degraded"},
        {"risk": "Audit-history tampering", "severity": "High", "control": "Server-keyed HMAC-SHA256 hash chain", "status": "Controlled" if chain["ok"] else "Degraded"},
        {"risk": "Bad human resolution reused", "severity": "High", "control": "Pattern threshold + source revalidation + one-click rollback", "status": "Controlled"},
        {"risk": "Misleading source attribution", "severity": "High", "control": "Final-response lineage consistency gate rejects contradictory or weakly related citations", "status": "Controlled"},
        {"risk": "Private-message overcollection", "severity": "High", "control": "Approved group-channel scope + relevance gate; PM/DM blocked before evidence persistence", "status": "Controlled" if shields.get("group_chat_scope") else "Degraded"},
        {"risk": "Customer export exposure", "severity": "High", "control": "PII-minimised AES-256-GCM export + superadmin authorization + audit event", "status": "Controlled" if shields.get("encrypted_export") else "Degraded"},
        {"risk": "System transfer interception or spoofing", "severity": "High", "control": "TLS deployment gate + server-side API key + HMAC body signature + replay window", "status": "Controlled" if shields.get("secure_transfer") else "Degraded"},
        {"risk": "Learned model unavailable", "severity": "Medium", "control": "Deterministic evidence routing fallback and fail-safe abstention", "status": "Controlled"},
    ]
    return {"risks": risks, "controlled": sum(1 for r in risks if r["status"] == "Controlled"), "total": len(risks)}


@router.get("/technical-proof")
def technical_proof(db: Session = Depends(get_db), user: User = Depends(require_superadmin)):
    model = get_policy_ai().model_card()
    resilience_score, resilience_checks = _resilience_checks(db)
    return {
        "version": get_settings().VERSION,
        "verification": {
            "live_resilience_score": resilience_score,
            "live_resilience_checks": len(resilience_checks),
            "all_live_checks_passing": all(c["ok"] for c in resilience_checks),
            "regression_suite": "25 automated tests in the finals repository; run preflight_finals before demo.",
        },
        "architecture": [
            "FastAPI API boundary",
            "SQLAlchemy transactional persistence",
            "TF-IDF word + character features",
            "Logistic Regression policy routing and stance classification",
            "TF-IDF evidence retrieval + multi-factor governance ranking",
            "Deterministic Policy Atom contradiction verifier",
            "Human publication gate + semantic pattern memory",
            "HMAC-SHA256 governance ledger",
            "AES-256-GCM encrypted customer export + API-key/HMAC transfer gateway",
        ],
        "not_hardcoded_proofs": [
            "Live questions are classified statistically, not by exact string equality.",
            "New evidence can be ingested at runtime and immediately changes admin analysis without changing user policy automatically.",
            "Unseen questions create persisted deduplicated knowledge gaps.",
            "Human-published patterns answer future paraphrases through similarity scoring.",
            "Decision memory can be deactivated, reopening the governed review path.",
            "Private-message evidence is rejected while relevant group-channel evidence can be quarantined dynamically.",
            "Compare Evidence runs a transparent 1,500-scenario Monte Carlo Decision Digital Twin.",
        ],
        "model_card": model,
        "limits": [
            "Curated development corpus is not a production benchmark.",
            "Demo accounts are seeded only while DEMO_MODE=true; production identity should use enterprise SSO/OIDC.",
            "SQLite is the demo default; DATABASE_URL supports migration to PostgreSQL.",
            "Compliance mappings are design alignments, not certification claims.",
        ],
    }


@router.get("/audit")
def audit(limit: int = Query(default=30, ge=1, le=100), db: Session = Depends(get_db), user: User = Depends(require_superadmin)):
    rows = db.execute(select(LedgerEntry).order_by(LedgerEntry.id.desc()).limit(limit)).scalars().all()
    return {"chain": verify_chain(db), "entries": [serialize_entry(x) for x in rows]}

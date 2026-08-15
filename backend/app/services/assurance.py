from __future__ import annotations
import hashlib
import hmac
import json
from datetime import datetime, timezone
from sqlalchemy import select, func
from sqlalchemy.orm import Session

from ..db.models import (
    Approval, Conflict, CustomerCase, DecisionContract, DecisionVersion, Evidence,
    Integration, LedgerEntry, LiveChallenge, SecurityAlert, SecurityShield, Simulation,
)
from .common import loads, iso
from .ledger import verify_chain, serialize_entry
from .policy_reasoner import extract_policy_atoms, compare_policy_atoms
from .impact_graph import build_impact_graph
from .twin_engine import serialize_sim
from ..core.config import get_settings


def _canonical(db: Session, rule_key: str):
    rows = db.execute(
        select(Evidence).where(Evidence.rule_key == rule_key, Evidence.approved.is_(True), Evidence.superseded.is_(False))
        .order_by(Evidence.authority_level.desc(), Evidence.id.desc())
    ).scalars().all()
    return rows[0] if rows else None


def governance_gate(db: Session, conflict_ref: str) -> dict:
    c = db.execute(select(Conflict).where(Conflict.conflict_ref == conflict_ref)).scalar_one_or_none()
    if not c:
        return {"status":"BLOCKED", "score":0, "checks":[], "reason":"Conflict not found"}
    canonical = _canonical(db, c.rule_key)
    sim = db.execute(select(Simulation).where(Simulation.conflict_ref == conflict_ref).order_by(Simulation.id.desc())).scalars().first()
    sim_payload = serialize_sim(sim) if sim else None
    certificate = (sim_payload or {}).get("analysis", {}).get("decision_certificate", {})
    chain = verify_chain(db)
    alerts = db.execute(select(func.count(SecurityAlert.id)).where(SecurityAlert.status == "open", SecurityAlert.severity.in_(["Critical", "High"]))).scalar_one()
    cases = db.execute(select(func.count(CustomerCase.id)).where(CustomerCase.conflict_ref == conflict_ref)).scalar_one()

    checks = [
        {"key":"authority", "label":"Canonical authority", "ok":bool(canonical and canonical.authority_level >= 4), "detail":f"{canonical.authority if canonical else 'none'} · level {canonical.authority_level if canonical else 0}"},
        {"key":"impact", "label":"Impact is explainable", "ok":cases == c.affected_customers and cases > 0, "detail":f"{cases} operational cases reconcile to conflict blast radius"},
        {"key":"simulation", "label":"Decision robustness", "ok":bool(certificate and certificate.get('status') == 'ROBUST'), "detail":f"{certificate.get('sensitivity_stability_pct','—')}% sensitivity stability · p10 fit {certificate.get('worst_case_fit_p10','—')}%"},
        {"key":"ledger", "label":"Ledger integrity", "ok":bool(chain.get('ok')), "detail":f"{chain.get('entries',0)} chained events verified"},
        {"key":"security", "label":"No unresolved critical security block", "ok":alerts == 0, "detail":f"{alerts} open High/Critical alerts"},
    ]
    passed = sum(1 for x in checks if x["ok"])
    score = round(100*passed/len(checks))
    return {
        "conflict_ref": conflict_ref,
        "status": "PASS" if passed == len(checks) else "REVIEW",
        "score": score,
        "checks": checks,
        "publish_policy": "All gates should pass before production rollout; finals demo retains explicit human approval authority.",
    }


def invariant_report(db: Session) -> dict:
    chain = verify_chain(db)
    active_decisions = db.execute(select(DecisionContract).where(DecisionContract.status == "active")).scalars().all()
    duplicates = {}
    for d in active_decisions:
        duplicates[d.rule_key] = duplicates.get(d.rule_key, 0) + 1
    duplicate_domains = [k for k,v in duplicates.items() if v > 1]
    approved_superseded = db.execute(select(func.count(Evidence.id)).where(Evidence.approved.is_(True), Evidence.superseded.is_(True), Evidence.status == "active")).scalar_one()
    protected_high = db.execute(select(func.count(CustomerCase.id)).where(CustomerCase.protected.is_(True), CustomerCase.risk_status.in_(["High","Critical"]))).scalar_one()
    dangling_cases = db.execute(select(func.count(CustomerCase.id)).where(CustomerCase.conflict_ref.is_not(None))).scalar_one()
    unresolved = db.execute(select(func.sum(Conflict.affected_customers)).where(Conflict.status == "unresolved")).scalar_one() or 0
    checks = [
        {"key":"ledger", "ok":bool(chain.get('ok')), "detail":"Ledger hash-chain verifies end-to-end"},
        {"key":"decision_uniqueness", "ok":not duplicate_domains, "detail":f"Duplicate active decision domains: {duplicate_domains or 'none'}"},
        {"key":"evidence_state", "ok":approved_superseded == 0, "detail":f"{approved_superseded} evidence rows are simultaneously active+approved+superseded"},
        {"key":"protected_risk", "ok":protected_high == 0, "detail":f"{protected_high} protected cases still carry High/Critical risk"},
        {"key":"blast_radius_reconciliation", "ok":dangling_cases <= unresolved, "detail":f"{dangling_cases} case links vs {unresolved} unresolved-conflict affected slots"},
    ]
    return {"status":"HEALTHY" if all(x['ok'] for x in checks) else "DEGRADED", "checks":checks}


def progressive_rollout_plan(db: Session, conflict_ref: str) -> dict:
    c = db.execute(select(Conflict).where(Conflict.conflict_ref == conflict_ref)).scalar_one_or_none()
    if not c:
        return {"status":"BLOCKED", "waves":[]}
    cases = db.execute(select(CustomerCase).where(CustomerCase.conflict_ref == conflict_ref).order_by(CustomerCase.case_ref)).scalars().all()
    # Stable, deterministic cohort assignment lets the plan be reproduced exactly.
    ranked = sorted(cases, key=lambda x: hashlib.sha256(x.case_ref.encode()).hexdigest())
    n = len(ranked)
    sizes = [max(1, round(n*.10)), max(1, round(n*.40)), n]
    labels = ["CANARY", "CONTROLLED", "FULL"]
    waves=[]
    prev=0
    for i,(label,end) in enumerate(zip(labels,sizes), start=1):
        cohort=ranked[prev:end] if i < 3 else ranked[prev:]
        prev=end
        waves.append({
            "wave": i, "name": label, "case_count": len(cohort),
            "sample_case_refs": [x.case_ref for x in cohort[:6]],
            "entry_criteria": "Prior wave passes complaint, duplicate-request and policy-alignment guardrails" if i>1 else "Governance gate PASS + human approval",
            "rollback_trigger": "Any critical security alert, ledger failure, >5pp complaint deterioration, or policy-alignment <90%",
        })
    return {
        "conflict_ref": conflict_ref,
        "strategy":"deterministic progressive delivery",
        "affected_cases": n,
        "waves": waves,
        "safety_model":"Canary → controlled cohort → full rollout with explicit rollback triggers",
    }


def decision_replay(db: Session, decision_ref: str) -> dict:
    d = db.execute(select(DecisionContract).where(DecisionContract.decision_ref == decision_ref)).scalar_one_or_none()
    if not d:
        return {"status":"NOT_FOUND", "decision_ref":decision_ref, "timeline":[]}
    entries = db.execute(select(LedgerEntry).where(LedgerEntry.decision_ref == decision_ref).order_by(LedgerEntry.id.asc())).scalars().all()
    versions = db.execute(select(DecisionVersion).where(DecisionVersion.decision_ref == decision_ref).order_by(DecisionVersion.id.asc())).scalars().all()
    timeline=[]
    for v in versions:
        timeline.append({"at":iso(v.created_at), "type":"VERSION", "label":f"Policy {v.version}", "actor":v.actor, "detail":v.rule_text, "status":v.status})
    for e in entries:
        timeline.append({"at":iso(e.created_at), "type":"LEDGER", "label":e.action.replace('_',' ').title(), "actor":e.actor, "detail":loads(e.payload_json,{}) , "txid":e.txid, "hash":e.entry_hash})
    timeline.sort(key=lambda x: x.get("at") or "")
    return {
        "status":"REPLAYABLE",
        "decision_ref":decision_ref,
        "current":{"version":d.version,"rule":d.approved_rule,"status":d.status,"approved_by":d.approved_by},
        "timeline":timeline,
        "chain":verify_chain(db),
        "replay_note":"State reconstruction is derived from version history plus append-only ledger events; no generated narrative is required.",
    }


def proof_pack(db: Session, conflict_ref: str = "CF-INCOME-001", decision_ref: str = "JT-084") -> dict:
    c = db.execute(select(Conflict).where(Conflict.conflict_ref == conflict_ref)).scalar_one_or_none()
    if not c:
        return {"status":"NOT_FOUND", "conflict_ref":conflict_ref}
    canonical = _canonical(db, c.rule_key)
    sim = db.execute(select(Simulation).where(Simulation.conflict_ref == conflict_ref).order_by(Simulation.id.desc())).scalars().first()
    approval = db.execute(select(Approval).where(Approval.conflict_ref == conflict_ref).order_by(Approval.id.desc())).scalars().first()
    decision = db.execute(select(DecisionContract).where(DecisionContract.decision_ref == decision_ref)).scalar_one_or_none()
    impact = build_impact_graph(db, c.rule_key, c.conflict_ref)
    canonical_atoms = extract_policy_atoms(canonical.body if canonical else "", c.rule_key)
    legacy = db.execute(select(Evidence).where(Evidence.rule_key == c.rule_key, Evidence.superseded.is_(False)).order_by(Evidence.authority_level.asc())).scalars().first()
    comparison = compare_policy_atoms(canonical_atoms, extract_policy_atoms(legacy.body if legacy else "", c.rule_key)) if legacy else {}
    ledger = verify_chain(db)
    entries = db.execute(select(LedgerEntry).order_by(LedgerEntry.id.asc())).scalars().all()
    relevant = [serialize_entry(e) for e in entries if (e.decision_ref == decision_ref or conflict_ref in e.payload_json or (canonical and canonical.evidence_ref in e.payload_json))]
    gates = governance_gate(db, conflict_ref)
    invariants = invariant_report(db)
    integrations = db.execute(select(Integration).order_by(Integration.id)).scalars().all()
    payload = {
        "format":"JurisTwin Decision Assurance Proof Pack v4",
        "generated_at":datetime.now(timezone.utc).isoformat(),
        "subject":{"conflict_ref":conflict_ref,"decision_ref":decision_ref if decision else None,"rule_key":c.rule_key},
        "conflict":{"name":c.name,"severity":c.severity,"status":c.status,"confidence":c.confidence,"root_cause":c.root_cause},
        "canonical_evidence": None if not canonical else {"evidence_ref":canonical.evidence_ref,"source":canonical.source,"authority":canonical.authority,"authority_level":canonical.authority_level,"version":canonical.version,"body":canonical.body},
        "reasoning":{"canonical_atoms":canonical_atoms,"legacy_comparison":comparison},
        "impact":{"algorithm":impact.get('algorithm'),"affected_cases":impact.get('affected_cases'),"affected_systems":impact.get('affected_systems'),"reachable_nodes":impact.get('reachable_nodes'),"sample_paths":impact.get('sample_paths',[])[:5]},
        "simulation":serialize_sim(sim) if sim else None,
        "approval":None if not approval else {"approval_ref":approval.approval_ref,"status":approval.status,"selected_option":approval.selected_option,"requested_by":approval.requested_by,"approved_by":approval.approved_by},
        "decision":None if not decision else {"decision_ref":decision.decision_ref,"version":decision.version,"status":decision.status,"approved_rule":decision.approved_rule,"approved_by":decision.approved_by,"effective_at":iso(decision.effective_at)},
        "governance_gate":gates,
        "invariants":invariants,
        "ledger":{"verified":bool(ledger.get('ok')),"entries":ledger.get('entries'),"head_hash":ledger.get('head_hash'),"relevant_events":relevant},
        "integration_posture":{"connected":sum(1 for i in integrations if i.status=='connected'),"total":len(integrations),"real_ingress_contract":"HMAC-SHA256 signed webhook + replay protection"},
        "claims_boundary":"Prototype coefficients and demo adapters are explicitly labelled. Proof Pack certifies traceability, governance and runtime integrity—not statistical model accuracy or vendor production connectivity.",
    }
    canonical_json=json.dumps(payload,sort_keys=True,separators=(',',':'),default=str)
    digest=hashlib.sha256(canonical_json.encode()).hexdigest()
    settings=get_settings()
    signature=hmac.new(settings.PROOF_SIGNING_SECRET.encode(),digest.encode(),hashlib.sha256).hexdigest()
    payload["proof"]={
        "digest_algorithm":"SHA-256",
        "signature_algorithm":"HMAC-SHA256",
        "bundle_digest":digest,
        "signature":signature,
        "key_id":"juristwin-assurance-local-v4",
        "verification":"Re-serialize all fields except status/proof with sorted JSON keys, SHA-256 hash the UTF-8 bytes, then verify HMAC-SHA256 over the hex digest.",
    }
    payload["status"]="ASSURED" if gates.get('status')=='PASS' and invariants.get('status')=='HEALTHY' and ledger.get('ok') else "REVIEW"
    return payload


def verify_proof_signature(digest: str, signature: str) -> dict:
    settings=get_settings()
    expected=hmac.new(settings.PROOF_SIGNING_SECRET.encode(),digest.encode(),hashlib.sha256).hexdigest()
    valid=bool(digest and signature and hmac.compare_digest(expected,signature))
    return {
        "valid":valid,
        "digest":digest,
        "signature_algorithm":"HMAC-SHA256",
        "key_id":"juristwin-assurance-local-v4",
        "verification_boundary":"Finals/local signing key. Production target: managed KMS/HSM asymmetric signing.",
    }

from uuid import uuid4
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session
from ..db.database import get_db
from ..db.models import Approval, Conflict, Simulation, DecisionContract, DecisionVersion, Evidence, CustomerCase, CaseEvent, User
from ..core.security import current_user, require_roles
from ..schemas import SubmitApprovalRequest, ApprovalDecisionRequest
from ..services.common import loads, dumps, iso, utcnow
from ..services.ledger import append_entry
from ..services.assurance import governance_gate

router = APIRouter(prefix="/approvals", tags=["approvals"])


RESOLUTION_PROFILES = {
    "income_document_rule": {
        "decision_ref": "JT-084",
        "approved_rule": "Gig workers may submit verified bank statements as acceptable income evidence.",
        "approved_by": "Product Owner + Functional Lead",
        "effective_at": datetime(2026, 7, 24, tzinfo=timezone.utc),
        "supersedes": "Payslips-only requirement (v3.0)",
        "legacy_claims": {"payslips_required", "qa_outdated"},
        "canonical_claim": "bank_statement_accepted",
        "version": "v4.1",
        "case_ref": "JT-2026-084",
        "affected": {"applications": 27, "rejected_cases": 1, "qa_tests": 8, "tasks": 3, "documents": 2, "officers_notified": 4},
        "propagation": {"rejected_cases": 1, "qa_tests": 8, "documents": 3, "officers_notified": 4},
        "versions": [
            ("v3.0", "Income verification requires three months of payslips.", "legacy_requirement", "Functional Lead", "historical", {"source":"FSD v3.0"}),
            ("v4.0", "Bank statements may be accepted in place of payslips for approved gig-worker waivers.", "waiver_authorized", "Product Owner", "historical", {"source":"Outlook Approval"}),
            ("v4.1", None, "complete_process_alignment", None, "active", {}),
        ],
        "event": "Bank statements accepted; legacy payslip-only instruction superseded.",
    },
    "loan_restructure_rule": {
        "decision_ref": "JT-RESTRUCTURE-002",
        "approved_rule": "Use the Risk Committee v5.1 restructuring threshold: delegated approval requires risk score 60 or below plus affordability review.",
        "approved_by": "Risk Committee + Credit Operations",
        "effective_at": datetime(2026, 7, 25, tzinfo=timezone.utc),
        "supersedes": "Legacy restructuring threshold of 70 (v4.3)",
        "legacy_claims": {"risk_threshold_70"},
        "canonical_claim": "risk_threshold_60",
        "version": "v5.2",
        "case_ref": "JT-2026-112",
        "affected": {"applications": 11, "rejected_cases": 0, "qa_tests": 14, "tasks": 2, "documents": 2, "officers_notified": 3},
        "propagation": {"rejected_cases": 0, "qa_tests": 14, "documents": 2, "officers_notified": 3},
        "versions": [
            ("v4.3", "Legacy desk guidance allows restructuring approval up to risk score 70.", "legacy_threshold", "Credit Operations", "historical", {"source":"Legacy Restructuring Desk Guide"}),
            ("v5.1", "Risk Committee approval sets the delegated threshold at risk score 60 or below with affordability review.", "risk_committee_approval", "Risk Committee", "historical", {"source":"Loan Restructuring SOP"}),
            ("v5.2", None, "threshold_and_case_recalculation", None, "active", {}),
        ],
        "event": "Risk threshold aligned to 60; exposed restructuring cases recalculated.",
    },
    "notification_deadline": {
        "decision_ref": "JT-NOTIFY-003",
        "approved_rule": "Use a three business-day notification deadline for adverse customer decisions across scheduler and frontline guidance.",
        "approved_by": "Compliance Manager + Operations Lead",
        "effective_at": datetime(2026, 7, 26, tzinfo=timezone.utc),
        "supersedes": "Three-calendar-day legacy notification procedure (v1.7)",
        "legacy_claims": {"calendar_days_3", "legacy_instruction"},
        "canonical_claim": "business_days_3",
        "version": "v2.2",
        "case_ref": "JT-2026-123",
        "affected": {"applications": 6, "rejected_cases": 0, "qa_tests": 5, "tasks": 1, "documents": 2, "officers_notified": 2},
        "propagation": {"rejected_cases": 0, "qa_tests": 5, "documents": 2, "officers_notified": 2},
        "versions": [
            ("v1.7", "Customer notifications must be sent within three calendar days.", "legacy_calendar_sla", "Operations", "historical", {"source":"Legacy Notification Procedure"}),
            ("v2.1", "Compliance approved a three business-day notification deadline for adverse decisions.", "compliance_approval", "Compliance Manager", "historical", {"source":"Customer Notification SLA Approval"}),
            ("v2.2", None, "sla_and_scheduler_alignment", None, "active", {}),
        ],
        "event": "Notification SLA aligned to three business days across scheduler and operations.",
    },
}


def serialize(a: Approval):
    return {"approval_ref": a.approval_ref, "sim_ref": a.sim_ref, "conflict_ref": a.conflict_ref, "selected_option": a.selected_option, "status": a.status, "requested_by": a.requested_by, "approved_by": a.approved_by, "comments": a.comments, "created_at": iso(a.created_at), "decided_at": iso(a.decided_at)}


def _profile(c: Conflict) -> dict:
    p = RESOLUTION_PROFILES.get(c.rule_key)
    if not p:
        raise HTTPException(409, f"No governed resolution profile is configured for rule domain {c.rule_key}")
    return p


@router.get("")
def list_approvals(db: Session = Depends(get_db), user: User = Depends(current_user)):
    return [serialize(a) for a in db.execute(select(Approval).order_by(Approval.id.desc())).scalars().all()]


@router.get("/{ref}")
def get_approval(ref: str, db: Session = Depends(get_db), user: User = Depends(current_user)):
    a = db.execute(select(Approval).where(Approval.approval_ref == ref)).scalar_one_or_none()
    if not a: raise HTTPException(404, "Approval not found")
    return serialize(a)


@router.post("/simulation/{sim_ref}/submit")
def submit(sim_ref: str, body: SubmitApprovalRequest, db: Session = Depends(get_db), user: User = Depends(current_user)):
    sim = db.execute(select(Simulation).where(Simulation.sim_ref == sim_ref)).scalar_one_or_none()
    if not sim: raise HTTPException(404, "Simulation not found")
    option = (body.selected_option or sim.recommended_option).upper()
    if option not in {"A", "B", "C"}: raise HTTPException(400, "selected_option must be A, B or C")
    existing = db.execute(select(Approval).where(Approval.sim_ref == sim_ref, Approval.status == "pending")).scalar_one_or_none()
    if existing: return serialize(existing)
    a = Approval(approval_ref=f"APR-{uuid4().hex[:6].upper()}", sim_ref=sim_ref, conflict_ref=sim.conflict_ref, selected_option=option, status="pending", requested_by=user.email, comments=body.comments)
    db.add(a)
    append_entry(db, "DECISION_PROPOSAL_CREATED", user.email, {"approval_ref": a.approval_ref, "simulation": sim_ref, "selected_option": option, "conflict_ref": sim.conflict_ref})
    db.commit(); db.refresh(a)
    return serialize(a)


@router.post("/{ref}/approve")
def approve(ref: str, body: ApprovalDecisionRequest, db: Session = Depends(get_db), user: User = Depends(require_roles("manager", "compliance_manager", "product_owner"))):
    a = db.execute(select(Approval).where(Approval.approval_ref == ref)).scalar_one_or_none()
    if not a: raise HTTPException(404, "Approval not found")
    if a.status == "approved":
        contract = db.execute(select(DecisionContract).where(DecisionContract.source_approval_ref == a.approval_ref)).scalar_one_or_none()
        return {"approval": serialize(a), "decision_contract": serialize_contract(contract) if contract else None, "idempotent": True}
    if a.status != "pending": raise HTTPException(409, f"Approval is {a.status}")
    if a.selected_option != "C": raise HTTPException(400, "Governed publication requires the complete-process Option C")

    gate = governance_gate(db, a.conflict_ref)
    if gate.get("status") != "PASS":
        failed=[x.get("label") for x in gate.get("checks",[]) if not x.get("ok")]
        raise HTTPException(409, detail={"message":"Decision publication blocked by JurisTwin Governance Gate", "gate_score":gate.get("score"), "failed_checks":failed})

    c = db.execute(select(Conflict).where(Conflict.conflict_ref == a.conflict_ref)).scalar_one()
    profile = _profile(c)
    a.status = "approved"; a.approved_by = user.email; a.comments = body.comments or a.comments; a.decided_at = utcnow()
    c.status = "resolved"; c.resolved_at = utcnow()

    # Supersede only the known stale evidence for the selected policy domain. Canonical evidence
    # stays intact and historical rows remain replayable.
    legacy = db.execute(select(Evidence).where(Evidence.rule_key == c.rule_key)).scalars().all()
    for e in legacy:
        if e.claim in profile["legacy_claims"]:
            e.superseded = True
            e.status = "superseded"

    decision_ref = profile["decision_ref"]
    contract = db.execute(select(DecisionContract).where(DecisionContract.decision_ref == decision_ref)).scalar_one_or_none()
    if not contract:
        cases = db.execute(select(CustomerCase).where(CustomerCase.conflict_ref == c.conflict_ref)).scalars().all()
        affected = dict(profile["affected"])
        affected["applications"] = len(cases)
        contract = DecisionContract(
            decision_ref=decision_ref, rule_key=c.rule_key, approved_rule=profile["approved_rule"],
            approved_by=profile["approved_by"], effective_at=profile["effective_at"], supersedes=profile["supersedes"],
            affected_json=dumps(affected), status="active", version=profile["version"], source_approval_ref=a.approval_ref,
        )
        db.add(contract); db.flush()
        for version, text, change_type, actor, status, metadata in profile["versions"]:
            rule_text = text or profile["approved_rule"]
            db.add(DecisionVersion(
                decision_ref=decision_ref, version=version, rule_text=rule_text, change_type=change_type,
                actor=actor or user.email, status=status,
                metadata_json=dumps({**metadata, **({"approval_ref":a.approval_ref} if status == "active" else {})}),
            ))
        db.add(Evidence(
            evidence_ref=f"EV-DECISION-{decision_ref}", source="Decision Ledger", title=f"Decision {decision_ref}", body=contract.approved_rule,
            rule_key=c.rule_key, claim=profile["canonical_claim"], authority="Consensus Ledger Protocol", authority_level=6,
            version=profile["version"], status="active", sensitivity="confidential", case_ref=profile["case_ref"], approved=True, superseded=False,
            metadata_json=dumps({"registry_id": decision_ref, "approval_ref": a.approval_ref, "conflict_ref": c.conflict_ref}),
        ))
    else:
        cases = db.execute(select(CustomerCase).where(CustomerCase.conflict_ref == c.conflict_ref)).scalars().all()

    # Propagate the chosen policy outcome to the complete affected cohort.
    target_delay = 1.1
    sim = db.execute(select(Simulation).where(Simulation.sim_ref == a.sim_ref)).scalar_one_or_none()
    if sim:
        payload = loads(sim.options_json, [])
        option_rows = payload.get("options", []) if isinstance(payload, dict) else payload
        selected = next((x for x in option_rows if isinstance(x, dict) and x.get("key") == "C"), None)
        if selected:
            target_delay = float(selected.get("predicted_delay_days", target_delay))
    for case in cases:
        case.risk_status = "Low"
        case.pending_days = min(float(case.pending_days or target_delay), target_delay)
        case.current_blocker = None
        case.protected = True
        if case.case_ref == profile["case_ref"]:
            db.add(CaseEvent(case_id=case.id, source="Decision Ledger", title="Approved Resolution Published", description=f"{decision_ref}: {profile['event']}", event_time=utcnow(), severity="success"))

    append_entry(db, "DECISION_APPROVED", user.email, {"approval_ref": a.approval_ref, "decision_ref": decision_ref, "conflict_ref": c.conflict_ref, "selected_option": "C", "governance_gate_score": gate.get("score"), "governance_gate":"PASS"}, decision_ref)
    propagation = {"applications_reviewed": len(cases), **profile["propagation"]}
    append_entry(db, "DECISION_PROPAGATED", "sentinel-orchestrator", propagation, decision_ref)
    db.commit(); db.refresh(a); db.refresh(contract)
    return {
        "approval": serialize(a),
        "decision_contract": serialize_contract(contract),
        "propagation": {"cases": len(cases), **profile["propagation"]},
        "governance_gate": gate,
    }


@router.post("/{ref}/request-changes")
def request_changes(ref: str, body: ApprovalDecisionRequest, db: Session = Depends(get_db), user: User = Depends(require_roles("manager", "compliance_manager", "product_owner"))):
    a = db.execute(select(Approval).where(Approval.approval_ref == ref)).scalar_one_or_none()
    if not a: raise HTTPException(404, "Approval not found")
    if a.status != "pending": raise HTTPException(409, f"Approval is {a.status}")
    a.comments = body.comments or "Changes requested before final authorization"
    append_entry(db, "APPROVAL_CHANGES_REQUESTED", user.email, {"approval_ref": a.approval_ref, "comments": a.comments})
    db.commit(); db.refresh(a)
    return serialize(a)


@router.post("/{ref}/reject")
def reject(ref: str, body: ApprovalDecisionRequest, db: Session = Depends(get_db), user: User = Depends(require_roles("manager", "compliance_manager", "product_owner"))):
    a = db.execute(select(Approval).where(Approval.approval_ref == ref)).scalar_one_or_none()
    if not a: raise HTTPException(404, "Approval not found")
    if a.status != "pending": raise HTTPException(409, f"Approval is {a.status}")
    a.status = "rejected"; a.approved_by = user.email; a.comments = body.comments; a.decided_at = utcnow()
    append_entry(db, "DECISION_REJECTED", user.email, {"approval_ref": a.approval_ref, "comments": body.comments})
    db.commit(); db.refresh(a); return serialize(a)


def serialize_contract(d: DecisionContract | None):
    if not d: return None
    return {"decision_ref": d.decision_ref, "rule_key": d.rule_key, "approved_rule": d.approved_rule, "approved_by": d.approved_by, "effective_at": iso(d.effective_at), "supersedes": d.supersedes, "affected": loads(d.affected_json, {}), "status": d.status, "version": d.version, "source_approval_ref": d.source_approval_ref, "created_at": iso(d.created_at)}

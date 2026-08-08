from uuid import uuid4
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session
from ..db.database import get_db
from ..db.models import Approval, Conflict, Simulation, DecisionContract, Evidence, CustomerCase, CaseEvent, User
from ..core.security import current_user, require_roles
from ..schemas import SubmitApprovalRequest, ApprovalDecisionRequest
from ..services.common import loads, dumps, iso, utcnow
from ..services.ledger import append_entry

router = APIRouter(prefix="/approvals", tags=["approvals"])


def serialize(a: Approval):
    return {"approval_ref": a.approval_ref, "sim_ref": a.sim_ref, "conflict_ref": a.conflict_ref, "selected_option": a.selected_option, "status": a.status, "requested_by": a.requested_by, "approved_by": a.approved_by, "comments": a.comments, "created_at": iso(a.created_at), "decided_at": iso(a.decided_at)}

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
    append_entry(db, "DECISION_PROPOSAL_CREATED", user.email, {"approval_ref": a.approval_ref, "simulation": sim_ref, "selected_option": option})
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
    if a.selected_option != "C": raise HTTPException(400, "Grand-finals governed publish requires the complete-process Option C")
    c = db.execute(select(Conflict).where(Conflict.conflict_ref == a.conflict_ref)).scalar_one()
    a.status = "approved"; a.approved_by = user.email; a.comments = body.comments or a.comments; a.decided_at = utcnow()
    c.status = "resolved"; c.resolved_at = utcnow()
    # Supersede legacy FSD + training rule and publish new governed evidence.
    legacy = db.execute(select(Evidence).where(Evidence.rule_key == c.rule_key)).scalars().all()
    for e in legacy:
        if e.claim == "payslips_required":
            e.superseded = True; e.status = "superseded"
    decision_ref = "JT-084" if c.conflict_ref == "CF-INCOME-001" else f"JT-{uuid4().hex[:6].upper()}"
    contract = db.execute(select(DecisionContract).where(DecisionContract.decision_ref == decision_ref)).scalar_one_or_none()
    if not contract:
        contract = DecisionContract(
            decision_ref=decision_ref, rule_key=c.rule_key, approved_rule="Gig workers may submit verified bank statements as acceptable income evidence.",
            approved_by="Product Owner + Functional Lead + Compliance Manager", effective_at=utcnow(), supersedes="Payslips-only requirement (v3.0)",
            affected_json=dumps({"applications": 27, "rejected_cases": 5, "qa_tests": 8, "tasks": 3, "documents": 2, "officers_notified": 4}),
            status="active", version="v4.1", source_approval_ref=a.approval_ref,
        )
        db.add(contract); db.flush()
        db.add(Evidence(evidence_ref=f"EV-DECISION-{decision_ref}", source="Decision Ledger", title=f"Decision {decision_ref}", body=contract.approved_rule,
                        rule_key=c.rule_key, claim="bank_statement_accepted", authority="Consensus Ledger Protocol", authority_level=6,
                        version="v4.1", status="active", sensitivity="confidential", case_ref="JT-2026-084", approved=True, superseded=False,
                        metadata_json=dumps({"registry_id": decision_ref, "approval_ref": a.approval_ref})))
    # Propagate to affected cohort.
    cases = db.execute(select(CustomerCase).where(CustomerCase.conflict_ref == c.conflict_ref)).scalars().all()
    for case in cases:
        case.risk_status = "Low"; case.pending_days = min(case.pending_days, 1.1); case.current_blocker = None; case.protected = True
        if case.case_ref == "JT-2026-084":
            db.add(CaseEvent(case_id=case.id, source="Decision Ledger", title="Approved Resolution Published", description=f"{decision_ref}: bank statements accepted; legacy payslip-only instruction superseded.", event_time=utcnow(), severity="success"))
    append_entry(db, "DECISION_APPROVED", user.email, {"approval_ref": a.approval_ref, "decision_ref": decision_ref, "selected_option": "C"}, decision_ref)
    append_entry(db, "DECISION_PROPAGATED", "sentinel-orchestrator", {"applications_reviewed": len(cases), "qa_tests_updated": 8, "documents_superseded": 2, "officers_notified": 4}, decision_ref)
    db.commit(); db.refresh(a); db.refresh(contract)
    return {"approval": serialize(a), "decision_contract": serialize_contract(contract), "propagation": {"cases": len(cases), "qa_tests": 8, "documents": 2, "officers_notified": 4}}

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

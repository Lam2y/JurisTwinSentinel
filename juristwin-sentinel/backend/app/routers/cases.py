from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session
from ..db.database import get_db
from ..db.models import CustomerCase, CaseEvent, Evidence, Conflict, User
from ..core.security import current_user
from ..services.common import loads, iso
from ..services.memory import serialize_evidence
from ..services.conflict_engine import conflict_payload

router = APIRouter(prefix="/cases", tags=["cases"])


def can_view_case(user: User, case: CustomerCase):
    if user.role in {"manager", "compliance_manager", "product_owner"}: return True
    if user.role == "intern": return True
    assigned = set(loads(user.assigned_case_refs, []))
    return case.case_ref in assigned or case.owner_email == user.email

@router.get("")
def list_cases(db: Session = Depends(get_db), user: User = Depends(current_user)):
    cases = db.execute(select(CustomerCase).order_by(CustomerCase.id.asc())).scalars().all()
    cases = [c for c in cases if can_view_case(user, c)]
    return [{"case_ref": c.case_ref, "customer_name": c.customer_name if user.role != "intern" else "[REDACTED]", "customer_type": c.customer_type, "application_type": c.application_type, "status": c.status, "risk_status": c.risk_status, "sentiment": c.sentiment, "pending_days": c.pending_days, "conflict_ref": c.conflict_ref, "protected": c.protected} for c in cases]

@router.get("/{case_ref}")
def get_case(case_ref: str, db: Session = Depends(get_db), user: User = Depends(current_user)):
    case = db.execute(select(CustomerCase).where(CustomerCase.case_ref == case_ref)).scalar_one_or_none()
    if not case or not can_view_case(user, case): raise HTTPException(404, "Case not found")
    events = db.execute(select(CaseEvent).where(CaseEvent.case_id == case.id).order_by(CaseEvent.event_time.asc())).scalars().all()
    evidence = db.execute(select(Evidence).where(Evidence.case_ref == case_ref).order_by(Evidence.created_at.asc())).scalars().all()
    conflict = db.execute(select(Conflict).where(Conflict.conflict_ref == case.conflict_ref)).scalar_one_or_none() if case.conflict_ref else None
    return {
        "case": {"case_ref": case.case_ref, "customer_name": case.customer_name if user.role != "intern" else "[REDACTED]", "customer_type": case.customer_type, "application_type": case.application_type, "status": case.status, "risk_status": case.risk_status, "sentiment": case.sentiment, "pending_days": case.pending_days, "current_blocker": case.current_blocker, "protected": case.protected, "metadata": loads(case.metadata_json, {}) if user.role != "intern" else {}},
        "timeline": [{"source": e.source, "title": e.title, "description": e.description, "event_time": iso(e.event_time), "severity": e.severity} for e in events],
        "evidence": [serialize_evidence(e, user) for e in evidence],
        "conflict": conflict_payload(db, conflict) if conflict else None,
    }

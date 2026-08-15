from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session
from ..db.database import get_db
from ..db.models import Conflict, DecisionContract, SecurityAlert, User
from ..db.seed import reset_database
from ..core.security import current_user, require_roles

router = APIRouter(prefix="/demo", tags=["demo"])

@router.get("/story")
def story(user: User = Depends(current_user)):
    return {"steps": [
        {"step": 1, "key": "CONNECT", "title": "Connect", "route": "memory", "action": "Secure Enterprise Memory", "message": "Collect scattered evidence from enterprise systems and retrieve it by meaning with role-aware access."},
        {"step": 2, "key": "EXPOSE", "title": "Expose", "route": "conflict", "action": "Detect and cross-reference conflict", "message": "White-box conflict intelligence identifies exactly where sources disagree and which source has authority."},
        {"step": 3, "key": "SIMULATE", "title": "Simulate", "route": "twin", "action": "Run 1,500 stress scenarios", "message": "The decision twin tests possible interventions before anything reaches the customer."},
        {"step": 4, "key": "RECOMMEND", "title": "Recommend", "route": "twin", "action": "Issue robust decision certificate", "message": "JurisTwin recommends the option that remains defensible under uncertainty, sensitivity and Pareto checks."},
        {"step": 5, "key": "APPROVE", "title": "Approve", "route": "governance", "action": "Publish Decision JT-084", "message": "Human approval plus an enforced governance gate converts the recommendation into a version-controlled decision contract."},
        {"step": 6, "key": "PROTECT", "title": "Protect", "route": "bodyguard", "action": "Monitor, audit and restore", "message": "AI Bodyguard and the Decision Ledger protect the approved decision and preserve a replayable audit trail."},
    ], "operating_impact": {"applications_affected": 27, "rejected_cases_flagged": 1, "qa_tests_updated": 8, "documents_superseded": 3, "officers_notified": 4}}

@router.get("/status")
def status(db: Session = Depends(get_db), user: User = Depends(current_user)):
    conflict = db.execute(select(Conflict).where(Conflict.conflict_ref == "CF-INCOME-001")).scalar_one()
    contract = db.execute(select(DecisionContract).where(DecisionContract.decision_ref == "JT-084")).scalar_one_or_none()
    alert = db.execute(select(SecurityAlert).order_by(SecurityAlert.id.desc())).scalars().first()
    return {"conflict_status": conflict.status, "decision_published": bool(contract), "bodyguard_alert": alert.status if alert else None}

@router.post("/reset")
def reset(db: Session = Depends(get_db), user: User = Depends(require_roles("manager", "compliance_manager", "product_owner"))):
    reset_database(db)
    return {"ok": True, "message": "Grand Finals dataset reset to deterministic starting state."}

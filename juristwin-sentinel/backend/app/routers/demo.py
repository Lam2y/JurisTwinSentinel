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
        {"step": 1, "title": "Command Center", "route": "dashboard", "action": "Investigate Income-Document Conflict", "message": "Start with the company-wide signal, not a chatbot prompt."},
        {"step": 2, "title": "Case Workspace", "route": "case", "action": "Open Conflict Network Graph", "message": "Show one customer receiving two contradictory answers."},
        {"step": 3, "title": "Conflict Intelligence", "route": "conflict", "action": "Simulate Resolution Options", "message": "Trace exactly which source is approved, informal, outdated or operational."},
        {"step": 4, "title": "Decision Digital Twin", "route": "twin", "action": "Submit Scenario for Approval", "message": "Compare three futures before touching the live process."},
        {"step": 5, "title": "Approval", "route": "approval", "action": "Approve & Publish Resolution", "message": "Human approval converts AI advice into a governed decision contract."},
        {"step": 6, "title": "Decision Ledger", "route": "ledger", "action": "Verify Ledger", "message": "Prove the decision history is append-only and hash linked."},
        {"step": 7, "title": "AI Bodyguard", "route": "bodyguard", "action": "Simulate attack → Restore", "message": "Protect the approved rule after publication."},
    ]}

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

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session
from ..db.database import get_db
from ..db.models import SecurityAlert, DecisionContract, User
from ..core.security import current_user, require_roles
from ..services.bodyguard import simulate_incident, restore_alert, serialize_alert
from ..services.ledger import append_entry

router = APIRouter(prefix="/bodyguard", tags=["bodyguard"])

@router.get("/alerts")
def alerts(db: Session = Depends(get_db), user: User = Depends(current_user)):
    return [serialize_alert(a) for a in db.execute(select(SecurityAlert).order_by(SecurityAlert.id.desc())).scalars().all()]

@router.post("/simulate-attack")
def simulate(db: Session = Depends(get_db), user: User = Depends(require_roles("manager", "compliance_manager", "product_owner"))):
    contract = db.execute(select(DecisionContract).where(DecisionContract.decision_ref == "JT-084", DecisionContract.status == "active")).scalar_one_or_none()
    if not contract:
        raise HTTPException(409, "Publish Decision JT-084 before demonstrating post-decision Bodyguard protection")
    return simulate_incident(db)

@router.post("/alerts/{ref}/restore")
def restore(ref: str, db: Session = Depends(get_db), user: User = Depends(require_roles("manager", "compliance_manager", "product_owner"))):
    a = db.execute(select(SecurityAlert).where(SecurityAlert.alert_ref == ref)).scalar_one_or_none()
    if not a: raise HTTPException(404, "Alert not found")
    return restore_alert(db, a, user.email)

def _get_alert(db: Session, ref: str):
    a = db.execute(select(SecurityAlert).where(SecurityAlert.alert_ref == ref)).scalar_one_or_none()
    if not a: raise HTTPException(404, "Alert not found")
    return a

@router.post("/alerts/{ref}/revoke-access")
def revoke_access(ref: str, db: Session = Depends(get_db), user: User = Depends(require_roles("manager", "compliance_manager"))):
    a = _get_alert(db, ref)
    append_entry(db, "BODYGUARD_ACCESS_REVOKED", user.email, {"alert_ref": ref, "user_ref": a.user_ref, "document": a.document}, a.conflict_decision_ref)
    db.commit()
    return {"ok": True, "alert_ref": ref, "action": "access_revoked", "user_ref": a.user_ref}

@router.post("/alerts/{ref}/escalate")
def escalate(ref: str, db: Session = Depends(get_db), user: User = Depends(require_roles("manager", "compliance_manager", "product_owner"))):
    a = _get_alert(db, ref)
    append_entry(db, "BODYGUARD_ESCALATED", user.email, {"alert_ref": ref, "severity": a.severity, "destination": "Compliance Manager"}, a.conflict_decision_ref)
    db.commit()
    return {"ok": True, "alert_ref": ref, "action": "escalated", "destination": "Compliance Manager"}

@router.post("/alerts/{ref}/authorize-overwrite")
def authorize_overwrite(ref: str, db: Session = Depends(get_db), user: User = Depends(require_roles("manager", "compliance_manager", "product_owner"))):
    a = _get_alert(db, ref)
    a.status = "authorized_override"
    append_entry(db, "BODYGUARD_OVERRIDE_AUTHORIZED", user.email, {"alert_ref": ref, "document": a.document, "user_ref": a.user_ref}, a.conflict_decision_ref)
    db.commit(); db.refresh(a)
    return serialize_alert(a)


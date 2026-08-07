from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session
from ..db.database import get_db
from ..db.models import SecurityAlert, DecisionContract, User
from ..core.security import current_user, require_roles
from ..services.bodyguard import simulate_incident, restore_alert, serialize_alert

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

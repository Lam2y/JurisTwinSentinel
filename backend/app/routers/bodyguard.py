from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session
from ..db.database import get_db
from ..db.models import SecurityAlert, DecisionContract, User
from ..core.security import current_user, require_capability, require_roles
from ..schemas import BodyguardActionRequest
from ..services.bodyguard import simulate_incident, restore_alert, serialize_alert, review_alert, explanation, revoke_access, escalate_alert, authorize_override

router=APIRouter(prefix="/bodyguard",tags=["bodyguard"])

def _get(db,ref):
    a=db.execute(select(SecurityAlert).where(SecurityAlert.alert_ref==ref)).scalar_one_or_none()
    if not a:raise HTTPException(404,"Alert not found")
    return a

@router.get("/alerts")
def alerts(db:Session=Depends(get_db),user:User=Depends(current_user)):return [serialize_alert(a) for a in db.execute(select(SecurityAlert).order_by(SecurityAlert.id.desc())).scalars().all()]
@router.get("/alerts/{ref}")
def alert(ref:str,db:Session=Depends(get_db),user:User=Depends(current_user)):return serialize_alert(_get(db,ref))
@router.post("/simulate-attack")
def simulate(db:Session=Depends(get_db),user:User=Depends(require_roles("manager","compliance_manager","product_owner"))):
    contract=db.execute(select(DecisionContract).where(DecisionContract.decision_ref=="JT-084",DecisionContract.status=="active")).scalar_one_or_none()
    if not contract:raise HTTPException(409,"Publish Decision JT-084 before demonstrating post-decision Bodyguard protection")
    return simulate_incident(db)
@router.post("/alerts/{ref}/review")
def review(ref:str,db:Session=Depends(get_db),user:User=Depends(require_capability("can_review_bodyguard"))):return review_alert(db,_get(db,ref),user.email)
@router.post("/alerts/{ref}/explain")
def explain(ref:str,db:Session=Depends(get_db),user:User=Depends(current_user)):return explanation(db,_get(db,ref),user.email)
@router.post("/alerts/{ref}/revoke-access")
def revoke(ref:str,db:Session=Depends(get_db),user:User=Depends(require_capability("can_review_bodyguard"))):return revoke_access(db,_get(db,ref),user.email)
@router.post("/alerts/{ref}/escalate")
def escalate(ref:str,db:Session=Depends(get_db),user:User=Depends(require_capability("can_review_bodyguard"))):return escalate_alert(db,_get(db,ref),user.email)
@router.post("/alerts/{ref}/authorize-overwrite")
def override(ref:str,body:BodyguardActionRequest,db:Session=Depends(get_db),user:User=Depends(require_capability("can_override"))):
    try:return authorize_override(db,_get(db,ref),user.email,body.comments)
    except ValueError as e:raise HTTPException(409,str(e))
@router.post("/alerts/{ref}/restore")
def restore(ref:str,db:Session=Depends(get_db),user:User=Depends(require_capability("can_override"))):return restore_alert(db,_get(db,ref),user.email)

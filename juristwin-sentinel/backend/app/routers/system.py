from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import text, select
from sqlalchemy.orm import Session
from ..db.database import get_db
from ..core.security import current_user, require_roles
from ..db.models import User, RolePolicy, SecurityShield
from ..schemas import RolePolicyUpdate, ShieldUpdate
from ..services.common import loads, dumps, iso
from ..services.ledger import verify_chain, append_entry

router=APIRouter(prefix="/system",tags=["system"])

def role_ser(r):
    return {"role":r.role,"display_name":r.display_name,"description":r.description,"enabled":r.enabled,"max_sensitivity":r.max_sensitivity,"can_override":r.can_override,"can_modify_twin":r.can_modify_twin,"can_export_ledger":r.can_export_ledger,"can_review_bodyguard":r.can_review_bodyguard,"updated_by":r.updated_by,"updated_at":iso(r.updated_at)}
def shield_ser(s):
    return {"key":s.key,"name":s.name,"description":s.description,"enabled":s.enabled,"value":loads(s.value_json,{}),"updated_by":s.updated_by,"updated_at":iso(s.updated_at)}

@router.get("/health")
def health(db:Session=Depends(get_db)):
    db.execute(text("SELECT 1"));return {"status":"operational","database":"ok","decision_ledger":verify_chain(db)}

@router.get("/config")
def config(db:Session=Depends(get_db),user:User=Depends(current_user)):
    roles=db.execute(select(RolePolicy).order_by(RolePolicy.id)).scalars().all();shields=db.execute(select(SecurityShield).order_by(SecurityShield.id)).scalars().all()
    return {"rbac":[role_ser(r) for r in roles],"shields":[shield_ser(s) for s in shields],"retention":"7-Year Ledger Retention","mode":"Finalist Demo Environment","current_role":user.role}

@router.patch("/roles/{role}")
def update_role(role:str,body:RolePolicyUpdate,db:Session=Depends(get_db),user:User=Depends(require_roles("manager","compliance_manager"))):
    r=db.execute(select(RolePolicy).where(RolePolicy.role==role)).scalar_one_or_none()
    if not r: raise HTTPException(404,"Role policy not found")
    data=body.model_dump(exclude_none=True)
    if role==user.role and data.get("enabled") is False: raise HTTPException(400,"Cannot disable your own active role during this session")
    for k,v in data.items(): setattr(r,k,v)
    r.updated_by=user.email
    append_entry(db,"RBAC_POLICY_UPDATED",user.email,{"role":role,"changes":data})
    db.commit();db.refresh(r);return role_ser(r)

@router.patch("/shields/{key}")
def update_shield(key:str,body:ShieldUpdate,db:Session=Depends(get_db),user:User=Depends(require_roles("manager","compliance_manager"))):
    s=db.execute(select(SecurityShield).where(SecurityShield.key==key)).scalar_one_or_none()
    if not s: raise HTTPException(404,"Security shield not found")
    changes={}
    if body.enabled is not None: s.enabled=body.enabled;changes["enabled"]=body.enabled
    if body.value is not None: s.value_json=dumps(body.value);changes["value"]=body.value
    s.updated_by=user.email
    append_entry(db,"SECURITY_SHIELD_UPDATED",user.email,{"shield":key,"changes":changes})
    db.commit();db.refresh(s);return shield_ser(s)

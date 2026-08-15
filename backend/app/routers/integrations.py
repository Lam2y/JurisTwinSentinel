from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session
from ..db.database import get_db
from ..db.models import Integration, User
from ..core.security import current_user, require_roles
from ..schemas import IntegrationConfigRequest
from ..services.common import loads, dumps, iso, utcnow
from ..services.ledger import append_entry

router=APIRouter(prefix="/integrations",tags=["integrations"])

def _age(dt):
    if not dt:return "Never"
    now=utcnow(); d=now-dt if dt.tzinfo else now-dt.replace(tzinfo=timezone.utc); sec=max(0,int(d.total_seconds()))
    if sec<60:return "Real-time"
    if sec<3600:return f"{sec//60}m ago"
    if sec<86400:return f"{sec//3600}h ago"
    return f"{sec//86400}d ago"

def ser(i):
    d=loads(i.details_json,{})
    return {"key":i.key,"name":i.name,"kind":i.kind,"status":i.status,"object_count":i.object_count,"last_sync_at":iso(i.last_sync_at),"last_sync_label":"Real-time" if d.get("realtime") and i.status=="connected" else _age(i.last_sync_at),"shield_status":i.shield_status,"details":d}

def _get(db,key):
    i=db.execute(select(Integration).where(Integration.key==key)).scalar_one_or_none()
    if not i:raise HTTPException(404,"Integration not found")
    return i

@router.get("")
def list_integrations(db:Session=Depends(get_db),user:User=Depends(current_user)):
    return [ser(i) for i in db.execute(select(Integration).order_by(Integration.id.asc())).scalars().all()]

@router.get("/{key}")
def get_integration(key:str,db:Session=Depends(get_db),user:User=Depends(current_user)): return ser(_get(db,key))

@router.post("/{key}/sync")
def sync(key:str,db:Session=Depends(get_db),user:User=Depends(require_roles("manager","compliance_manager","product_owner"))):
    i=_get(db,key)
    if i.status!="connected": raise HTTPException(409,f"{i.name} is inactive. Connect it before syncing.")
    bump={"outlook":13,"teams":28,"gmail":9,"sharepoint":4,"onedrive":3,"clickup":6,"customer_core":2,"qa":1,"postgres":18,"vector":42}.get(key,1)
    d=loads(i.details_json,{}); before_errors=int(d.get("errors",0));i.object_count+=bump;i.last_sync_at=utcnow();d["errors"]=max(0,before_errors-1);d["last_batch"]=bump
    if d.get("errors",0)==0:d.pop("note",None)
    i.details_json=dumps(d)
    append_entry(db,"INTEGRATION_SYNC",user.email,{"integration":key,"new_objects":bump,"object_count":i.object_count,"errors_before":before_errors,"errors_after":d.get("errors",0)})
    db.commit();db.refresh(i);return ser(i)

@router.post("/{key}/connect")
def connect(key:str,body:IntegrationConfigRequest,db:Session=Depends(get_db),user:User=Depends(require_roles("manager","compliance_manager","product_owner"))):
    i=_get(db,key);d=loads(i.details_json,{})|body.config;i.status="connected";i.last_sync_at=utcnow();d["errors"]=0;d.pop("note",None)
    if i.object_count==0:i.object_count={"gmail":126,"outlook":20,"teams":20}.get(key,10)
    i.details_json=dumps(d);append_entry(db,"INTEGRATION_CONNECTED",user.email,{"integration":key,"configuration":body.config,"object_count":i.object_count});db.commit();db.refresh(i);return ser(i)

@router.post("/{key}/pause")
def pause(key:str,db:Session=Depends(get_db),user:User=Depends(require_roles("manager","compliance_manager","product_owner"))):
    i=_get(db,key);i.status="inactive";d=loads(i.details_json,{});d["note"]="Paused by administrator";i.details_json=dumps(d);append_entry(db,"INTEGRATION_PAUSED",user.email,{"integration":key});db.commit();db.refresh(i);return ser(i)

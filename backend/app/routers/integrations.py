from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session
from ..db.database import get_db
from ..db.models import Integration, User, CustomerCase, Evidence, Conflict, LedgerEntry
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
    d=loads(i.details_json,{})
    mode=d.get("adapter_mode")
    if mode=="deterministic_finals_adapter":
        # Never pretend that a finals fixture contacted Microsoft/Google. Counts remain immutable
        # until a real tenant adapter is configured. The live signed webhook is the executable
        # machine-to-machine ingress contract used on stage.
        append_entry(db,"INTEGRATION_FIXTURE_INSPECTED",user.email,{"integration":key,"object_count":i.object_count,"adapter_mode":mode})
        db.commit()
        out=ser(i);out["operation"]={"mode":"fixture_no_mutation","live_network_call":False,"message":"Deterministic finals fixture inspected; no vendor network sync was claimed or simulated."}
        return out
    if i.status!="connected":
        raise HTTPException(409,f"{i.name} is inactive. Connect it before refreshing.")
    if key=="customer_core":
        i.object_count=db.execute(select(CustomerCase)).scalars().all().__len__()
    elif key=="postgres":
        i.object_count=sum(len(db.execute(select(model)).scalars().all()) for model in (CustomerCase,Evidence,Conflict,LedgerEntry))
    elif key=="vector":
        rows=db.execute(select(Evidence)).scalars().all()
        i.object_count=sum(len(((e.title or '')+' '+(e.body or '')).split()) for e in rows)
    # webhook count is updated only by real authenticated POSTs, not by this refresh endpoint.
    i.last_sync_at=utcnow();d["errors"]=0;i.details_json=dumps(d)
    append_entry(db,"LOCAL_RUNTIME_REFRESH",user.email,{"integration":key,"object_count":i.object_count,"adapter_mode":mode})
    db.commit();db.refresh(i)
    out=ser(i);out["operation"]={"mode":mode or "local_runtime","live_network_call":False,"message":"Count recomputed from current local governed state."}
    return out

@router.post("/{key}/connect")
def connect(key:str,body:IntegrationConfigRequest,db:Session=Depends(get_db),user:User=Depends(require_roles("manager","compliance_manager","product_owner"))):
    i=_get(db,key);d=loads(i.details_json,{})
    if d.get("adapter_mode")=="deterministic_finals_adapter":
        raise HTTPException(409,"This finals adapter is an offline fixture and will not fake a vendor connection. Configure a real tenant adapter for production, or use the HMAC-signed webhook to demonstrate live ingress.")
    i.status="connected";i.last_sync_at=utcnow();d=loads(i.details_json,{})|body.config;d["errors"]=0;i.details_json=dumps(d)
    append_entry(db,"INTEGRATION_CONNECTED",user.email,{"integration":key,"configuration":body.config,"adapter_mode":d.get("adapter_mode")})
    db.commit();db.refresh(i);return ser(i)

@router.post("/{key}/pause")
def pause(key:str,db:Session=Depends(get_db),user:User=Depends(require_roles("manager","compliance_manager","product_owner"))):
    i=_get(db,key);i.status="inactive";d=loads(i.details_json,{});d["note"]="Paused by administrator";i.details_json=dumps(d);append_entry(db,"INTEGRATION_PAUSED",user.email,{"integration":key});db.commit();db.refresh(i);return ser(i)


_POLICY_FIELDS={
    "retrieval_enabled","policy_authority_enabled","scope_label","channel_scope","personal_dm_allowed",
    "official_only","allowed_channels","allowed_sender_roles","allowed_libraries","freshness_sla_minutes"
}

@router.patch("/{key}/policy")
def update_source_policy(key:str,body:IntegrationConfigRequest,db:Session=Depends(get_db),user:User=Depends(require_roles("manager","compliance_manager"))):
    i=_get(db,key); d=loads(i.details_json,{})
    changes={}
    for k,v in (body.config or {}).items():
        if k not in _POLICY_FIELDS:
            continue
        # Client data training is intentionally not configurable from the UI; it stays disabled.
        d[k]=v; changes[k]=v
    d["client_training_allowed"]=False
    i.details_json=dumps(d)
    append_entry(db,"SOURCE_SCOPE_UPDATED",user.email,{"integration":key,"changes":changes,"client_training_allowed":False})
    db.commit();db.refresh(i)
    out=ser(i); out["policy_update"]={"changed":changes,"training_boundary":"Client evidence is not used for model training"}
    return out

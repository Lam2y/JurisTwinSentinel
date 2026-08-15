from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session
from fastapi.responses import Response
from ..db.database import get_db
from ..db.models import DecisionContract, DecisionVersion, LedgerEntry, SecurityShield, User
from ..core.security import current_user, require_capability
from ..services.common import loads, iso
from ..services.ledger import serialize_entry, verify_chain

router=APIRouter(prefix="/ledger",tags=["ledger"])

def contract(d):return {"decision_ref":d.decision_ref,"rule_key":d.rule_key,"approved_rule":d.approved_rule,"approved_by":d.approved_by,"effective_at":iso(d.effective_at),"supersedes":d.supersedes,"affected":loads(d.affected_json,{}),"status":d.status,"version":d.version,"source_approval_ref":d.source_approval_ref}
def version(v):return {"decision_ref":v.decision_ref,"version":v.version,"rule_text":v.rule_text,"change_type":v.change_type,"actor":v.actor,"status":v.status,"metadata":loads(v.metadata_json,{}),"created_at":iso(v.created_at)}

@router.get("/decisions")
def decisions(db:Session=Depends(get_db),user:User=Depends(current_user)):return [contract(d) for d in db.execute(select(DecisionContract).order_by(DecisionContract.id.desc())).scalars().all()]
@router.get("/decisions/{ref}")
def decision(ref:str,db:Session=Depends(get_db),user:User=Depends(current_user)):
    d=db.execute(select(DecisionContract).where(DecisionContract.decision_ref==ref)).scalar_one_or_none()
    if not d:raise HTTPException(404,"Decision contract not found")
    entries=db.execute(select(LedgerEntry).where(LedgerEntry.decision_ref==ref).order_by(LedgerEntry.id.asc())).scalars().all();versions=db.execute(select(DecisionVersion).where(DecisionVersion.decision_ref==ref).order_by(DecisionVersion.id.desc())).scalars().all()
    retention=db.execute(select(SecurityShield).where(SecurityShield.key=="ledger_retention")).scalar_one_or_none()
    return {"decision":contract(d),"versions":[version(v) for v in versions],"audit_trail":[serialize_entry(e) for e in entries],"chain":verify_chain(db),"retention_lock":{"enabled":retention.enabled if retention else True,"value":loads(retention.value_json,{}) if retention else {"years":7}}}

@router.get("/recent")
def recent(limit:int=20,db:Session=Depends(get_db),user:User=Depends(current_user)):
    limit=max(1,min(limit,100))
    rows=db.execute(select(LedgerEntry).order_by(LedgerEntry.id.desc()).limit(limit)).scalars().all()
    return {"entries":[serialize_entry(e) for e in rows],"chain":verify_chain(db)}

@router.get("/verify")
def verify(db:Session=Depends(get_db),user:User=Depends(current_user)):return verify_chain(db)
@router.get("/export.csv")
def export_csv(db:Session=Depends(get_db),user:User=Depends(require_capability("can_export_ledger"))):
    rows=db.execute(select(LedgerEntry).order_by(LedgerEntry.id.asc())).scalars().all()
    def clean(v):return '"'+str(v or '').replace('"','""')+'"'
    lines=["txid,decision_ref,action,actor,created_at,previous_hash,entry_hash"]
    for e in rows:lines.append(",".join(clean(v) for v in [e.txid,e.decision_ref,e.action,e.actor,iso(e.created_at),e.previous_hash,e.entry_hash]))
    return Response("\n".join(lines),media_type="text/csv",headers={"Content-Disposition":"attachment; filename=juristwin_decision_ledger.csv"})

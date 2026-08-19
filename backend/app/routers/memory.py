from uuid import uuid4
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session
from ..db.database import get_db
from ..db.models import Evidence, User, SecurityShield
from ..core.security import current_user, require_roles
from ..schemas import MemorySearchRequest, MemoryIngestRequest, MemoryAnswerRequest
from ..services.memory import search_memory, serialize_evidence, governed_answer
from ..services.common import dumps
from ..services.ledger import append_entry
import hashlib

router=APIRouter(prefix="/memory",tags=["memory"])

@router.post("/search")
def search(body:MemorySearchRequest,db:Session=Depends(get_db),user:User=Depends(current_user)):
    search_user=user
    if body.preview_role and user.role in {"manager","compliance_manager"}:
        candidate=db.execute(select(User).where(User.role==body.preview_role)).scalars().first()
        if candidate: search_user=candidate
    results=search_memory(db,search_user,body.query,body.limit,body.filters)
    append_entry(db,"MEMORY_SEARCH_EXECUTED",user.email,{"query_excerpt":" ".join(body.query.strip().split())[:180],"preview_role":search_user.role,"result_count":len(results),"filters":body.filters})
    db.commit()
    return {"query":body.query,"role":search_user.role,"requested_by":user.role,"filters":body.filters,"count":len(results),"results":results}

@router.post("/answer")
def answer(body:MemoryAnswerRequest,db:Session=Depends(get_db),user:User=Depends(current_user)):
    answer_user=user
    if body.preview_role and user.role in {"manager","compliance_manager"}:
        candidate=db.execute(select(User).where(User.role==body.preview_role)).scalars().first()
        if candidate: answer_user=candidate
    result=governed_answer(db,answer_user,body.question)
    result["requested_by"]=user.role
    # Query audit is deliberately actor-centric. A policy-safe excerpt plus SHA-256 fingerprint
    # supports breach investigation without turning the audit trail into a second unrestricted inbox.
    excerpt=" ".join(body.question.strip().split())[:240]
    append_entry(db,"POLICY_QUERY_ANSWERED",user.email,{
        "question_excerpt":excerpt,
        "question_sha256":hashlib.sha256(body.question.encode("utf-8")).hexdigest(),
        "preview_role":answer_user.role,
        "rule_key":result.get("rule_key"),
        "result_status":result.get("management_status") or result.get("status"),
        "resolution_mode":(result.get("resolution") or {}).get("mode"),
        "sources_used":[x.get("evidence_ref") or x.get("source") for x in (result.get("sources_used") or result.get("citations") or [])],
    })
    db.commit()
    return result

@router.get("/sources")
def sources(db:Session=Depends(get_db),user:User=Depends(current_user)):
    rows=db.execute(select(Evidence).order_by(Evidence.created_at.desc())).scalars().all(); return [serialize_evidence(db,e,user) for e in rows]

@router.get("/{ref}/download")
def download_check(ref:str,db:Session=Depends(get_db),user:User=Depends(current_user)):
    e=db.execute(select(Evidence).where(Evidence.evidence_ref==ref)).scalar_one_or_none()
    if not e: raise HTTPException(404,"Evidence not found")
    dlp=db.execute(select(SecurityShield).where(SecurityShield.key=="dlp")).scalar_one_or_none()
    if dlp and dlp.enabled and e.sensitivity=="restricted" and user.role not in {"manager","compliance_manager","product_owner"}:
        append_entry(db,"DLP_DOWNLOAD_BLOCKED",user.email,{"evidence_ref":ref,"sensitivity":e.sensitivity});db.commit()
        raise HTTPException(403,"Active DLP Protection blocked this restricted evidence download")
    append_entry(db,"EVIDENCE_DOWNLOAD_AUTHORIZED",user.email,{"evidence_ref":ref,"sensitivity":e.sensitivity});db.commit()
    return {"ok":True,"evidence":serialize_evidence(db,e,user),"dlp":"checked"}

@router.post("/ingest")
def ingest(body:MemoryIngestRequest,db:Session=Depends(get_db),user:User=Depends(require_roles("manager","compliance_manager","product_owner"))):
    e=Evidence(evidence_ref=f"EV-{uuid4().hex[:10].upper()}",source=body.source,title=body.title,body=body.body,rule_key=body.rule_key,claim=body.claim,authority=body.authority,authority_level=body.authority_level,version=body.version,sensitivity=body.sensitivity,case_ref=body.case_ref,approved=body.approved,metadata_json=dumps(body.metadata))
    db.add(e);db.flush();append_entry(db,"EVIDENCE_INGESTED",user.email,{"evidence_ref":e.evidence_ref,"source":e.source});db.commit();db.refresh(e);return serialize_evidence(db,e,user)

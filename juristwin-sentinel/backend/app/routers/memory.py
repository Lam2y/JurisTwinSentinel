from uuid import uuid4
from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session
from ..db.database import get_db
from ..db.models import Evidence, User
from ..core.security import current_user, require_roles
from ..schemas import MemorySearchRequest, MemoryIngestRequest
from ..services.memory import search_memory, serialize_evidence
from ..services.common import dumps
from ..services.ledger import append_entry

router = APIRouter(prefix="/memory", tags=["memory"])

@router.post("/search")
def search(body: MemorySearchRequest, db: Session = Depends(get_db), user: User = Depends(current_user)):
    return {"query": body.query, "role": user.role, "results": search_memory(db, user, body.query, body.limit)}

@router.get("/sources")
def sources(db: Session = Depends(get_db), user: User = Depends(current_user)):
    rows = db.execute(select(Evidence).order_by(Evidence.created_at.desc())).scalars().all()
    return [serialize_evidence(e, user) for e in rows]

@router.post("/ingest")
def ingest(body: MemoryIngestRequest, db: Session = Depends(get_db), user: User = Depends(require_roles("manager", "compliance_manager", "product_owner"))):
    e = Evidence(evidence_ref=f"EV-{uuid4().hex[:10].upper()}", source=body.source, title=body.title, body=body.body,
                 rule_key=body.rule_key, claim=body.claim, authority=body.authority, authority_level=body.authority_level,
                 version=body.version, sensitivity=body.sensitivity, case_ref=body.case_ref, approved=body.approved,
                 metadata_json=dumps(body.metadata))
    db.add(e); db.flush(); append_entry(db, "EVIDENCE_INGESTED", user.email, {"evidence_ref": e.evidence_ref, "source": e.source})
    db.commit(); db.refresh(e); return serialize_evidence(e, user)

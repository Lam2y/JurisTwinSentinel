from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session
from ..db.database import get_db
from ..db.models import CustomerCase, Conflict, DecisionContract, User
from ..core.security import current_user
from ..schemas import SearchRequest
from ..services.memory import search_memory

router = APIRouter(tags=["search"])

@router.post("/search")
def global_search(body: SearchRequest, db: Session = Depends(get_db), user: User = Depends(current_user)):
    q = body.query.lower().strip()
    cases = db.execute(select(CustomerCase)).scalars().all()
    conflicts = db.execute(select(Conflict)).scalars().all()
    decisions = db.execute(select(DecisionContract)).scalars().all()
    result = []
    for c in cases:
        if q in f"{c.case_ref} {c.customer_name} {c.application_type}".lower():
            result.append({"type": "case", "ref": c.case_ref, "title": c.customer_name if user.role != "intern" else "[REDACTED]", "subtitle": c.application_type})
    for c in conflicts:
        if q in f"{c.conflict_ref} {c.name} {c.root_cause}".lower(): result.append({"type": "conflict", "ref": c.conflict_ref, "title": c.name, "subtitle": c.severity})
    for d in decisions:
        if q in f"{d.decision_ref} {d.approved_rule}".lower(): result.append({"type": "decision", "ref": d.decision_ref, "title": d.approved_rule, "subtitle": d.version})
    for e in search_memory(db, user, body.query, limit=max(1, body.limit//2)):
        result.append({"type": "evidence", "ref": e["evidence_ref"], "title": e["title"], "subtitle": e["source"], "score": e.get("score")})
    return {"query": body.query, "results": result[:body.limit]}

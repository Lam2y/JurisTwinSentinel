from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session
from ..db.database import get_db
from ..db.models import Conflict, User
from ..core.security import current_user, require_roles
from ..services.conflict_engine import conflict_payload, build_graph, detect_conflicts

router = APIRouter(prefix="/conflicts", tags=["conflicts"])

@router.get("")
def list_conflicts(db: Session = Depends(get_db), user: User = Depends(current_user)):
    rows = db.execute(select(Conflict).order_by(Conflict.id.asc())).scalars().all()
    return [conflict_payload(db, c) for c in rows]

@router.get("/{ref}")
def get_conflict(ref: str, db: Session = Depends(get_db), user: User = Depends(current_user)):
    c = db.execute(select(Conflict).where(Conflict.conflict_ref == ref)).scalar_one_or_none()
    if not c: raise HTTPException(404, "Conflict not found")
    return conflict_payload(db, c)

@router.get("/{ref}/graph")
def graph(ref: str, db: Session = Depends(get_db), user: User = Depends(current_user)):
    c = db.execute(select(Conflict).where(Conflict.conflict_ref == ref)).scalar_one_or_none()
    if not c: raise HTTPException(404, "Conflict not found")
    return build_graph(db, c)

@router.post("/detect")
def detect(db: Session = Depends(get_db), user: User = Depends(require_roles("manager", "compliance_manager", "product_owner"))):
    return detect_conflicts(db)

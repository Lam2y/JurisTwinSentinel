from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session
from ..db.database import get_db
from ..db.models import Conflict, Simulation, User
from ..core.security import current_user, require_capability
from ..schemas import SimulationRequest
from ..services.twin_engine import run_simulation, serialize_sim

router = APIRouter(prefix="/simulations", tags=["simulations"])

@router.get("/conflict/{ref}")
def latest(ref: str, db: Session = Depends(get_db), user: User = Depends(current_user)):
    s = db.execute(select(Simulation).where(Simulation.conflict_ref == ref).order_by(Simulation.id.desc())).scalars().first()
    if not s:
        c = db.execute(select(Conflict).where(Conflict.conflict_ref == ref)).scalar_one_or_none()
        if not c: raise HTTPException(404, "Conflict not found")
        return run_simulation(db, c, user)
    return serialize_sim(s)

@router.post("/conflict/{ref}/run")
def run(ref: str, body: SimulationRequest, db: Session = Depends(get_db), user: User = Depends(require_capability("can_modify_twin"))):
    c = db.execute(select(Conflict).where(Conflict.conflict_ref == ref)).scalar_one_or_none()
    if not c: raise HTTPException(404, "Conflict not found")
    return run_simulation(db, c, user, body.weights)

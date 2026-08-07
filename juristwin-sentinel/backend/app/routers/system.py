from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session
from ..db.database import get_db
from ..core.security import current_user
from ..db.models import User
from ..services.ledger import verify_chain

router = APIRouter(prefix="/system", tags=["system"])

@router.get("/health")
def health(db: Session = Depends(get_db)):
    db.execute(text("SELECT 1"))
    return {"status": "operational", "database": "ok", "decision_ledger": verify_chain(db)}

@router.get("/config")
def config(user: User = Depends(current_user)):
    return {
        "rbac": [
            {"role":"Manager","access":"Full evidence view","sensitivity":"Restricted","override":True},
            {"role":"Compliance Manager","access":"Full ledger + governance","sensitivity":"Restricted","override":True},
            {"role":"Product Owner","access":"Policy and decision authority","sensitivity":"Restricted","override":True},
            {"role":"Officer","access":"Assigned cases only","sensitivity":"Confidential","override":False},
            {"role":"Intern","access":"Redacted view","sensitivity":"Internal","override":False},
        ],
        "shields": [
            {"name":"OOH Modification Guard","status":"active","rule":"Flag approved decision modifications during OOH hours"},
            {"name":"Data Sensitivity Masking","status":"active","rule":"Shield PII across lower authority tiers"},
            {"name":"Active DLP Protection","status":"active","rule":"Prevent unapproved downloads of policy waivers"},
            {"name":"Immutable Ledger Audit Trail","status":"active","rule":"Lock governed change history into hash-linked records"},
        ],
        "retention":"7-Year Ledger Retention",
        "mode":"Finalist Demo Environment",
        "current_role": user.role,
    }

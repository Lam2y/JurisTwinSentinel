from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session
from ..db.database import get_db
from ..db.models import Integration, User
from ..core.security import current_user, require_roles
from ..services.common import loads, iso, utcnow
from ..services.ledger import append_entry

router = APIRouter(prefix="/integrations", tags=["integrations"])

def ser(i):
    return {"key": i.key, "name": i.name, "kind": i.kind, "status": i.status, "object_count": i.object_count, "last_sync_at": iso(i.last_sync_at), "shield_status": i.shield_status, "details": loads(i.details_json, {})}

@router.get("")
def list_integrations(db: Session = Depends(get_db), user: User = Depends(current_user)):
    return [ser(i) for i in db.execute(select(Integration).order_by(Integration.id.asc())).scalars().all()]

@router.post("/{key}/sync")
def sync(key: str, db: Session = Depends(get_db), user: User = Depends(require_roles("manager", "compliance_manager", "product_owner"))):
    i = db.execute(select(Integration).where(Integration.key == key)).scalar_one_or_none()
    if not i: raise HTTPException(404, "Integration not found")
    # Deterministic sync bump demonstrates state change without external service credentials.
    bump = {"outlook": 3, "teams": 7, "sharepoint": 1, "onedrive": 1, "clickup": 2, "customer_core": 0, "qa": 0, "postgres": 4, "vector": 9}.get(key, 1)
    i.object_count += bump; i.last_sync_at = utcnow(); i.status = "connected"
    append_entry(db, "INTEGRATION_SYNC", user.email, {"integration": key, "new_objects": bump, "object_count": i.object_count})
    db.commit(); db.refresh(i); return ser(i)

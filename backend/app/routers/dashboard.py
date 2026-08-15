from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.orm import Session
from ..db.database import get_db
from ..db.models import CustomerCase, Conflict, SecurityAlert, LedgerEntry, User
from ..core.security import current_user

router = APIRouter(tags=["dashboard"])

@router.get("/dashboard")
def dashboard(db: Session = Depends(get_db), user: User = Depends(current_user)):
    active_cases = db.scalar(select(func.count()).select_from(CustomerCase).where(CustomerCase.status == "active")) or 0
    conflicts = db.scalar(select(func.count()).select_from(Conflict).where(Conflict.status.in_(["unresolved","quarantined"]))) or 0
    customers_at_risk = db.scalar(select(func.count()).select_from(CustomerCase).where(CustomerCase.risk_status.in_(["High", "Critical"]))) or 0
    protected = db.scalar(select(func.count()).select_from(CustomerCase).where(CustomerCase.protected.is_(True))) or 0
    alerts = db.scalar(select(func.count()).select_from(SecurityAlert).where(SecurityAlert.status.in_(["open","reviewed","escalated","access_revoked"]))) or 0
    priority = db.execute(select(Conflict).where(Conflict.status.in_(["unresolved","quarantined"])).order_by(Conflict.id.asc())).scalars().all()
    recent = db.execute(select(LedgerEntry).order_by(LedgerEntry.id.desc()).limit(5)).scalars().all()
    # Evidence alignment reflects the flagship pre-resolution state; after resolution it becomes healthy.
    flagship = db.execute(select(Conflict).where(Conflict.conflict_ref == "CF-INCOME-001")).scalar_one()
    resolved = flagship.status == "resolved"
    quarantined = db.scalar(select(func.count()).select_from(Conflict).where(Conflict.status == "quarantined")) or 0
    integrity = {
        "score": 97 if resolved else 78,
        "threshold": "Healthy" if resolved else "Amber Warning Threshold",
        "evidence_alignment": 96 if resolved else 61,
        "version_consistency": 97 if resolved else 72,
        "access_compliance": 96,
        "decision_propagation": 98 if resolved else 58,
    }
    return {
        "greeting": f"Good morning, {user.name.split()[0]}.",
        "summary": (
            f"Sentinel quarantined {quarantined} live evidence conflict(s) without changing canonical policy."
            if quarantined else
            ("Flagship income-document decision aligned; two lower-priority conflicts remain." if resolved else "Three decision conflicts require immediate alignment across active customer cases.")
        ),
        "metrics": {"active_cases": active_cases, "decision_conflicts": conflicts, "customers_at_risk": customers_at_risk, "protected_decisions": protected, "security_alerts": alerts},
        "priority_conflicts": [{"conflict_ref": c.conflict_ref, "name": c.name, "severity": c.severity, "affected_customers": c.affected_customers, "systems_affected": c.systems_affected, "status": c.status} for c in priority],
        "integrity": integrity,
        "recent_audit": [{"txid": e.txid, "action": e.action, "actor": e.actor, "decision_ref": e.decision_ref, "created_at": e.created_at.isoformat()} for e in recent],
    }

from datetime import timedelta
from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from ..core.config import get_settings
from ..db.models import KnowledgeGap
from .common import utcnow
from .ledger import append_entry


def apply_resolved_gap_retention(db: Session, actor: str = "system") -> int:
    """Delete resolved review-queue records older than the configured retention window.

    Published ResolutionPattern records and the tamper-evident audit ledger are retained so
    governance decisions remain explainable after the transient review item expires.
    """
    days = max(1, int(get_settings().RESOLVED_GAP_RETENTION_DAYS))
    cutoff = utcnow() - timedelta(days=days)
    ids = db.execute(
        select(KnowledgeGap.id).where(
            KnowledgeGap.status == "resolved",
            KnowledgeGap.resolved_at.is_not(None),
            KnowledgeGap.resolved_at < cutoff,
        )
    ).scalars().all()
    if not ids:
        return 0

    db.execute(delete(KnowledgeGap).where(KnowledgeGap.id.in_(ids)))
    append_entry(db, "RETENTION_PURGE_APPLIED", actor, {
        "record_type": "resolved_knowledge_gap",
        "deleted_count": len(ids),
        "retention_days": days,
    })
    db.commit()
    return len(ids)


def expired_resolved_gap_count(db: Session) -> int:
    days = max(1, int(get_settings().RESOLVED_GAP_RETENTION_DAYS))
    cutoff = utcnow() - timedelta(days=days)
    return len(db.execute(
        select(KnowledgeGap.id).where(
            KnowledgeGap.status == "resolved",
            KnowledgeGap.resolved_at.is_not(None),
            KnowledgeGap.resolved_at < cutoff,
        )
    ).scalars().all())

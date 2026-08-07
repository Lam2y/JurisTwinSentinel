from uuid import uuid4
from sqlalchemy import select
from sqlalchemy.orm import Session
from ..db.models import SecurityAlert
from .common import dumps, loads, iso, utcnow
from .ledger import append_entry


def simulate_incident(db: Session, actor: str = "QA-014"):
    existing = db.execute(select(SecurityAlert).where(SecurityAlert.status == "open").order_by(SecurityAlert.id.desc())).scalar_one_or_none()
    if existing:
        return serialize_alert(existing)
    reasons = [
        "User QA-014 credentials do not map to an authorised policy approver tier.",
        "Action timestamp falls outside user's historic normal working hours.",
        "Modification performed outside approved Sentinel change-management workflow.",
        "Modified rule conflicts with active, downstream Customer Decision JT-084.",
    ]
    timeline = [
        {"action": "Viewed", "time": "01:41 AM", "status": "observed"},
        {"action": "Downloaded", "time": "01:42 AM", "status": "observed"},
        {"action": "Modified", "time": "01:43 AM", "status": "alerted"},
        {"action": "Shared", "time": "blocked", "status": "blocked"},
        {"action": "Restored", "time": None, "status": "pending"},
    ]
    alert = SecurityAlert(
        alert_ref=f"ALERT-{uuid4().hex[:6].upper()}", severity="High", status="open",
        title="APPROVED DECISION MODIFIED", user_ref=actor, document="Credit Policy v4.2",
        action="Bank-statement rule removed", conflict_decision_ref="JT-084",
        reasons_json=dumps(reasons), timeline_json=dumps(timeline), occurred_at=utcnow(),
    )
    db.add(alert)
    append_entry(db, "BODYGUARD_ALERT", "sentinel-bodyguard", {"alert_ref": alert.alert_ref, "user": actor, "document": alert.document, "risk": "High"}, "JT-084")
    db.commit(); db.refresh(alert)
    return serialize_alert(alert)


def restore_alert(db: Session, alert: SecurityAlert, actor: str):
    if alert.status == "restored":
        return serialize_alert(alert)
    alert.status = "restored"
    alert.restored_at = utcnow()
    timeline = loads(alert.timeline_json, [])
    for item in timeline:
        if item.get("action") == "Restored":
            item["time"] = alert.restored_at.strftime("%I:%M %p")
            item["status"] = "completed"
    alert.timeline_json = dumps(timeline)
    append_entry(db, "RESTORE_APPROVED_VERSION", actor, {"alert_ref": alert.alert_ref, "document": alert.document, "result": "Approved version restored"}, alert.conflict_decision_ref)
    db.commit(); db.refresh(alert)
    return serialize_alert(alert)


def serialize_alert(a: SecurityAlert):
    return {
        "alert_ref": a.alert_ref, "severity": a.severity, "status": a.status, "title": a.title,
        "user_ref": a.user_ref, "document": a.document, "action": a.action,
        "conflict_decision_ref": a.conflict_decision_ref, "reasons": loads(a.reasons_json, []),
        "timeline": loads(a.timeline_json, []), "occurred_at": iso(a.occurred_at), "restored_at": iso(a.restored_at),
    }

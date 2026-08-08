from uuid import uuid4
from sqlalchemy import select
from sqlalchemy.orm import Session
from ..db.models import SecurityAlert, SecurityShield, DecisionContract, DecisionVersion, CustomerCase, User
from .common import dumps, loads, iso, utcnow
from .ledger import append_entry

STANDARD_RULE="Gig workers may submit verified bank statements as acceptable income evidence."
OVERRIDE_RULE="Bank statements are not accepted as standalone proof of income; an authorised override requires payslips or dual-source evidence."

def _shield(db,key): return db.execute(select(SecurityShield).where(SecurityShield.key==key)).scalar_one_or_none()
def _next_version(db,decision_ref):
    rows=db.execute(select(DecisionVersion).where(DecisionVersion.decision_ref==decision_ref).order_by(DecisionVersion.id.desc())).scalars().all()
    if not rows:return "v4.1"
    try:
        major,minor=rows[0].version.lower().lstrip('v').split('.');return f"v{major}.{int(minor)+1}"
    except:return f"v4.{len(rows)+1}"
def _add_timeline(alert,action,status="completed",time=None,detail=None):
    tl=loads(alert.timeline_json,[]);tl.append({"action":action,"time":time or utcnow().strftime("%I:%M %p"),"status":status,**({"detail":detail} if detail else {})});alert.timeline_json=dumps(tl)
def _new_version(db,contract,rule,actor,change_type,meta=None):
    for v in db.execute(select(DecisionVersion).where(DecisionVersion.decision_ref==contract.decision_ref,DecisionVersion.status=="active")).scalars().all():v.status="historical"
    ver=_next_version(db,contract.decision_ref);contract.version=ver;contract.approved_rule=rule;contract.effective_at=utcnow()
    db.add(DecisionVersion(decision_ref=contract.decision_ref,version=ver,rule_text=rule,change_type=change_type,actor=actor,status="active",metadata_json=dumps(meta or {})))
    return ver

def simulate_incident(db:Session,actor:str="QA-014"):
    existing=db.execute(select(SecurityAlert).where(SecurityAlert.status.in_(["open","reviewed","escalated","access_revoked"])).order_by(SecurityAlert.id.desc())).scalars().first()
    if existing:return serialize_alert(existing)
    reasons=["User QA-014 credentials do not map to an authorised policy approver tier.","Modification performed outside approved Sentinel change-management workflow.","Modified rule conflicts with active, downstream Customer Decision JT-084."]
    ooh=_shield(db,"ooh_guard")
    if not ooh or ooh.enabled:reasons.insert(1,"Action timestamp falls outside user's historic normal working hours.")
    timeline=[{"action":"Viewed","time":"01:41 AM","status":"observed"},{"action":"Downloaded","time":"01:42 AM","status":"observed"},{"action":"Modified","time":"01:43 AM","status":"alerted"},{"action":"Shared","time":"blocked","status":"blocked"},{"action":"Restored","time":None,"status":"pending"}]
    alert=SecurityAlert(alert_ref=f"ALERT-{uuid4().hex[:6].upper()}",severity="High" if len(reasons)>=4 else "Medium",status="open",title="APPROVED DECISION MODIFIED",user_ref=actor,document="Credit Policy v4.2",action="Bank-statement rule removed",conflict_decision_ref="JT-084",reasons_json=dumps(reasons),timeline_json=dumps(timeline),occurred_at=utcnow())
    db.add(alert);append_entry(db,"BODYGUARD_ALERT","sentinel-bodyguard",{"alert_ref":alert.alert_ref,"user":actor,"document":alert.document,"risk":alert.severity,"reasons":reasons},"JT-084");db.commit();db.refresh(alert);return serialize_alert(alert)

def review_alert(db,alert,actor):
    alert.status="reviewed";_add_timeline(alert,"Reviewed",detail=f"Incident reviewed by {actor}");append_entry(db,"BODYGUARD_ACTIVITY_REVIEWED",actor,{"alert_ref":alert.alert_ref,"timeline_entries":len(loads(alert.timeline_json,[]))},alert.conflict_decision_ref);db.commit();db.refresh(alert);return serialize_alert(alert)

def explanation(db,alert,actor):
    contract=db.execute(select(DecisionContract).where(DecisionContract.decision_ref==alert.conflict_decision_ref)).scalar_one_or_none();target=db.execute(select(User).where(User.name==alert.user_ref)).scalar_one_or_none()
    reasons=loads(alert.reasons_json,[]);result={"summary":f"Sentinel found {len(reasons)} independent governance signals indicating the modification should not silently replace the approved decision.","reasons":reasons,"decision":contract.approved_rule if contract else None,"decision_version":contract.version if contract else None,"user_access_active":target.active if target else None,"recommended_actions":["Review activity chronology","Revoke user access if credentials are compromised","Escalate to Compliance for policy review","Restore the approved version unless the overwrite is formally authorised"]}
    append_entry(db,"BODYGUARD_EXPLANATION_REQUESTED",actor,{"alert_ref":alert.alert_ref,"reason_count":len(reasons)},alert.conflict_decision_ref);db.commit();return result

def revoke_access(db,alert,actor):
    u=db.execute(select(User).where(User.name==alert.user_ref)).scalar_one_or_none()
    if u:u.active=False
    alert.status="access_revoked";_add_timeline(alert,"Access Revoked",detail=f"{alert.user_ref} disabled by {actor}");append_entry(db,"BODYGUARD_ACCESS_REVOKED",actor,{"alert_ref":alert.alert_ref,"user_ref":alert.user_ref,"user_account_found":bool(u),"active":False},alert.conflict_decision_ref);db.commit();db.refresh(alert);return {"alert":serialize_alert(alert),"user":{"name":u.name,"email":u.email,"active":u.active} if u else None}

def escalate_alert(db,alert,actor):
    alert.status="escalated";_add_timeline(alert,"Escalated to Compliance",detail=f"Escalated by {actor}");append_entry(db,"BODYGUARD_ESCALATED",actor,{"alert_ref":alert.alert_ref,"severity":alert.severity,"destination":"Compliance Manager"},alert.conflict_decision_ref);db.commit();db.refresh(alert);return serialize_alert(alert)

def authorize_override(db,alert,actor,comments=None):
    contract=db.execute(select(DecisionContract).where(DecisionContract.decision_ref==alert.conflict_decision_ref,DecisionContract.status=="active")).scalar_one_or_none()
    if not contract:raise ValueError("Active decision contract not found")
    ver=_new_version(db,contract,OVERRIDE_RULE,actor,"authorised_override",{"alert_ref":alert.alert_ref,"comments":comments})
    cases=db.execute(select(CustomerCase).where(CustomerCase.conflict_ref=="CF-INCOME-001")).scalars().all()
    for c in cases:c.risk_status="High";c.current_blocker="Authorised override requires additional income evidence";c.pending_days=max(c.pending_days,2.4)
    alert.status="authorized_override";_add_timeline(alert,"Authorised Overwrite",detail=f"Override accepted as {ver}")
    append_entry(db,"BODYGUARD_OVERRIDE_AUTHORIZED",actor,{"alert_ref":alert.alert_ref,"document":alert.document,"new_version":ver,"affected_cases":len(cases),"comments":comments},alert.conflict_decision_ref);db.commit();db.refresh(alert);return {"alert":serialize_alert(alert),"decision_version":ver,"approved_rule":contract.approved_rule,"affected_cases":len(cases)}

def restore_alert(db:Session,alert:SecurityAlert,actor:str):
    if alert.status=="restored":return serialize_alert(alert)
    contract=db.execute(select(DecisionContract).where(DecisionContract.decision_ref==alert.conflict_decision_ref,DecisionContract.status=="active")).scalar_one_or_none();ver=None
    if contract:
        ver=_new_version(db,contract,STANDARD_RULE,actor,"restored_approved_version",{"alert_ref":alert.alert_ref})
        cases=db.execute(select(CustomerCase).where(CustomerCase.conflict_ref=="CF-INCOME-001")).scalars().all()
        for c in cases:c.risk_status="Low";c.pending_days=min(c.pending_days,1.1);c.current_blocker=None;c.protected=True
    alert.status="restored";alert.restored_at=utcnow();timeline=loads(alert.timeline_json,[])
    found=False
    for item in timeline:
        if item.get("action")=="Restored":item["time"]=alert.restored_at.strftime("%I:%M %p");item["status"]="completed";item["detail"]=f"Decision restored as {ver or 'approved version'}";found=True
    if not found:timeline.append({"action":"Restored","time":alert.restored_at.strftime("%I:%M %p"),"status":"completed"})
    alert.timeline_json=dumps(timeline);append_entry(db,"RESTORE_APPROVED_VERSION",actor,{"alert_ref":alert.alert_ref,"document":alert.document,"result":"Approved version restored","new_version":ver},alert.conflict_decision_ref);db.commit();db.refresh(alert);return serialize_alert(alert)

def serialize_alert(a):
    return {"alert_ref":a.alert_ref,"severity":a.severity,"status":a.status,"title":a.title,"user_ref":a.user_ref,"document":a.document,"action":a.action,"conflict_decision_ref":a.conflict_decision_ref,"reasons":loads(a.reasons_json,[]),"timeline":loads(a.timeline_json,[]),"occurred_at":iso(a.occurred_at),"restored_at":iso(a.restored_at)}

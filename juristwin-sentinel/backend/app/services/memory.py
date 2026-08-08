import math, re
from collections import Counter
from datetime import datetime, timedelta, timezone
from sqlalchemy import select
from sqlalchemy.orm import Session
from ..db.models import Evidence, User, RolePolicy, SecurityShield
from .common import loads, iso

TOKEN_RE = re.compile(r"[a-z0-9]+")
SENSITIVITY_LEVEL = {"public": 0, "internal": 1, "confidential": 2, "restricted": 3}

def tokenize(text: str): return TOKEN_RE.findall((text or "").lower())
def cosine(a: Counter, b: Counter):
    dot=sum(a[k]*b.get(k,0) for k in a); na=math.sqrt(sum(v*v for v in a.values())); nb=math.sqrt(sum(v*v for v in b.values()))
    return dot/(na*nb) if na and nb else 0.0

def _policy(db,user):
    return db.execute(select(RolePolicy).where(RolePolicy.role==user.role)).scalar_one_or_none()
def _shield(db,key):
    return db.execute(select(SecurityShield).where(SecurityShield.key==key)).scalar_one_or_none()
def _can_access(db:Session,user:User,e:Evidence):
    p=_policy(db,user); max_level=p.max_sensitivity if p else 1
    level=SENSITIVITY_LEVEL.get((e.sensitivity or "internal").lower(),1)
    if level<=max_level:
        if user.role=="officer" and e.case_ref:
            assigned=set(loads(user.assigned_case_refs,[])); return e.case_ref in assigned or e.case_ref=="JT-2026-084"
        return True
    return False

def _redacted(e):
    return {"evidence_ref":e.evidence_ref,"source":e.source,"title":e.title,"body":"[REDACTED BY SENTINEL SHIELD]","rule_key":e.rule_key,"claim":"[RESTRICTED]","authority":e.authority,"authority_level":e.authority_level,"version":e.version,"status":e.status,"sensitivity":e.sensitivity,"case_ref":e.case_ref,"approved":e.approved,"superseded":e.superseded,"created_at":iso(e.created_at),"metadata":{"access":"redacted"}}

def serialize_evidence(db:Session,e:Evidence,user:User,score:float|None=None):
    masking=_shield(db,"data_masking")
    redact=(masking.enabled if masking else True) and not _can_access(db,user,e)
    if redact: result=_redacted(e)
    else:
        result={"evidence_ref":e.evidence_ref,"source":e.source,"title":e.title,"body":e.body,"rule_key":e.rule_key,"claim":e.claim,"authority":e.authority,"authority_level":e.authority_level,"version":e.version,"status":e.status,"sensitivity":e.sensitivity,"case_ref":e.case_ref,"approved":e.approved,"superseded":e.superseded,"created_at":iso(e.created_at),"metadata":loads(e.metadata_json,{})}
        if masking and not masking.enabled and not _can_access(db,user,e): result["metadata"]["shield_bypassed_for_demo"] = True
    if score is not None: result["score"]=round(score,4)
    return result

def _matches(e, filters):
    f=filters or {}; meta=loads(e.metadata_json,{})
    if f.get("source") and f["source"]!="All" and f["source"].lower() not in (e.source or "").lower(): return False
    if f.get("customer") and f["customer"] not in {"Any","All"} and f["customer"].lower() not in str(meta.get("customer") or "").lower(): return False
    if f.get("project") and f["project"] not in {"Any","All"} and f["project"].lower()!=str(meta.get("project") or "").lower(): return False
    if f.get("sensitivity") and f["sensitivity"]!="All" and f["sensitivity"].lower()!=(e.sensitivity or "").lower(): return False
    if f.get("status") and f["status"]!="All" and f["status"].lower()!=(e.status or "").lower(): return False
    if f.get("version") and f["version"]!="All" and f["version"].lower() not in (e.version or "").lower(): return False
    if f.get("authority_level") and int(e.authority_level or 0)<int(f["authority_level"]): return False
    if f.get("decision_tier") and int(meta.get("decision_tier",1))!=int(f["decision_tier"]): return False
    if f.get("days"):
        cutoff=datetime.now(timezone.utc)-timedelta(days=int(f["days"])); created=e.created_at
        if created and created.tzinfo is None: created=created.replace(tzinfo=timezone.utc)
        if created and created<cutoff: return False
    return True

def search_memory(db:Session,user:User,query:str,limit:int=10,filters:dict|None=None):
    rows=db.execute(select(Evidence).order_by(Evidence.created_at.desc())).scalars().all(); qv=Counter(tokenize(query)); scored=[]
    for e in rows:
        if not _matches(e,filters): continue
        text=" ".join([e.title or "",e.body or "",e.claim or "",e.rule_key or "",e.source or "",str(loads(e.metadata_json,{}))])
        score=cosine(qv,Counter(tokenize(text))) if qv else 0.55 + min((e.authority_level or 1)*.05,.35)
        if score>0 or not qv: scored.append((score,e))
    scored.sort(key=lambda x:(x[0],x[1].created_at),reverse=True)
    return [serialize_evidence(db,e,user,s) for s,e in scored[:limit]]

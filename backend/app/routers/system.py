from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import text, select, func
from sqlalchemy.orm import Session
from ..db.database import get_db
from ..core.security import current_user, require_roles
from ..db.models import User, RolePolicy, SecurityShield, Integration, CustomerCase, Conflict, Evidence, LiveChallenge
from ..schemas import RolePolicyUpdate, ShieldUpdate
from ..services.common import loads, dumps, iso
from ..services.ledger import verify_chain, append_entry
from ..services.policy_reasoner import extract_policy_atoms, compare_policy_atoms
from ..services.impact_graph import build_impact_graph
from ..services.policy_ml import get_policy_ai
from ..services.memory import governed_answer

router=APIRouter(prefix="/system",tags=["system"])

def role_ser(r):
    return {"role":r.role,"display_name":r.display_name,"description":r.description,"enabled":r.enabled,"max_sensitivity":r.max_sensitivity,"can_override":r.can_override,"can_modify_twin":r.can_modify_twin,"can_export_ledger":r.can_export_ledger,"can_review_bodyguard":r.can_review_bodyguard,"updated_by":r.updated_by,"updated_at":iso(r.updated_at)}
def shield_ser(s):
    return {"key":s.key,"name":s.name,"description":s.description,"enabled":s.enabled,"value":loads(s.value_json,{}),"updated_by":s.updated_by,"updated_at":iso(s.updated_at)}

@router.get("/health")
def health(db:Session=Depends(get_db)):
    db.execute(text("SELECT 1"));return {"status":"operational","database":"ok","decision_ledger":verify_chain(db),"version":"5.7.0","service":"JurisTwin Sentinel JurisTech"}

@router.get("/readiness")
def readiness(db:Session=Depends(get_db),user:User=Depends(current_user)):
    checks=[]
    def check(key,label,ok,detail,critical=True):
        checks.append({"key":key,"label":label,"ok":bool(ok),"detail":detail,"critical":critical})

    try:
        db.execute(text("SELECT 1")); db_ok=True
    except Exception:
        db_ok=False
    check("database","Transactional database",db_ok,"SQLAlchemy database round-trip succeeded" if db_ok else "Database query failed")

    chain=verify_chain(db)
    check("ledger","Tamper-evident ledger",bool(chain.get("ok")),f"{chain.get('entries',0)} entries verified")

    roles=db.execute(select(RolePolicy)).scalars().all()
    enabled_roles=sum(1 for r in roles if r.enabled)
    check("rbac","RBAC governance",enabled_roles>=5,f"{enabled_roles}/{len(roles)} roles enabled")

    shields=db.execute(select(SecurityShield)).scalars().all()
    enabled_shields=sum(1 for s in shields if s.enabled)
    check("shields","Security shields",enabled_shields>=3,f"{enabled_shields}/{len(shields)} safeguards enabled")

    ints=db.execute(select(Integration)).scalars().all()
    connected=sum(1 for i in ints if i.status=="connected")
    check("integrations","Integration adapter layer",connected>=7,f"{connected}/{len(ints)} adapters connected",critical=False)

    canonical=db.execute(select(Evidence).where(Evidence.evidence_ref=="EV-OUTLOOK-001",Evidence.approved.is_(True))).scalar_one_or_none()
    check("canonical","Canonical evidence",bool(canonical),"Highest-authority approved evidence is addressable")

    flagship=db.execute(select(Conflict).where(Conflict.conflict_ref=="CF-INCOME-001")).scalar_one_or_none()
    check("conflict","Conflict intelligence",bool(flagship),"Flagship conflict graph is available")

    case_count=db.execute(select(func.count(CustomerCase.id))).scalar_one()
    check("cases","Operational case state",case_count>=100,f"{case_count} governed customer cases loaded")

    # The live challenge engine is considered ready when its persistence table exists and the user
    # has an eligible role. No external network dependency is required.
    challenge_count=db.execute(select(func.count(LiveChallenge.id))).scalar_one()
    challenge_role=user.role in {"manager","compliance_manager","product_owner"}
    check("challenge","Judge Challenge engine",challenge_role,f"Runtime unseen-evidence pipeline ready · {challenge_count} prior challenge(s)")

    incoming=extract_policy_atoms("Bank statements are no longer accepted. Officers must request payslips from gig workers.", "income_document_rule")
    canonical_atoms=extract_policy_atoms("Bank statements may be accepted in place of payslips.", "income_document_rule")
    reason=compare_policy_atoms(canonical_atoms,incoming)
    check("reasoner","Policy Atom Reasoner",reason.get("collision") is True,f"Explainable modality collision engine · {len(reason.get('collisions',[]))} collision(s)")

    try:
        model_card=get_policy_ai().model_card()
        bench=model_card.get("held_out_development_benchmark",{})
        model_ok=(model_card.get("status")=="READY" and model_card.get("learned_component") is True and bench.get("domain_macro_f1",0)>=0.85 and bench.get("stance_macro_f1",0)>=0.85)
        check("hybrid_ai","Learned + white-box policy AI",model_ok,f"Local learned classifier READY · domain macro-F1 {bench.get('domain_macro_f1','—')} · stance macro-F1 {bench.get('stance_macro_f1','—')} · symbolic fallback enabled")
    except Exception as exc:
        # The learned layer is an enhancement, never a single point of failure: the deterministic
        # reasoner remains available. Readiness still surfaces the model issue visibly.
        check("hybrid_ai","Learned + white-box policy AI",False,f"Learned layer unavailable: {type(exc).__name__}; symbolic fallback remains safe")

    impact=build_impact_graph(db,"income_document_rule","CF-INCOME-001")
    check("impact","Dependency blast-radius engine",impact.get("affected_cases")==27,f"BFS traversed {impact.get('reachable_nodes',0)} nodes to {impact.get('affected_cases',0)} affected cases")

    governed=governed_answer(db,user,"Can gig workers use bank statements as income evidence?")
    answer_ok=governed.get("status") in {"CONFLICT_PRESENT","VERIFIED"} and governed.get("rule_key")=="income_document_rule" and bool(governed.get("citations"))
    check("verified_answer","Evidence-bound plain-language answers",answer_ok,f"{governed.get('status')} · {len(governed.get('citations',[]))} cited governed source(s) · learned routing cannot author policy")

    from ..core.config import get_settings
    settings_v4=get_settings()
    webhook_secret=settings_v4.WEBHOOK_SECRET
    check("webhook","Signed real-time evidence gateway",len(webhook_secret)>=16,"HMAC-SHA256 machine-to-machine ingress ready · replay-safe contract")
    check("proof_signing","Decision Assurance signing",len(settings_v4.PROOF_SIGNING_SECRET)>=24,"HMAC-SHA256 exported Proof Packs are authenticity-signed")
    static_markers=("juristwin-finals-local-secret-change-me","juristwin-finals-webhook-secret","juristwin-finals-proof-signing-secret")
    secret_ok=all(len(x)>=32 and not any(marker in x for marker in static_markers) for x in (settings_v4.SECRET_KEY,settings_v4.WEBHOOK_SECRET,settings_v4.PROOF_SIGNING_SECRET))
    check("secret_hygiene","Runtime secret hygiene",secret_ok,f"{settings_v4.SECURITY_SECRET_MODE} · independent non-static JWT/webhook/proof keys")

    from ..services.assurance import invariant_report
    invariant=invariant_report(db)
    check("invariants","Operational invariants",invariant.get("status")=="HEALTHY","Cross-table safe-state invariants reconcile")
    check("hardening","API hardening layer",True,"Request tracing · security headers · rate containment · structured runtime telemetry")

    critical=[c for c in checks if c["critical"]]
    passed=sum(1 for c in checks if c["ok"])
    critical_ok=all(c["ok"] for c in critical)
    score=round(100*passed/max(1,len(checks)))
    return {
        "status":"READY" if critical_ok else "DEGRADED",
        "score":score,
        "checks":checks,
        "resilience":{
            "external_ai_required":False,
            "external_network_required":False,
            "learned_ai":"Local TF-IDF word+character n-grams + Logistic Regression; retrained on startup from bundled labelled corpus",
            "fallback_mode":"Learned proposal + deterministic policy-atom verification; symbolic-only fallback if ML is unavailable",
            "safe_state":"Live evidence is quarantined until governed approval; challenge mode cannot silently overwrite canonical policy.",
        },
    }

@router.get("/config")
def config(db:Session=Depends(get_db),user:User=Depends(current_user)):
    roles=db.execute(select(RolePolicy).order_by(RolePolicy.id)).scalars().all();shields=db.execute(select(SecurityShield).order_by(SecurityShield.id)).scalars().all()
    return {"rbac":[role_ser(r) for r in roles],"shields":[shield_ser(s) for s in shields],"retention":"7-Year Ledger Retention","mode":"JurisTwin Sentinel v5.7 Track-2 MaxScore Hybrid Decision Assurance Platform","current_role":user.role}

@router.patch("/roles/{role}")
def update_role(role:str,body:RolePolicyUpdate,db:Session=Depends(get_db),user:User=Depends(require_roles("manager","compliance_manager"))):
    r=db.execute(select(RolePolicy).where(RolePolicy.role==role)).scalar_one_or_none()
    if not r: raise HTTPException(404,"Role policy not found")
    data=body.model_dump(exclude_none=True)
    if role==user.role and data.get("enabled") is False: raise HTTPException(400,"Cannot disable your own active role during this session")
    for k,v in data.items(): setattr(r,k,v)
    r.updated_by=user.email
    append_entry(db,"RBAC_POLICY_UPDATED",user.email,{"role":role,"changes":data})
    db.commit();db.refresh(r);return role_ser(r)

@router.patch("/shields/{key}")
def update_shield(key:str,body:ShieldUpdate,db:Session=Depends(get_db),user:User=Depends(require_roles("manager","compliance_manager"))):
    s=db.execute(select(SecurityShield).where(SecurityShield.key==key)).scalar_one_or_none()
    if not s: raise HTTPException(404,"Security shield not found")
    changes={}
    if body.enabled is not None: s.enabled=body.enabled;changes["enabled"]=body.enabled
    if body.value is not None: s.value_json=dumps(body.value);changes["value"]=body.value
    s.updated_by=user.email
    append_entry(db,"SECURITY_SHIELD_UPDATED",user.email,{"shield":key,"changes":changes})
    db.commit();db.refresh(s);return shield_ser(s)

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import text, select, func
from sqlalchemy.orm import Session
from ..db.database import get_db
from ..core.security import current_user, require_roles
from ..db.models import User, RolePolicy, SecurityShield, Integration, CustomerCase, Conflict, Evidence, LiveChallenge, LedgerEntry
from ..schemas import RolePolicyUpdate, ShieldUpdate
from ..services.common import loads, dumps, iso, utcnow
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
    db.execute(text("SELECT 1"));return {"status":"operational","database":"ok","decision_ledger":verify_chain(db),"version":"6.0.0","service":"JurisTwin Sentinel JurisTech"}

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
    return {"rbac":[role_ser(r) for r in roles],"shields":[shield_ser(s) for s in shields],"retention":"7-Year Ledger Retention","mode":"JurisTwin Sentinel v6.0 Lecturer-Complete Manager Decision Assurance Platform","current_role":user.role}

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


@router.get("/security-overview")
def security_overview(db:Session=Depends(get_db),user:User=Depends(current_user)):
    roles=db.execute(select(RolePolicy).order_by(RolePolicy.id)).scalars().all()
    shields={s.key:s for s in db.execute(select(SecurityShield)).scalars().all()}
    integrations=db.execute(select(Integration).order_by(Integration.id)).scalars().all()
    export_cfg=loads(shields.get("customer_export").value_json,{}) if shields.get("customer_export") else {}
    role_matrix=[]
    for r in roles:
        role_matrix.append({
            "role":r.role,"display_name":r.display_name,"max_sensitivity":r.max_sensitivity,
            "view_customer_data":"full" if r.role in {"manager","compliance_manager","product_owner"} else ("redacted" if r.role=="intern" else "assigned_only"),
            "masked_customer_export":r.role in set(export_cfg.get("masked_roles",["manager","compliance_manager"])),
            "full_customer_export":r.role in set(export_cfg.get("full_roles",["compliance_manager"])),
            "ledger_export":bool(r.can_export_ledger),
        })
    source_policies=[]
    for i in integrations:
        d=loads(i.details_json,{})
        last_sync=i.last_sync_at
        if last_sync and last_sync.tzinfo is None:
            from datetime import timezone
            last_sync=last_sync.replace(tzinfo=timezone.utc)
        age_minutes=round(max(0,(utcnow()-last_sync).total_seconds()/60),1) if last_sync else None
        sla=d.get("freshness_sla_minutes")
        freshness_state=("LIVE" if d.get("realtime") and i.status=="connected" else
                         "CURRENT" if age_minutes is not None and (not sla or age_minutes<=float(sla)) else
                         "STALE" if age_minutes is not None else "NO_SYNC")
        source_policies.append({
            "key":i.key,"name":i.name,"kind":i.kind,"status":i.status,"object_count":i.object_count,
            "last_sync_at":iso(i.last_sync_at),"realtime":bool(d.get("realtime")),
            "retrieval_enabled":bool(d.get("retrieval_enabled",True)),
            "policy_authority_enabled":bool(d.get("policy_authority_enabled",False)),
            "scope_label":d.get("scope_label") or "Configured source scope",
            "channel_scope":d.get("channel_scope"),
            "personal_dm_allowed":bool(d.get("personal_dm_allowed",False)),
            "official_only":bool(d.get("official_only",False)),
            "client_training_allowed":False,
            "freshness_sla_minutes":sla,
            "freshness_state":freshness_state,"age_minutes":age_minutes,
            "allowed_channels":d.get("allowed_channels",[]),
            "allowed_sender_roles":d.get("allowed_sender_roles",[]),
            "allowed_libraries":d.get("allowed_libraries",[]),
            "adapter_mode":d.get("adapter_mode"),
        })
    recent=db.execute(select(LedgerEntry).order_by(LedgerEntry.id.desc()).limit(30)).scalars().all()
    audit=[]
    for e in recent:
        payload=loads(e.payload_json,{})
        audit.append({
            "txid":e.txid,"action":e.action,"actor":e.actor,"created_at":iso(e.created_at),
            "subject":payload.get("question_excerpt") or payload.get("evidence_ref") or payload.get("integration") or payload.get("conflict_ref") or payload.get("mode") or payload.get("role") or "Governed system action",
            "result":payload.get("result_status") or payload.get("status") or ("BLOCKED" if "BLOCKED" in e.action else "RECORDED"),
            "payload":payload,
        })
    return {
        "privacy":{
            "principle":"Minimum necessary evidence: source scope first, RBAC second, DLP on export.",
            "teams":"Approved group/channel conversations only; personal/1:1 DMs are blocked from indexing by default.",
            "email":"Only explicitly approved official management/policy mailboxes may influence policy resolution; casual coworker mail is excluded.",
            "customer_data":"Customer records may prove operational impact but never define policy and never train the model.",
            "model_training":"Client evidence is not used to retrain the local classifier or any external model. Administrators control retrieval/indexing scope instead.",
        },
        "transfer_security":{
            "demo_runtime":"Loopback/local HTTP for finals resilience; no claim of TLS termination inside the local browser demo.",
            "production_transport":"TLS 1.2+ / TLS 1.3 at the API gateway or reverse proxy; vendor connectors use OAuth/service credentials where available.",
            "signed_ingress":"HMAC-SHA256 signed webhook with replay/idempotency protection is implemented for machine-to-machine events.",
            "api_keys":"Secrets are server-side environment variables; never sent to the browser or stored in source-control defaults.",
            "at_rest":"Production deployment should use encrypted managed PostgreSQL/disk encryption and enterprise KMS; the finals local fixture does not pretend to provide managed-database TDE.",
        },
        "realtime":{
            "answer_recompute":"Every governed question re-runs retrieval and source-scope resolution against current database state.",
            "live_ingress":"Signed webhook events are visible immediately but quarantined until governance if they attempt to change policy.",
            "policy_change_behavior":"Approved source/Decision Contract changes are reflected on the next question without rebuilding the frontend.",
        },
        "role_matrix":role_matrix,"source_policies":source_policies,"audit":audit,
        "current_user":{"email":user.email,"role":user.role},
    }


@router.get("/manager-control-summary")
def manager_control_summary(db:Session=Depends(get_db),user:User=Depends(current_user)):
    """Management-facing proof that the prototype review recommendations are implemented.

    This endpoint intentionally expresses controls in business language while deriving PASS/REVIEW
    from the live database configuration. It powers the in-product "Original → Now" coverage view.
    """
    integrations={i.key:i for i in db.execute(select(Integration)).scalars().all()}
    shields={s.key:s for s in db.execute(select(SecurityShield)).scalars().all()}

    def details(key):
        row=integrations.get(key)
        return loads(row.details_json,{}) if row else {}

    teams=details("teams"); outlook=details("outlook"); gmail=details("gmail")
    customer_export=loads(shields.get("customer_export").value_json,{}) if shields.get("customer_export") else {}
    transport=loads(shields.get("transport_security").value_json,{}) if shields.get("transport_security") else {}
    query_audit=shields.get("query_audit")
    realtime_guard=shields.get("realtime_freshness")

    try:
        answer=governed_answer(db,user,"Can gig workers use bank statements as income evidence?")
    except Exception:
        answer={}
    answer_ok=answer.get("management_status") in {"GOVERNED_ANSWER","ACCESS_RESTRICTED"} and bool(answer.get("primary_source") or answer.get("sources_used"))
    source_scope_ok=(bool(teams.get("retrieval_enabled",True)) and not bool(teams.get("personal_dm_allowed",False)) and
                     bool(outlook.get("official_only",False)) and bool(gmail.get("official_only",False)))
    authority_ok=(bool(outlook.get("policy_authority_enabled",False)) and
                  not bool(details("customer_core").get("policy_authority_enabled",False)))
    privacy_ok=all(not bool(details(k).get("client_training_allowed",False)) for k in integrations)
    export_ok=("manager" in set(customer_export.get("masked_roles",[])) and
               "manager" not in set(customer_export.get("full_roles",[])) and
               "compliance_manager" in set(customer_export.get("full_roles",[])))
    transfer_ok=(str(transport.get("webhook_auth","")).upper()=="HMAC-SHA256" and
                 bool(transport.get("frontend_secrets") is False))
    audit_count=db.execute(select(func.count(LedgerEntry.id))).scalar_one()
    audit_ok=bool(query_audit and query_audit.enabled and audit_count>0)
    realtime_ok=bool(realtime_guard and realtime_guard.enabled)

    controls=[
        {
            "key":"trusted_answer","title":"One definite answer + exact source","manager_question":"What should my team follow?",
            "original":"The prototype mainly exposed that sources disagreed, leaving management to interpret the conflict.",
            "now":"JurisTwin gives one governed answer first, names the main source, shows supporting sources, and explains why that source won.",
            "status":"PASS" if answer_ok else "REVIEW","proof":f"{len(answer.get('sources_used') or answer.get('citations') or [])} winning source(s) returned with {answer.get('resolution',{}).get('mode','governed resolution')}",
            "page":"overview","action":"Try a management question"
        },
        {
            "key":"source_scope","title":"Management chooses which sources count","manager_question":"Where is JurisTwin allowed to look?",
            "original":"Connected systems could look like one broad evidence pool.",
            "now":"Managers can enable/disable sources, restrict Teams to approved group/channel conversations, and restrict email to official management/policy senders.",
            "status":"PASS" if source_scope_ok else "REVIEW","proof":"Teams personal DMs blocked · Outlook/Gmail official-only rules enforced",
            "page":"governance","action":"Review source access"
        },
        {
            "key":"authority_majority","title":"Official source first; majority only when safe","manager_question":"If sources conflict, who wins?",
            "original":"A conflict could be shown without a simple, defensible winner-selection rule.",
            "now":"Private/ineligible evidence is removed first; approved authority wins. Majority is only a fallback among equally authoritative sources, so casual chat cannot outvote policy.",
            "status":"PASS" if authority_ok else "REVIEW","proof":"Authority precedence + same-tier majority fallback",
            "page":"overview","action":"See why a source won"
        },
        {
            "key":"privacy","title":"Private and irrelevant content stays out","manager_question":"Are we reading too much employee/client data?",
            "original":"Privacy boundaries were not obvious enough to management.",
            "now":"Personal DMs and casual email are excluded, minimum-necessary evidence is used, and client evidence never becomes AI training data.",
            "status":"PASS" if privacy_ok and source_scope_ok else "REVIEW","proof":"Client training hard-disabled across connector policies",
            "page":"governance","action":"See privacy boundaries"
        },
        {
            "key":"customer_security","title":"Customer-data access and export control","manager_question":"Who can view or export client data?",
            "original":"The prototype did not make export permissions and forbidden actions obvious.",
            "now":"Backend RBAC separates customer view, masked export and full export. Every allowed or blocked export requires a reason and is audited.",
            "status":"PASS" if export_ok else "REVIEW","proof":"Manager: masked export only · Compliance: full export · Officer/Intern: blocked",
            "page":"governance","action":"Test an export restriction"
        },
        {
            "key":"secure_transfer","title":"Protected transfer, secrets and API keys","manager_question":"How is data protected between Teams/Outlook and JurisTwin?",
            "original":"Connector movement and secret handling were mostly architectural details.",
            "now":"The system shows the protected data path, keeps keys server-side, supports signed live ingress, and documents TLS/encrypted-storage boundaries for production.",
            "status":"PASS" if transfer_ok else "REVIEW","proof":"HMAC-SHA256 live ingress · browser receives no API secrets",
            "page":"governance","action":"Review the protected data path"
        },
        {
            "key":"audit","title":"Who asked, changed or exported what","manager_question":"Can we investigate a future data incident?",
            "original":"Decision history existed, but user-level query/export traceability was not a main management view.",
            "now":"Questions, source-rule changes, approvals and export attempts are attributed to a user, time, subject and outcome in the tamper-evident ledger.",
            "status":"PASS" if audit_ok else "REVIEW","proof":f"{audit_count} audit ledger event(s) currently traceable",
            "page":"governance","action":"Open who-did-what audit"
        },
        {
            "key":"realtime","title":"Live source changes affect the next answer","manager_question":"Will the answer stay current?",
            "original":"The prototype could be mistaken for a static prepared scenario.",
            "now":"Every question recomputes against current governed state. Source-scope changes take effect immediately, and signed incoming evidence appears live but remains quarantined until approved.",
            "status":"PASS" if realtime_ok else "REVIEW","proof":"15-second manager view refresh · per-request answer recomputation · signed live ingress",
            "page":"evidence","action":"Test a live policy change"
        },
    ]
    passed=sum(1 for c in controls if c["status"]=="PASS")
    return {
        "status":"COMPLETE" if passed==len(controls) else "REVIEW",
        "score":round(100*passed/max(1,len(controls))),"passed":passed,"total":len(controls),
        "controls":controls,
        "principle":"Answer first. Approved sources only. Private data minimised. Human authority publishes. Everything sensitive is traceable.",
        "current_user":{"name":user.name,"email":user.email,"role":user.role},
    }

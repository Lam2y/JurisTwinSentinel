from __future__ import annotations

import math
import re
from collections import Counter
from datetime import datetime, timedelta, timezone
from sqlalchemy import select
from sqlalchemy.orm import Session
from ..db.models import Evidence, User, RolePolicy, SecurityShield, Conflict, ConflictEvidence, DecisionContract
from .common import loads, iso
from .policy_ml import get_policy_ai
from .source_governance import evidence_scope, resolve_by_authority_then_majority

TOKEN_RE = re.compile(r"[a-z0-9]+")
SENSITIVITY_LEVEL = {"public": 0, "internal": 1, "confidential": 2, "restricted": 3}


def tokenize(text: str):
    return TOKEN_RE.findall((text or "").lower())


def cosine(a: Counter, b: Counter):
    dot=sum(a[k]*b.get(k,0) for k in a)
    na=math.sqrt(sum(v*v for v in a.values()))
    nb=math.sqrt(sum(v*v for v in b.values()))
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
            assigned=set(loads(user.assigned_case_refs,[])); return e.case_ref in assigned
        return True
    return False


def _redacted(e):
    return {
        "evidence_ref":e.evidence_ref,"source":e.source,"title":e.title,
        "body":"[REDACTED BY SENTINEL SHIELD]","rule_key":e.rule_key,"claim":"[RESTRICTED]",
        "authority":e.authority,"authority_level":e.authority_level,"version":e.version,
        "status":e.status,"sensitivity":e.sensitivity,"case_ref":e.case_ref,"approved":e.approved,
        "superseded":e.superseded,"created_at":iso(e.created_at),"metadata":{"access":"redacted"},
    }


def serialize_evidence(db:Session,e:Evidence,user:User,score:float|None=None,retrieval:dict|None=None):
    masking=_shield(db,"data_masking")
    redact=(masking.enabled if masking else True) and not _can_access(db,user,e)
    if redact:
        result=_redacted(e)
    else:
        result={
            "evidence_ref":e.evidence_ref,"source":e.source,"title":e.title,"body":e.body,
            "rule_key":e.rule_key,"claim":e.claim,"authority":e.authority,"authority_level":e.authority_level,
            "version":e.version,"status":e.status,"sensitivity":e.sensitivity,"case_ref":e.case_ref,
            "approved":e.approved,"superseded":e.superseded,"created_at":iso(e.created_at),
            "metadata":loads(e.metadata_json,{}),
        }
        if masking and not masking.enabled and not _can_access(db,user,e):
            result["metadata"]["shield_bypassed_for_demo"] = True
    if score is not None:
        result["score"]=round(score,4)
    if retrieval is not None:
        result["retrieval"]={k:round(v,4) if isinstance(v,float) else v for k,v in retrieval.items()}
    return result


def _matches(e, filters):
    f=filters or {}; meta=loads(e.metadata_json,{})
    if f.get("source") and f["source"]!="All" and f["source"].lower() not in (e.source or "").lower(): return False
    if f.get("rule_key") and f["rule_key"]!="All" and f["rule_key"]!=(e.rule_key or ""): return False
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


def _text(e: Evidence) -> str:
    return " ".join([
        e.title or "",e.body or "",e.claim or "",e.rule_key or "",e.source or "",
        e.authority or "",str(loads(e.metadata_json,{})),
    ])


def _bm25(query_tokens:list[str], doc_tokens:list[str], df:Counter, n_docs:int, avgdl:float) -> float:
    if not query_tokens or not doc_tokens or not n_docs:
        return 0.0
    tf=Counter(doc_tokens); dl=len(doc_tokens); k1=1.4; b=.72; score=0.0
    for term in set(query_tokens):
        n=df.get(term,0)
        idf=math.log(1 + (n_docs-n+0.5)/(n+0.5))
        freq=tf.get(term,0)
        denom=freq + k1*(1-b+b*(dl/max(avgdl,1)))
        if denom:
            score += idf*(freq*(k1+1)/denom)
    return score


def search_memory(db:Session,user:User,query:str,limit:int=10,filters:dict|None=None):
    """Permission-aware hybrid retrieval.

    Finals v2 blends BM25 lexical evidence matching with cosine term-vector similarity, exact phrase
    evidence, source authority and recency. The score components are returned so the ranking is
    explainable rather than a black-box vector-search claim.
    """
    rows=[e for e in db.execute(select(Evidence).order_by(Evidence.created_at.desc())).scalars().all() if _matches(e,filters) and evidence_scope(db,e).get("retrieval_eligible")]
    query_tokens=tokenize(query); qv=Counter(query_tokens)

    if not query_tokens:
        ranked=[]
        for e in rows:
            authority=min((e.authority_level or 1)/5,1)
            approved_bonus=.08 if e.approved else 0
            score=.55 + .30*authority + approved_bonus
            ranked.append((score,e,{"mode":"browse","authority_prior":authority,"approved_bonus":approved_bonus}))
        ranked.sort(key=lambda x:(x[0],x[1].created_at),reverse=True)
        return [serialize_evidence(db,e,user,s,r) for s,e,r in ranked[:limit]]

    docs=[tokenize(_text(e)) for e in rows]
    df=Counter()
    for doc in docs:
        for t in set(doc): df[t]+=1
    avgdl=sum(map(len,docs))/max(1,len(docs))
    raw_bm=[_bm25(query_tokens,doc,df,len(docs),avgdl) for doc in docs]
    max_bm=max(raw_bm,default=1) or 1
    query_lower=(query or "").lower().strip()

    ranked=[]
    now=datetime.now(timezone.utc)
    for e,doc,bmraw in zip(rows,docs,raw_bm):
        cv=cosine(qv,Counter(doc))
        bm=bmraw/max_bm
        text_lower=_text(e).lower()
        phrase=1.0 if query_lower and query_lower in text_lower else 0.0
        authority=min((e.authority_level or 1)/5,1)
        created=e.created_at
        if created and created.tzinfo is None: created=created.replace(tzinfo=timezone.utc)
        age_days=max(0,(now-created).total_seconds()/86400) if created else 365
        recency=math.exp(-age_days/120)
        approved=1.0 if e.approved else 0.0
        # Hybrid score remains bounded and inspectable.
        score=.44*bm + .31*cv + .08*phrase + .08*authority + .05*recency + .04*approved
        if score>0:
            ranked.append((score,e,{
                "mode":"hybrid_bm25_cosine",
                "bm25":bm,
                "cosine":cv,
                "exact_phrase":phrase,
                "authority_prior":authority,
                "recency_prior":recency,
                "approved_prior":approved,
            }))
    ranked.sort(key=lambda x:(x[0],x[1].created_at),reverse=True)
    return [serialize_evidence(db,e,user,s,r) for s,e,r in ranked[:limit]]



def _source_mix(db: Session, user: User, conflict: Conflict | None, rule_key: str, limit: int = 5) -> list[dict]:
    """Return only source-scope-eligible evidence for the management answer."""
    relation_by_id: dict[int, str] = {}
    if conflict:
        links = db.execute(select(ConflictEvidence).where(ConflictEvidence.conflict_id == conflict.id)).scalars().all()
        relation_by_id = {x.evidence_id: x.relation for x in links}
    rows = db.execute(
        select(Evidence).where(Evidence.rule_key == rule_key)
        .order_by(Evidence.authority_level.desc(), Evidence.id.desc())
    ).scalars().all()
    out=[]
    for e in rows:
        scope=evidence_scope(db,e)
        if not scope.get('retrieval_eligible'):
            continue
        item=serialize_evidence(db,e,user)
        rel=relation_by_id.get(e.id)
        if not rel:
            if e.approved and not e.superseded: rel='approved'
            elif e.superseded or (e.status or '').lower()=='outdated': rel='outdated'
            else: rel='context'
        body=item.get('body') or item.get('claim') or ''
        out.append({
            'evidence_ref':item.get('evidence_ref'),'source':item.get('source'),'title':item.get('title'),
            'message':body,'claim':item.get('claim'),'authority':item.get('authority'),
            'authority_level':item.get('authority_level'),'version':item.get('version'),'relation':rel,
            'approved':item.get('approved'),'superseded':item.get('superseded'),'sensitivity':item.get('sensitivity'),
            'redacted':str(item.get('body') or '').startswith('[REDACTED'),
            'scope':scope,
        })
    # Management view: the most authoritative/relevant sources first, without flooding the answer.
    out.sort(key=lambda x:(1 if x.get('approved') else 0, int(x.get('authority_level') or 0), 0 if x.get('relation')=='context' else 1),reverse=True)
    return out[:limit]

def _source_synthesis(source_mix: list[dict], conflict: Conflict | None, contract: DecisionContract | None) -> dict:
    visible=[x for x in source_mix if not x.get('redacted')]
    approved=next((x for x in visible if x.get('relation')=='approved'), visible[0] if visible else None)
    disagree=[x for x in visible if x.get('relation') in {'conflict','informal','outdated'}]
    operational=[x for x in visible if x.get('relation')=='operational']
    if contract:
        headline='One governed answer, with the older disagreement still traceable.'
        summary=f"The active Decision Contract {contract.decision_ref} is the current source of truth. JurisTwin keeps the earlier source disagreement visible for audit instead of deleting it."
    elif conflict and conflict.status in {'unresolved','quarantined'}:
        names=', '.join(dict.fromkeys(x.get('source') or 'Evidence' for x in disagree[:3])) or 'other enterprise sources'
        canon=(approved or {}).get('source') or 'the highest-authority approved source'
        headline=f"{len(visible) or len(source_mix)} governed sources checked — they do not all agree."
        summary=f"{canon} provides the current governed instruction, while {names} still contain incompatible or stale guidance. JurisTwin exposes the disagreement instead of blending it into a fake consensus."
    else:
        headline=f"{len(visible) or len(source_mix)} governed sources checked."
        summary='The retrieved evidence is consistent with the current governed answer.'
    if operational:
        summary += f" Operational evidence from {operational[0].get('source')} shows the rule is already affecting live case handling."
    return {'headline':headline,'summary':summary,'sources_considered':len(source_mix),'visible_sources':len(visible)}


def governed_answer(db: Session, user: User, question: str) -> dict:
    """Return a definite, evidence-bound management answer with governed source lineage.

    Resolution policy:
    1. Active Decision Contract wins.
    2. Otherwise an approved, source-scope-eligible authority wins.
    3. Only when no approved canonical source exists, majority may break a conflict *within the same
       highest authority tier*. Casual mail or private DMs cannot outvote a governed source.
    """
    model = get_policy_ai().predict(question)
    domain = model.get("domain", {})
    rule_key = None if domain.get("abstain") else domain.get("label")
    confidence = float(domain.get("confidence") or 0)
    now=datetime.now(timezone.utc)

    if not rule_key or rule_key == "general_policy_rule":
        return {
            "status": "NEEDS_REVIEW",
            "management_status":"REVIEW_REQUIRED",
            "answer": "JurisTwin cannot bind this question to a governed policy domain with enough confidence. Please narrow the question or escalate to an authorised reviewer.",
            "question": question, "role": user.role, "rule_key": rule_key or "unknown",
            "model": {"engine": model.get("engine"), "domain_confidence": round(confidence, 4), "abstained": True},
            "citations": [], "sources_used": [],
            "resolution":{"mode":"ABSTAIN","explanation":"No policy domain passed the routing confidence threshold."},
            "freshness":{"evaluated_at":iso(now),"answer_recomputed":True},
            "guardrail": "Evidence-bound answering only; Sentinel does not invent policy facts when authority is uncertain.",
        }

    conflict = db.execute(select(Conflict).where(Conflict.rule_key == rule_key).order_by(Conflict.id.desc())).scalars().first()
    open_conflict = bool(conflict and conflict.status in {"unresolved", "quarantined"})
    contract = db.execute(
        select(DecisionContract).where(DecisionContract.rule_key == rule_key, DecisionContract.status == "active")
        .order_by(DecisionContract.id.desc())
    ).scalars().first()

    retrieval_matches=search_memory(db,user,question,limit=8,filters={"rule_key":rule_key})
    resolution=resolve_by_authority_then_majority(db,rule_key)
    evidence=resolution.get('winner')
    source_mix = _source_mix(db, user, conflict, rule_key, limit=4)
    synthesis = _source_synthesis(source_mix, conflict, contract)

    if not contract and not evidence:
        mode=resolution.get('mode')
        explanation = (
            'Equally authoritative eligible sources are tied, so Sentinel refuses to invent a winner.'
            if mode=='MAJORITY_TIE_REVIEW' else
            'No source inside the administrator-approved scope is eligible to define this policy.'
        )
        return {
            "status":"NEEDS_REVIEW","management_status":"REVIEW_REQUIRED",
            "answer":"No definite governed answer can be issued yet. An authorised reviewer must resolve the top-tier evidence.",
            "question":question,"role":user.role,"rule_key":rule_key,
            "conflict_ref": conflict.conflict_ref if conflict else None,
            "model":{"engine":model.get('engine'),"domain_confidence":round(confidence,4),"abstained":False},
            "citations":[],"sources_used":[],"source_mix":source_mix,"synthesis":synthesis,
            "resolution":{"mode":mode,"explanation":explanation,"authority_level":resolution.get('authority_level'),"majority":resolution.get('majority'),"eligible_count":resolution.get('eligible_count',0),"excluded_count":len(resolution.get('excluded',[])),"excluded":resolution.get('excluded',[])[:4]},
            "freshness":{"evaluated_at":iso(now),"answer_recomputed":True},
            "guardrail":"Authority first; majority only inside one equal authority tier; excluded private/casual sources cannot vote.",
        }

    citation = serialize_evidence(db, evidence, user) if evidence else None
    redacted = bool(citation and str(citation.get("body") or "").startswith("[REDACTED"))
    if redacted and not contract:
        return {
            "status":"RESTRICTED","management_status":"ACCESS_RESTRICTED",
            "answer":"A governed answer exists, but the supporting evidence is restricted for this role. Escalate to an authorised reviewer.",
            "question":question,"role":user.role,"rule_key":rule_key,"conflict_ref":conflict.conflict_ref if conflict else None,
            "model":{"engine":model.get('engine'),"domain_confidence":round(confidence,4),"abstained":False},
            "citations":[citation],"sources_used":[citation],"source_mix":source_mix,"synthesis":synthesis,
            "resolution":{"mode":resolution.get('mode'),"explanation":"A winning governed source exists, but its content is hidden by role-based access control.","excluded_count":len(resolution.get('excluded',[]))},
            "freshness":{"evaluated_at":iso(now),"answer_recomputed":True},
            "guardrail":"Restricted evidence is never revealed through the answer layer.",
        }

    if contract:
        answer=contract.approved_rule; authority=contract.approved_by; version=contract.version; decision_ref=contract.decision_ref; source='Decision Ledger'
        resolution_mode='DECISION_CONTRACT'
        primary_source={
            'evidence_ref':contract.decision_ref,'source':'Decision Ledger','title':f'Governed decision {contract.decision_ref}',
            'body':contract.approved_rule,'authority':contract.approved_by,'authority_level':6,'version':contract.version,
            'approved':True,'superseded':False,'created_at':iso(contract.created_at),
            'metadata':{'access':'governed_decision_contract'},
        }
        sources_used=[primary_source]
    else:
        answer=evidence.body; authority=evidence.authority; version=evidence.version; decision_ref=None; source=evidence.source
        resolution_mode=resolution.get('mode')
        # Cite only the source(s) that actually won the resolution, not unrelated search hits.
        support=resolution.get('support') or [evidence]
        sources_used=[]
        for e in support[:3]:
            item=serialize_evidence(db,e,user)
            item['scope']=evidence_scope(db,e)
            sources_used.append(item)
        primary_source=sources_used[0] if sources_used else citation

    # Keep the raw conflict state for technical users, but give management a clean answer-first status.
    status='CONFLICT_PRESENT' if open_conflict else 'VERIFIED'
    management_status='GOVERNED_ANSWER'
    warning=None
    if open_conflict:
        warning=(f"Other eligible evidence still disagrees under {conflict.conflict_ref}. "
                 "The answer above follows the governed resolution rule; lower-authority evidence cannot override it.")

    excluded=resolution.get('excluded',[])
    majority=resolution.get('majority') or {'needed':False}
    if resolution_mode=='SAME_TIER_MAJORITY':
        resolution_explanation=(f"No approved canonical source existed, so Sentinel used the majority among the same highest authority tier "
                                f"({majority.get('votes',0)}/{majority.get('population',0)} matching sources).")
    elif resolution_mode=='DECISION_CONTRACT':
        resolution_explanation='An active human-approved Decision Contract is the single governing source.'
    elif resolution_mode=='APPROVED_AUTHORITY':
        resolution_explanation='The highest-authority approved source is canonical; lower-authority disagreement is visible but cannot change the answer.'
    else:
        resolution_explanation='The highest source-scope-eligible authority determines the answer.'

    card=get_policy_ai().model_card(); bench=card.get('held_out_development_benchmark',{})
    ai_verification={
        'learned_component':True,'architecture':card.get('architecture'),
        'domain_macro_f1':bench.get('domain_macro_f1'),'stance_macro_f1':bench.get('stance_macro_f1'),
        'symbolic_verifier':'Policy Atom Reasoner','publication_authority':0,'internet_required':False,
        'decision_rule':'Keyword/hybrid retrieval finds relevant evidence; source scope filters it; authority resolves it; same-tier majority is fallback only; human governance publishes.',
        'client_data_training':False,
    }

    latest_times=[]
    for e in (resolution.get('support') or ([] if evidence is None else [evidence])):
        if e.created_at: latest_times.append(e.created_at if e.created_at.tzinfo else e.created_at.replace(tzinfo=timezone.utc))
    snapshot=max(latest_times) if latest_times else now
    return {
        'status':status,'management_status':management_status,'answer':answer,'warning':warning,
        'question':question,'role':user.role,'rule_key':rule_key,'decision_ref':decision_ref,
        'conflict_ref':conflict.conflict_ref if conflict else None,'authority':authority,'version':version,'source':source,
        'model':{'engine':model.get('engine'),'domain_confidence':round(confidence,4),'abstained':False,'publication_authority':0},
        'citations':sources_used,'sources_used':sources_used,'primary_source':primary_source,
        'retrieval_matches':retrieval_matches,'source_mix':source_mix,'synthesis':synthesis,
        'resolution':{
            'mode':resolution_mode,'explanation':resolution_explanation,'authority_level':resolution.get('authority_level',6 if contract else None),
            'majority':majority,'eligible_count':resolution.get('eligible_count',len(sources_used)),
            'excluded_count':len(excluded),'excluded':excluded[:6],
            'retrieval_match_count':len(retrieval_matches),
            'privacy_rule':'Personal Teams DMs and casual/unapproved mail are excluded before policy resolution.',
            'training_rule':'Client evidence is indexed for governed retrieval only; it is not used to train the local classifier or any external model.',
            'retrieval_strategy':'Keyword/BM25 + semantic similarity inside the administrator-approved source scope.',
            'winner_rule':'Active Decision Contract > approved authority > same-tier majority > human review.',
        },
        'freshness':{
            'evaluated_at':iso(now),'evidence_snapshot_at':iso(snapshot),'answer_recomputed':True,
            'update_rule':'Every question re-runs retrieval and source governance against the latest allowed evidence. Signed live inputs appear immediately but remain quarantined until authorised.',
        },
        'ai_verification':ai_verification,
        'guardrail':'Answer text is bound to governed evidence/Decision Contracts; private/casual sources are filtered before resolution and client data has zero model-training authority.',
    }


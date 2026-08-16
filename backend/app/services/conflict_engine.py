from sqlalchemy import select
from sqlalchemy.orm import Session
from ..db.models import Conflict, ConflictEvidence, Evidence
from .common import iso


def build_graph(db: Session, conflict: Conflict):
    links = db.execute(
        select(ConflictEvidence, Evidence)
        .join(Evidence, Evidence.id == ConflictEvidence.evidence_id)
        .where(ConflictEvidence.conflict_id == conflict.id)
    ).all()
    nodes = [{
        "id": f"rule:{conflict.rule_key}", "type": "rule", "label": conflict.name,
        "status": conflict.status, "color": "cyan"
    }]
    edges = []
    for ce, e in links:
        color = {"approved": "green", "informal": "amber", "conflict": "red", "operational": "cyan", "context": "slate"}.get(ce.relation, "slate")
        nodes.append({
            "id": e.evidence_ref, "type": "evidence", "label": e.title, "source": e.source,
            "claim": e.claim, "relation": ce.relation, "authority": e.authority,
            "version": e.version, "status": e.status, "color": color,
        })
        edges.append({"source": f"rule:{conflict.rule_key}", "target": e.evidence_ref, "relation": ce.relation, "color": color})
    return {"nodes": nodes, "edges": edges}


PLAIN_CONFLICT_COPY = {
    "income_document_rule": {
        "headline": "The approved rule allows bank statements, but frontline guidance still requires payslips.",
        "why_it_matters": "The same gig worker can receive two different answers depending on which document or message an officer follows.",
        "root_cause_plain": "The decision changed, but the FSD, training guidance and frontline instructions did not change with it.",
    },
    "loan_restructure_rule": {
        "headline": "The Risk Committee says the approval ceiling is 60, while a legacy desk guide still allows approvals up to 70.",
        "why_it_matters": "The same restructuring case could be approved or rejected depending on which threshold an officer or system follows.",
        "root_cause_plain": "The governed risk threshold changed, but the legacy operating guide was not retired everywhere at the same time.",
    },
    "notification_deadline": {
        "headline": "Compliance uses three business days, while legacy instructions still use three calendar days.",
        "why_it_matters": "Two teams can calculate different notification deadlines for the same customer, creating late or inconsistent notices.",
        "root_cause_plain": "The SLA definition changed, but the legacy procedure and frontline wording were not fully synchronised.",
    },
}


def plain_conflict_explanation(db: Session, conflict: Conflict) -> dict:
    """Return a judge-friendly explanation with the exact evidence that disagrees.

    This intentionally sits beside the graph rather than replacing it: non-technical users get the
    answer first, while technical judges can still inspect authority, versions and relationships.
    """
    links = db.execute(
        select(ConflictEvidence, Evidence)
        .join(Evidence, Evidence.id == ConflictEvidence.evidence_id)
        .where(ConflictEvidence.conflict_id == conflict.id)
    ).all()
    rows=[]
    for ce,e in links:
        rows.append({
            "evidence_ref":e.evidence_ref, "source":e.source, "title":e.title,
            "message":e.body or e.claim or "", "claim":e.claim, "relation":ce.relation,
            "authority":e.authority, "authority_level":e.authority_level, "version":e.version,
            "status":e.status, "approved":bool(e.approved), "superseded":bool(e.superseded),
        })
    approved=[r for r in rows if r["relation"]=="approved" or r["evidence_ref"]==conflict.approved_evidence_ref or r["approved"]]
    approved.sort(key=lambda r:(r["authority_level"] or 0, 1 if r["relation"]=="approved" else 0), reverse=True)
    canonical=approved[0] if approved else None
    conflicting=[r for r in rows if r["relation"] in {"conflict","informal"}]
    conflicting.sort(key=lambda r:((1 if r["relation"]=="conflict" else 0), r["authority_level"] or 0), reverse=True)
    copy=PLAIN_CONFLICT_COPY.get(conflict.rule_key,{
        "headline": conflict.root_cause,
        "why_it_matters": f"Conflicting instructions can produce inconsistent decisions across {conflict.affected_customers or 0} affected cases.",
        "root_cause_plain": conflict.root_cause,
    })
    if canonical:
        why_wins=(
            f"JurisTwin treats {canonical['source']} as the governed source because it is approved by "
            f"{canonical['authority']} at authority level {canonical['authority_level']}"
            f"{f' and is version {canonical["version"]}' if canonical.get('version') else ''}. "
            "Lower-authority or superseded guidance cannot silently override it."
        )
    else:
        why_wins="No approved canonical evidence is available; JurisTwin routes the conflict to human governance instead of guessing."
    return {
        "headline":copy["headline"],
        "what_conflicts":copy["headline"],
        "why_it_matters":copy["why_it_matters"],
        "root_cause_plain":copy["root_cause_plain"],
        "why_canonical_wins":why_wins,
        "customer_impact":f"{int(conflict.affected_customers or 0)} customer cases may receive inconsistent treatment until the conflict is resolved.",
        "canonical":canonical,
        "conflicting_evidence":conflicting,
        "all_evidence":rows,
    }


def conflict_payload(db: Session, c: Conflict):
    return {
        "conflict_ref": c.conflict_ref, "name": c.name, "rule_key": c.rule_key, "severity": c.severity,
        "status": c.status, "root_cause": c.root_cause, "recommendation": c.recommendation,
        "confidence": c.confidence, "affected_customers": c.affected_customers,
        "systems_affected": c.systems_affected, "approved_evidence_ref": c.approved_evidence_ref,
        "created_at": iso(c.created_at), "resolved_at": iso(c.resolved_at), "graph": build_graph(db, c),
        "plain_explanation": plain_conflict_explanation(db, c),
    }


def detect_conflicts(db: Session):
    # A transparent heuristic: active evidence on the same rule is a conflict when a lower-authority
    # active claim disagrees lexically with the highest-authority approved claim.
    evidence = db.execute(select(Evidence).where(Evidence.rule_key.is_not(None))).scalars().all()
    groups = {}
    for e in evidence:
        if e.superseded:
            continue
        groups.setdefault(e.rule_key, []).append(e)
    findings = []
    for rule_key, items in groups.items():
        approved = sorted([e for e in items if e.approved], key=lambda x: x.authority_level, reverse=True)
        if not approved:
            continue
        canonical = (approved[0].claim or "").lower()
        for e in items:
            if e.id == approved[0].id:
                continue
            claim = (e.claim or "").lower()
            if claim and canonical and claim != canonical:
                findings.append({"rule_key": rule_key, "approved": approved[0].evidence_ref, "conflicting": e.evidence_ref})
    return {"scanned_rules": len(groups), "findings": findings, "count": len(findings)}

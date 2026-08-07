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


def conflict_payload(db: Session, c: Conflict):
    return {
        "conflict_ref": c.conflict_ref, "name": c.name, "rule_key": c.rule_key, "severity": c.severity,
        "status": c.status, "root_cause": c.root_cause, "recommendation": c.recommendation,
        "confidence": c.confidence, "affected_customers": c.affected_customers,
        "systems_affected": c.systems_affected, "approved_evidence_ref": c.approved_evidence_ref,
        "created_at": iso(c.created_at), "resolved_at": iso(c.resolved_at), "graph": build_graph(db, c),
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

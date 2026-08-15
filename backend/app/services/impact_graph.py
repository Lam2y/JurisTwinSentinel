"""Explainable blast-radius graph traversal for JurisTwin Sentinel v3."""
from __future__ import annotations
from collections import deque
from sqlalchemy import select
from sqlalchemy.orm import Session
from ..db.models import CustomerCase, Conflict, Integration

RULE_DEPENDENCIES = {
    "income_document_rule": [
        ("process:income_verification", "Income Verification", "process"),
        ("system:customer_core", "Customer Core", "system"),
        ("system:document_vault", "Document Vault", "system"),
        ("system:qa", "QA Repository", "system"),
        ("team:operations", "Operations Officers", "team"),
    ],
    "loan_restructure_rule": [
        ("process:restructure", "Loan Restructuring", "process"),
        ("system:customer_core", "Customer Core", "system"),
        ("team:risk", "Risk Operations", "team"),
    ],
    "notification_deadline": [
        ("process:notification", "Customer Notification", "process"),
        ("system:outlook", "Outlook Extractor", "system"),
        ("team:operations", "Operations Officers", "team"),
    ],
}


def build_impact_graph(db: Session, rule_key: str, conflict_ref: str | None = None) -> dict:
    nodes = {}
    edges = []
    adjacency = {}
    def add_node(node_id, label, kind, **extra):
        nodes[node_id] = {"id": node_id, "label": label, "type": kind, **extra}
        adjacency.setdefault(node_id, [])
    def add_edge(a, b, relation):
        edges.append({"source": a, "target": b, "relation": relation})
        adjacency.setdefault(a, []).append(b)

    rule_id = f"rule:{rule_key}"
    add_node(rule_id, rule_key.replace("_", " ").title(), "policy", critical=True)

    conflict = None
    if conflict_ref:
        conflict = db.execute(select(Conflict).where(Conflict.conflict_ref == conflict_ref)).scalar_one_or_none()
    if not conflict:
        conflict = db.execute(select(Conflict).where(Conflict.rule_key == rule_key).order_by(Conflict.id.asc())).scalars().first()
    conflict_id = None
    if conflict:
        conflict_id = f"conflict:{conflict.conflict_ref}"
        add_node(conflict_id, conflict.name, "conflict", severity=conflict.severity)
        add_edge(rule_id, conflict_id, "governs")
        root = conflict_id
    else:
        root = rule_id

    dependencies = RULE_DEPENDENCIES.get(rule_key, [("process:governance", "Governance Review", "process")])
    for node_id, label, kind in dependencies:
        add_node(node_id, label, kind)
        add_edge(root, node_id, "impacts")

    # Cases are sourced from actual operational DB state, not a fixed impact number.
    cases = []
    if conflict:
        cases = db.execute(select(CustomerCase).where(CustomerCase.conflict_ref == conflict.conflict_ref)).scalars().all()
    if not cases:
        cohort = "gig-worker-income" if rule_key == "income_document_rule" else None
        all_cases = db.execute(select(CustomerCase)).scalars().all()
        if cohort:
            cases = [c for c in all_cases if cohort in (c.metadata_json or "")]

    process_targets = [d[0] for d in dependencies if d[2] == "process"] or [root]
    parent = process_targets[0]
    for c in cases:
        cid = f"case:{c.case_ref}"
        add_node(cid, c.case_ref, "customer_case", risk=c.risk_status, pending_days=c.pending_days)
        add_edge(parent, cid, "blocks")

    # BFS calculates reachable impact and records shortest explainability paths.
    q = deque([(rule_id, [rule_id])])
    seen = {rule_id}
    paths = {}
    while q:
        cur, path = q.popleft()
        for nxt in adjacency.get(cur, []):
            if nxt in seen:
                continue
            seen.add(nxt)
            npath = path + [nxt]
            paths[nxt] = npath
            q.append((nxt, npath))

    affected_case_ids = [n for n in seen if nodes.get(n, {}).get("type") == "customer_case"]
    system_ids = [n for n in seen if nodes.get(n, {}).get("type") == "system"]
    sample_paths = []
    for cid in affected_case_ids[:5]:
        sample_paths.append({
            "case_ref": cid.split(":", 1)[1],
            "path": [{"id": x, "label": nodes[x]["label"], "type": nodes[x]["type"]} for x in paths.get(cid, [rule_id, cid])],
        })
    return {
        "algorithm": "Breadth-first dependency traversal (BFS)",
        "root": rule_id,
        "nodes": list(nodes.values()),
        "edges": edges,
        "reachable_nodes": len(seen),
        "affected_cases": len(affected_case_ids),
        "affected_systems": len(system_ids),
        "sample_paths": sample_paths,
        "explanation": f"Blast radius is derived by traversing governed dependencies from {rule_key} into live case records; {len(affected_case_ids)} reachable customer cases were found.",
    }

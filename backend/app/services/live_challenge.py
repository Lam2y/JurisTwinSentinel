"""Live, judge-controlled evidence challenge pipeline.

The implementation is deliberately local and explainable: it performs deterministic semantic
feature extraction, policy stance classification, authority-aware contradiction analysis and
blast-radius calculation without requiring an external LLM or internet connection. This keeps the
Grand Finals demonstration resilient while still accepting genuinely unseen text at runtime.
"""
from __future__ import annotations

import hashlib
import re
from time import perf_counter
from uuid import uuid4
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..db.models import (
    CustomerCase, Evidence, Conflict, ConflictEvidence, DecisionContract,
    LiveChallenge,
)
from .common import dumps, loads, iso
from .ledger import append_entry
from .policy_reasoner import extract_policy_atoms, compare_policy_atoms
from .impact_graph import build_impact_graph

TOKEN_RE = re.compile(r"[a-z0-9]+")

RULE_PROFILES = {
    "income_document_rule": {
        "label": "Income-document eligibility",
        "keywords": {
            "bank", "statement", "payslip", "income", "salary", "wage", "gig",
            "employment", "proof", "document", "earnings", "worker",
        },
        "positive": {
            "accept", "accepted", "allow", "allowed", "eligible", "valid", "may",
            "can", "permitted", "sufficient", "standalone", "alternative",
        },
        "negative": {
            "reject", "rejected", "not", "no", "must", "mandatory", "compulsory",
            "require", "requires", "required", "prohibit", "prohibited", "invalid",
            "cannot", "only", "additional",
        },
    },
    "loan_restructure_rule": {
        "label": "Loan restructuring approval",
        "keywords": {
            "restructure", "restructuring", "loan", "approval", "threshold", "risk",
            "arrears", "repayment", "tenure", "instalment", "installment",
        },
        "positive": {"approve", "approved", "allow", "eligible", "within", "accept"},
        "negative": {"reject", "deny", "denied", "above", "exceed", "not", "cannot"},
    },
    "notification_deadline": {
        "label": "Customer notification deadline",
        "keywords": {
            "notify", "notification", "deadline", "sla", "day", "days", "business",
            "calendar", "customer", "notice", "inform",
        },
        "positive": {"business", "working", "within", "deadline"},
        "negative": {"calendar", "late", "after", "not"},
    },
}


def _tokens(text: str) -> set[str]:
    return set(TOKEN_RE.findall((text or "").lower()))


def _infer_rule(text: str, explicit: str | None = None) -> tuple[str, float, list[str]]:
    if explicit:
        return explicit, 0.99, ["Rule key supplied explicitly by the operator."]
    tokens = _tokens(text)
    ranked = []
    for key, profile in RULE_PROFILES.items():
        overlap = tokens & profile["keywords"]
        denominator = max(3, min(len(profile["keywords"]), 8))
        score = min(1.0, len(overlap) / denominator)
        ranked.append((score, key, sorted(overlap)))
    score, key, overlap = max(ranked, key=lambda x: x[0])
    if score <= 0:
        # Unknown material is safely routed to a general policy rule rather than falsely claiming
        # knowledge about it.
        return "general_policy_rule", 0.42, ["No strong domain signature; routed to general policy review."]
    return key, round(0.58 + score * 0.38, 3), [f"Matched policy terms: {', '.join(overlap[:8])}."]


def _stance(rule_key: str, text: str) -> tuple[str, float, list[str]]:
    tokens = _tokens(text)
    profile = RULE_PROFILES.get(rule_key)
    if not profile:
        return "UNSPECIFIED", 0.45, ["No specialised stance lexicon for this rule."]
    pos = tokens & profile["positive"]
    neg = tokens & profile["negative"]
    # Phrases carry more meaning than single-token polarity for policy text.
    lower = text.lower()
    phrase_negative = any(p in lower for p in [
        "not accepted", "no longer accepted", "must provide", "must submit",
        "payslips are compulsory", "bank statements are not", "cannot be used",
        "requires additional", "only payslip", "only payslips",
    ])
    phrase_positive = any(p in lower for p in [
        "bank statements are accepted", "bank statement is accepted", "may submit",
        "can submit", "acceptable income evidence", "alternative income documents",
    ])
    if phrase_negative:
        neg = set(neg) | {"policy-negative-phrase"}
    if phrase_positive:
        pos = set(pos) | {"policy-positive-phrase"}
    if len(neg) > len(pos):
        label = "RESTRICTIVE"
    elif len(pos) > len(neg):
        label = "PERMISSIVE"
    else:
        label = "UNSPECIFIED"
    confidence = min(0.96, 0.52 + 0.07 * abs(len(pos) - len(neg)) + (0.12 if phrase_negative or phrase_positive else 0))
    reasons = []
    if pos:
        reasons.append(f"Permissive cues: {', '.join(sorted(pos)[:6])}.")
    if neg:
        reasons.append(f"Restrictive cues: {', '.join(sorted(neg)[:6])}.")
    if not reasons:
        reasons.append("No decisive permission/restriction language detected.")
    return label, round(confidence, 3), reasons


def _canonical_for(db: Session, rule_key: str) -> Evidence | None:
    rows = db.execute(
        select(Evidence).where(
            Evidence.rule_key == rule_key,
            Evidence.approved.is_(True),
            Evidence.superseded.is_(False),
        )
    ).scalars().all()
    if not rows:
        return None
    rows.sort(key=lambda e: (e.authority_level or 0, e.created_at), reverse=True)
    return rows[0]


def _semantic_overlap(a: str, b: str) -> float:
    ta, tb = _tokens(a), _tokens(b)
    if not ta or not tb:
        return 0.0
    return len(ta & tb) / len(ta | tb)


def _conflict_for_rule(db: Session, rule_key: str) -> Conflict | None:
    return db.execute(
        select(Conflict).where(Conflict.rule_key == rule_key).order_by(Conflict.id.asc())
    ).scalars().first()


def _blast_radius(db: Session, rule_key: str, existing: Conflict | None) -> tuple[int, list[str]]:
    if existing:
        linked = db.execute(
            select(CustomerCase).where(CustomerCase.conflict_ref == existing.conflict_ref)
        ).scalars().all()
        if linked:
            return len(linked), [c.case_ref for c in linked[:8]]
        if existing.affected_customers:
            return int(existing.affected_customers), []
    # Conservative fallback: only count cases whose metadata/rule context actually references the rule.
    cases = db.execute(select(CustomerCase)).scalars().all()
    matched = []
    needle = rule_key.replace("_", " ")
    for c in cases:
        blob = f"{c.current_blocker or ''} {c.application_type or ''} {c.metadata_json or ''}".lower()
        if needle in blob:
            matched.append(c.case_ref)
    return len(matched), matched[:8]


def _severity(blast_radius: int, contradiction_confidence: float) -> str:
    if blast_radius >= 20 and contradiction_confidence >= 0.82:
        return "Critical"
    if blast_radius >= 10 or contradiction_confidence >= 0.82:
        return "High"
    if blast_radius >= 3:
        return "Medium"
    return "Low"


def run_live_challenge(db: Session, body, user) -> dict:
    t0 = perf_counter()
    stages = []

    def mark(name: str, start: float, detail: str):
        stages.append({
            "stage": name,
            "latency_ms": round((perf_counter() - start) * 1000, 2),
            "detail": detail,
        })

    # 1. Understand the unseen input.
    s = perf_counter()
    rule_key, rule_conf, rule_reasons = _infer_rule(f"{body.title} {body.body}", body.rule_key)
    stance, stance_conf, stance_reasons = _stance(rule_key, body.body)
    mark("Policy classification", s, f"{rule_key} · {stance}")

    # 2. Retrieve the highest-authority canonical evidence already in Enterprise Memory.
    s = perf_counter()
    canonical = _canonical_for(db, rule_key)
    canonical_stance, canonical_stance_conf, _ = _stance(
        rule_key, (canonical.claim or canonical.body) if canonical else ""
    )
    incoming_atoms = extract_policy_atoms(body.body, rule_key)
    canonical_atoms = extract_policy_atoms((canonical.claim or canonical.body) if canonical else "", rule_key)
    atom_reasoning = compare_policy_atoms(canonical_atoms, incoming_atoms) if canonical else {
        "collision": False, "collisions": [], "alignments": [], "confidence": 0.55,
        "engine": "JurisTwin Policy Atom Reasoner v3",
    }
    mark("Canonical evidence retrieval", s, canonical.evidence_ref if canonical else "No approved canonical evidence")

    # 3. Authority-aware contradiction decision. Unspecified wording is quarantined for review
    # rather than falsely classified as a contradiction.
    s = perf_counter()
    overlap = _semantic_overlap(body.body, (canonical.claim or canonical.body) if canonical else "")
    opposite = bool(canonical is not None and (atom_reasoning.get("collision") or (stance != "UNSPECIFIED" and canonical_stance != "UNSPECIFIED" and stance != canonical_stance)))
    if canonical is None:
        verdict = "NOVEL"
        contradiction_conf = 0.55
    elif opposite:
        verdict = "CONTRADICTION"
        contradiction_conf = min(0.99, max(atom_reasoning.get("confidence", 0.0), 0.72 + 0.12 * stance_conf + 0.08 * canonical_stance_conf + 0.06 * min(1.0, overlap * 3)))
    elif stance == "UNSPECIFIED":
        verdict = "NEEDS_REVIEW"
        contradiction_conf = 0.58
    else:
        verdict = "ALIGNED"
        contradiction_conf = min(0.95, 0.70 + 0.13 * stance_conf + 0.08 * min(1.0, overlap * 3))
    contradiction_conf = round(contradiction_conf, 3)
    mark("Contradiction analysis", s, f"{verdict} · {contradiction_conf:.1%} confidence")

    # 4. Determine operational impact before persistence.
    s = perf_counter()
    existing_conflict = _conflict_for_rule(db, rule_key)
    impact_graph = build_impact_graph(db, rule_key, existing_conflict.conflict_ref if existing_conflict else None)
    blast_radius = impact_graph.get("affected_cases", 0)
    sample_cases = [x.get("case_ref") for x in impact_graph.get("sample_paths", [])]
    # Preserve conservative fallback for domains with no dependency cohort.
    if blast_radius == 0:
        blast_radius, sample_cases = _blast_radius(db, rule_key, existing_conflict)
    mark("BFS dependency traversal", s, f"{blast_radius} reachable customer cases through {impact_graph.get('reachable_nodes',0)} governed nodes")

    # 5. Persist the live evidence. It is deliberately NOT approved simply because it was injected.
    s = perf_counter()
    content_sha256 = hashlib.sha256(body.body.strip().encode("utf-8")).hexdigest()
    ev = Evidence(
        evidence_ref=f"EV-LIVE-{uuid4().hex[:8].upper()}",
        source=body.source.strip(),
        title=body.title.strip(),
        body=body.body.strip(),
        rule_key=rule_key,
        claim=body.body.strip(),
        authority=body.authority.strip(),
        authority_level=body.authority_level,
        version="live",
        status="quarantined" if verdict in {"CONTRADICTION", "NEEDS_REVIEW", "NOVEL"} else "active",
        sensitivity=body.sensitivity,
        approved=False,
        superseded=False,
        metadata_json=dumps({
            "origin": "judge_challenge",
            "classification_confidence": rule_conf,
            "stance": stance,
            "verdict": verdict,
            "content_sha256": content_sha256,
        }),
    )
    db.add(ev)
    db.flush()
    mark("Governed evidence ingestion", s, f"{ev.evidence_ref} persisted as non-canonical evidence")

    generated_conflict = None
    decision = db.execute(
        select(DecisionContract).where(
            DecisionContract.rule_key == rule_key,
            DecisionContract.status == "active",
        ).order_by(DecisionContract.id.desc())
    ).scalars().first()

    # 6. Materialise a challenge-specific conflict only when the unseen input actually contradicts
    # canonical evidence. This makes the graph/audit trail real without modifying the approved rule.
    if verdict == "CONTRADICTION" and canonical:
        s = perf_counter()
        generated_conflict = Conflict(
            conflict_ref=f"CF-LIVE-{uuid4().hex[:6].upper()}",
            name=f"Live contradiction · {RULE_PROFILES.get(rule_key, {}).get('label', rule_key)}",
            rule_key=rule_key,
            severity=_severity(blast_radius, contradiction_conf),
            status="quarantined",
            root_cause=(
                f"Unseen {body.source} evidence conflicts with approved {canonical.source} evidence. "
                "Sentinel quarantined the new claim instead of silently replacing the governed rule."
            ),
            recommendation=(
                "Require authority validation and human approval before propagation. Compare the live evidence "
                "against the active decision contract and affected cases."
            ),
            confidence=contradiction_conf,
            affected_customers=blast_radius,
            systems_affected=max(1, min(5, 1 + blast_radius // 8)),
            approved_evidence_ref=canonical.evidence_ref,
        )
        db.add(generated_conflict)
        db.flush()
        db.add(ConflictEvidence(conflict_id=generated_conflict.id, evidence_id=canonical.id, relation="approved"))
        db.add(ConflictEvidence(conflict_id=generated_conflict.id, evidence_id=ev.id, relation="conflict"))
        mark("Conflict materialisation", s, generated_conflict.conflict_ref)

    analysis = {
        "rule_key": rule_key,
        "rule_confidence": rule_conf,
        "stance": stance,
        "stance_confidence": stance_conf,
        "verdict": verdict,
        "contradiction_confidence": contradiction_conf,
        "semantic_overlap": round(overlap, 3),
        "policy_atoms": {"incoming": incoming_atoms, "canonical": canonical_atoms, "reasoning": atom_reasoning},
        "impact_graph": impact_graph,
        "blast_radius": blast_radius,
        "sample_cases": sample_cases,
        "provenance": {
            "content_sha256": content_sha256,
            "source": body.source.strip(),
            "ingest_mode": "runtime_unseen_input",
            "canonical_mutated": False,
        },
        "canonical": {
            "evidence_ref": canonical.evidence_ref,
            "source": canonical.source,
            "title": canonical.title,
            "claim": canonical.claim or canonical.body,
            "authority": canonical.authority,
            "authority_level": canonical.authority_level,
            "stance": canonical_stance,
        } if canonical else None,
        "decision_guard": {
            "decision_ref": decision.decision_ref,
            "version": decision.version,
            "approved_rule": decision.approved_rule,
            "action": "BLOCK_SILENT_OVERWRITE" if verdict == "CONTRADICTION" else "NO_BLOCK_REQUIRED",
        } if decision else {
            "decision_ref": None,
            "action": "HUMAN_REVIEW_BEFORE_CANONICALISATION",
        },
        "reasons": rule_reasons + stance_reasons + ([
            "Structured policy-atom comparison found an incompatible governed modality."
        ] if opposite else []),
        "stages": stages,
    }

    challenge = LiveChallenge(
        challenge_ref=f"CH-{uuid4().hex[:8].upper()}",
        source=body.source.strip(),
        title=body.title.strip(),
        body=body.body.strip(),
        inferred_rule_key=rule_key,
        inferred_claim=body.body.strip(),
        evidence_ref=ev.evidence_ref,
        conflict_ref=generated_conflict.conflict_ref if generated_conflict else None,
        verdict=verdict,
        confidence=contradiction_conf,
        blast_radius=blast_radius,
        status="quarantined" if verdict in {"CONTRADICTION", "NEEDS_REVIEW", "NOVEL"} else "observed",
        analysis_json=dumps(analysis),
        created_by=user.email,
    )
    db.add(challenge)
    db.flush()

    append_entry(db, "LIVE_EVIDENCE_CHALLENGE", user.email, {
        "challenge_ref": challenge.challenge_ref,
        "evidence_ref": ev.evidence_ref,
        "rule_key": rule_key,
        "verdict": verdict,
        "confidence": contradiction_conf,
        "blast_radius": blast_radius,
        "conflict_ref": generated_conflict.conflict_ref if generated_conflict else None,
        "governance_action": analysis["decision_guard"]["action"],
        "content_sha256": content_sha256,
    }, decision.decision_ref if decision else None)
    db.commit()
    db.refresh(challenge)

    total_ms = round((perf_counter() - t0) * 1000, 2)
    analysis["total_latency_ms"] = total_ms
    # Update stored analysis once with final latency for reproducible history.
    challenge.analysis_json = dumps(analysis)
    db.commit()

    return serialize_challenge(challenge)


def serialize_challenge(c: LiveChallenge) -> dict:
    return {
        "challenge_ref": c.challenge_ref,
        "source": c.source,
        "title": c.title,
        "body": c.body,
        "rule_key": c.inferred_rule_key,
        "evidence_ref": c.evidence_ref,
        "conflict_ref": c.conflict_ref,
        "verdict": c.verdict,
        "confidence": c.confidence,
        "blast_radius": c.blast_radius,
        "status": c.status,
        "analysis": loads(c.analysis_json, {}),
        "created_by": c.created_by,
        "created_at": iso(c.created_at),
    }

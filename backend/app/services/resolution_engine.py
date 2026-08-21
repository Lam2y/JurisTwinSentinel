from __future__ import annotations
import hashlib
import math
import re
import time
from datetime import timezone
from uuid import uuid4

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..core.config import get_settings
from ..db.models import Evidence, EvidenceOrigin, Interaction, KnowledgeGap, ResolutionPattern, SecurityShield, User
from .common import dumps, loads, iso, utcnow
from .ledger import append_entry
from .policy_ml import get_policy_ai
from .policy_reasoner import compare_policy_atoms, extract_policy_atoms

EMAIL_RE = re.compile(r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b", re.I)
PHONE_RE = re.compile(r"(?<!\d)(?:\+?\d[\d\s\-()]{7,}\d)(?!\d)")
LONG_NUMBER_RE = re.compile(r"(?<!\d)\d{10,}(?!\d)")
SPACE_RE = re.compile(r"\s+")
TOKEN_RE = re.compile(r"[a-z0-9]+")


def normalize_question(text: str) -> str:
    return " ".join(TOKEN_RE.findall((text or "").lower()))


def fingerprint(text: str) -> str:
    return hashlib.sha256(normalize_question(text).encode("utf-8")).hexdigest()


def content_fingerprint(*parts: str) -> str:
    return hashlib.sha256("|".join(normalize_question(x) for x in parts).encode("utf-8")).hexdigest()


def _shield_enabled(db: Session, key: str, default=True) -> bool:
    row = db.execute(select(SecurityShield).where(SecurityShield.key == key)).scalar_one_or_none()
    return bool(row.enabled) if row else default


def redact_sensitive(text: str, db: Session) -> str:
    value = SPACE_RE.sub(" ", (text or "").strip())
    if not _shield_enabled(db, "pii_masking", True):
        return value
    value = EMAIL_RE.sub("[EMAIL REDACTED]", value)
    value = LONG_NUMBER_RE.sub("[ACCOUNT REDACTED]", value)
    value = PHONE_RE.sub("[PHONE REDACTED]", value)
    return value


def contains_sensitive(text: str) -> bool:
    value = text or ""
    return bool(EMAIL_RE.search(value) or LONG_NUMBER_RE.search(value) or PHONE_RE.search(value))


def _tfidf_scores(query: str, texts: list[str]) -> list[float]:
    if not texts:
        return []
    corpus = [query] + texts
    try:
        word = TfidfVectorizer(lowercase=True, ngram_range=(1, 2), sublinear_tf=True, min_df=1).fit_transform(corpus)
        char = TfidfVectorizer(lowercase=True, analyzer="char_wb", ngram_range=(3, 5), sublinear_tf=True, min_df=1).fit_transform(corpus)
        scores = 0.68 * cosine_similarity(word[0:1], word[1:]).flatten() + 0.32 * cosine_similarity(char[0:1], char[1:]).flatten()
        return [float(x) for x in scores]
    except ValueError:
        return [0.0 for _ in texts]


def _evidence_text(e: Evidence) -> str:
    return " ".join([e.title or "", e.body or "", e.claim or "", e.source or "", e.authority or ""])


def evidence_rank(db: Session, question: str, rule_key: str | None = None) -> list[dict]:
    # Fail closed at the collection boundary: only evidence with an explicitly permitted origin
    # participates in retrieval. Private/direct chat is excluded before relevance ranking.
    stmt = select(Evidence).join(EvidenceOrigin, EvidenceOrigin.evidence_ref == Evidence.evidence_ref).where(
        EvidenceOrigin.source_scope.in_(["group_channel", "shared_repository", "formal_approval"]),
        EvidenceOrigin.private_message_excluded.is_(True),
    )
    if rule_key:
        stmt = stmt.where(Evidence.rule_key == rule_key)
    rows = db.execute(stmt.order_by(Evidence.authority_level.desc(), Evidence.created_at.desc())).scalars().all()
    origins = {o.evidence_ref: o for o in db.execute(select(EvidenceOrigin).where(EvidenceOrigin.evidence_ref.in_([e.evidence_ref for e in rows]))).scalars().all()} if rows else {}
    scores = _tfidf_scores(question, [_evidence_text(e) for e in rows])
    now = utcnow()
    ranked = []
    for e, relevance in zip(rows, scores):
        created = e.created_at
        if created and created.tzinfo is None:
            created = created.replace(tzinfo=timezone.utc)
        age = max(0.0, (now - created).total_seconds() / 86400) if created else 365.0
        recency = math.exp(-age / 180.0)
        authority = min(max(float(e.authority_level or 0) / 5.0, 0.0), 1.0)
        approval = 1.0 if e.approved else 0.0
        current = 0.0 if e.superseded or (e.status or "").lower() in {"outdated", "superseded"} else 1.0
        governance_score = 0.45 * relevance + 0.25 * authority + 0.15 * approval + 0.10 * recency + 0.05 * current
        ranked.append({
            "row": e,
            "relevance": round(relevance, 4),
            "authority_score": round(authority, 4),
            "recency_score": round(recency, 4),
            "governance_score": round(governance_score, 4),
            "origin": origins.get(e.evidence_ref),
        })
    ranked.sort(key=lambda x: (x["governance_score"], x["row"].authority_level, bool(x["row"].approved)), reverse=True)
    return ranked


def _fallback_rule_key(db: Session, question: str) -> tuple[str | None, float]:
    """Deterministic routing fallback if the learned router is unavailable or abstains.

    It scores the question against evidence grouped by policy domain. It is intentionally only a
    router: publication still requires evidence coverage, canonical approval, and contradiction gates.
    """
    rows = db.execute(
        select(Evidence).join(EvidenceOrigin, EvidenceOrigin.evidence_ref == Evidence.evidence_ref).where(
            EvidenceOrigin.source_scope.in_(["group_channel", "shared_repository", "formal_approval"]),
            EvidenceOrigin.private_message_excluded.is_(True),
        )
    ).scalars().all()
    grouped: dict[str, list[str]] = {}
    for e in rows:
        grouped.setdefault(e.rule_key, []).append(_evidence_text(e))
    keys = list(grouped)
    if not keys:
        return None, 0.0
    docs = [" ".join(grouped[k]) for k in keys]
    scores = _tfidf_scores(question, docs)
    idx = max(range(len(scores)), key=scores.__getitem__)
    return (keys[idx], float(scores[idx])) if scores[idx] >= 0.08 else (None, float(scores[idx]))


def _domain_prediction(db: Session, question: str) -> dict:
    try:
        model = get_policy_ai().predict(question)
        domain = model.get("domain", {})
        label = None if domain.get("abstain") else domain.get("label")
        if label == "general_policy_rule":
            label = None
        return {
            "rule_key": label,
            "confidence": float(domain.get("confidence") or 0.0),
            "model": model,
            "router": "learned",
        }
    except Exception as exc:
        rule_key, score = _fallback_rule_key(db, question)
        return {
            "rule_key": rule_key,
            "confidence": score,
            "model": {"domain": {"label": rule_key, "confidence": score, "probabilities": {}}, "stance": {}, "error": type(exc).__name__},
            "router": "deterministic_fallback",
        }


def _pattern_match(db: Session, question: str):
    patterns = db.execute(select(ResolutionPattern).where(ResolutionPattern.active.is_(True)).order_by(ResolutionPattern.id.desc())).scalars().all()
    if not patterns:
        return None
    tfidf = _tfidf_scores(question, [p.example_question for p in patterns])
    if not tfidf:
        return None

    route = _domain_prediction(db, question)
    predicted = route.get("rule_key")
    query_tokens = set(TOKEN_RE.findall((question or "").lower()))
    scores = []
    for pattern, tfidf_score in zip(patterns, tfidf):
        pattern_tokens = set(TOKEN_RE.findall((pattern.example_question or "").lower()))
        union = query_tokens | pattern_tokens
        jaccard = len(query_tokens & pattern_tokens) / len(union) if union else 0.0
        domain_bonus = 1.0 if predicted and pattern.rule_key and predicted == pattern.rule_key else 0.0
        hybrid = 0.65 * tfidf_score + 0.25 * jaccard + 0.10 * domain_bonus
        scores.append(float(min(1.0, hybrid)))
    index = max(range(len(scores)), key=scores.__getitem__)
    pattern = patterns[index]
    score = scores[index]
    threshold = float(pattern.match_threshold or get_settings().PATTERN_MATCH_THRESHOLD)
    return {"pattern": pattern, "score": score, "matched": score >= threshold}


def _safe_source(e: Evidence, relation="support"):
    return {
        "evidence_ref": e.evidence_ref,
        "source": e.source,
        "title": e.title,
        "authority": e.authority,
        "version": e.version,
        "relation": relation,
    }


def _record_gap(db: Session, user: User, question: str, domain: str | None, confidence: float, similarity: float, reason: str):
    stored = redact_sensitive(question, db)
    fp = fingerprint(stored)
    row = db.execute(select(KnowledgeGap).where(KnowledgeGap.fingerprint == fp)).scalar_one_or_none()
    now = utcnow()

    if not row:
        stmt = select(KnowledgeGap).where(KnowledgeGap.status == "open")
        if domain:
            stmt = stmt.where(KnowledgeGap.predicted_domain == domain)
        open_rows = db.execute(stmt.order_by(KnowledgeGap.last_seen_at.desc()).limit(30)).scalars().all()
        if open_rows:
            tfidf_scores = _tfidf_scores(stored, [g.question for g in open_rows])
            q_tokens = set(TOKEN_RE.findall(stored.lower()))
            best = None
            for gap, tfidf_score in zip(open_rows, tfidf_scores):
                g_tokens = set(TOKEN_RE.findall((gap.question or "").lower()))
                union = q_tokens | g_tokens
                jaccard = len(q_tokens & g_tokens) / len(union) if union else 0.0
                semantic = 0.72 * tfidf_score + 0.28 * jaccard
                if best is None or semantic > best[0]:
                    best = (semantic, gap)
            if best and best[0] >= 0.76:
                row = best[1]

    if row:
        row.occurrence_count += 1
        row.last_seen_at = now
        row.reason = reason if reason == "USER_FEEDBACK_ESCALATION" else row.reason
        if row.status == "resolved":
            row.status = "open"
            row.resolved_at = None
        append_entry(db, "KNOWLEDGE_GAP_RESEEN", user.email, {"gap_ref": row.gap_ref, "occurrences": row.occurrence_count, "reason": reason})
    else:
        row = KnowledgeGap(
            gap_ref=f"KG-{uuid4().hex[:10].upper()}",
            fingerprint=fp,
            question=stored,
            normalized_question=normalize_question(stored),
            predicted_domain=domain,
            domain_confidence=confidence,
            top_evidence_similarity=similarity,
            reason=reason,
            status="open",
            occurrence_count=1,
            first_seen_at=now,
            last_seen_at=now,
        )
        db.add(row)
        db.flush()
        append_entry(db, "KNOWLEDGE_GAP_CREATED", user.email, {"gap_ref": row.gap_ref, "predicted_domain": domain, "reason": reason})
    db.commit()
    return row


def record_feedback_gap(db: Session, user: User, question: str):
    route = _domain_prediction(db, question)
    ranked = evidence_rank(db, question, route["rule_key"]) if route["rule_key"] else []
    top_similarity = float(ranked[0]["relevance"]) if ranked else 0.0
    return _record_gap(db, user, question, route["rule_key"], route["confidence"], top_similarity, "USER_FEEDBACK_ESCALATION")


def _approved_conflict(eligible: list[dict]) -> dict | None:
    """Block publication if two current approved sources disagree, regardless of score.

    This prevents 'highest score wins' from silently hiding a split-brain policy state.
    """
    if len(eligible) < 2:
        return None
    ordered = sorted(eligible, key=lambda x: (x["row"].authority_level, x["governance_score"]), reverse=True)
    for i, left in enumerate(ordered):
        left_atoms = extract_policy_atoms(left["row"].body, left["row"].rule_key)
        for right in ordered[i + 1:]:
            comp = compare_policy_atoms(left_atoms, extract_policy_atoms(right["row"].body, right["row"].rule_key))
            if comp.get("collision"):
                return {"left": left["row"], "right": right["row"], "comparison": comp}
    return None


def _record_interaction(db: Session, user: User, question: str, status: str, handled_by: str, started: float, evidence_ref: str | None = None, resolution_ref: str | None = None) -> Interaction:
    interaction = Interaction(
        interaction_ref=f"IX-{uuid4().hex[:10].upper()}",
        user_id=user.id,
        user_role=user.role,
        question_masked=redact_sensitive(question, db),
        question_fingerprint=fingerprint(question),
        status=status,
        handled_by=handled_by,
        latency_ms=round((time.perf_counter() - started) * 1000, 3),
        evidence_ref=evidence_ref,
        resolution_ref=resolution_ref,
    )
    db.add(interaction)
    db.flush()
    return interaction


def _finalize_answer(db: Session, user: User, question: str, started: float, payload: dict, evidence_ref: str | None = None, resolution_ref: str | None = None) -> dict:
    interaction = _record_interaction(db, user, question, payload["status"], payload["handled_by"], started, evidence_ref=evidence_ref, resolution_ref=resolution_ref)
    db.commit()
    payload["interaction_ref"] = interaction.interaction_ref
    payload["latency_ms"] = interaction.latency_ms
    return payload


def answer_question(db: Session, user: User, question: str) -> dict:
    started = time.perf_counter()
    settings = get_settings()
    clean = redact_sensitive(question, db)

    pattern_hit = _pattern_match(db, clean)
    if pattern_hit and pattern_hit["matched"]:
        p = pattern_hit["pattern"]
        refs = loads(p.source_refs_json, [])
        evidence = db.execute(select(Evidence).where(Evidence.evidence_ref.in_(refs))).scalars().all() if refs else []
        by_ref = {e.evidence_ref: e for e in evidence}
        governed = [by_ref[r] for r in refs if r in by_ref and by_ref[r].approved and not by_ref[r].superseded and (by_ref[r].status or "").lower() == "active"]
        if refs and not governed:
            gap = _record_gap(db, user, clean, p.rule_key, 1.0, pattern_hit["score"], "PATTERN_SOURCE_INVALIDATED")
            return _finalize_answer(db, user, clean, started, {
                "status": "REVIEW_PENDING",
                "answer": "That previously approved answer depends on evidence that is no longer current. I’ve paused reuse and sent it for superadmin review.",
                "sources": [],
                "handled_by": "safe_fallback",
                "review_ref": gap.gap_ref if user.role == "superadmin" else None,
            })
        sources = [_safe_source(e) for e in governed]
        if not sources:
            sources = [{"evidence_ref": p.resolution_ref, "source": "Governance Decision Memory", "title": "Superadmin-published resolution", "authority": "Superadmin", "version": "active", "relation": "support"}]
        append_entry(db, "QUESTION_ANSWERED_BY_PATTERN", user.email, {"resolution_ref": p.resolution_ref, "similarity": round(pattern_hit["score"], 4)})
        return _finalize_answer(db, user, clean, started, {
            "status": "ANSWERED", "answer": p.answer, "sources": sources, "handled_by": "governed_pattern_memory"
        }, resolution_ref=p.resolution_ref)

    route = _domain_prediction(db, clean)
    rule_key = route["rule_key"]
    confidence = float(route["confidence"] or 0.0)
    ranked = evidence_rank(db, clean, rule_key=rule_key) if rule_key else []
    top_similarity = float(ranked[0]["relevance"]) if ranked else 0.0

    if not rule_key or (route["router"] == "learned" and confidence < settings.DOMAIN_CONFIDENCE_THRESHOLD):
        gap = _record_gap(db, user, clean, rule_key, confidence, top_similarity, "LOW_DOMAIN_CONFIDENCE")
        return _finalize_answer(db, user, clean, started, {
            "status": "REVIEW_PENDING", "answer": "I don't have a governed answer for that yet. I’ve sent this question to the superadmin for review.", "sources": [], "handled_by": "safe_fallback", "review_ref": gap.gap_ref if user.role == "superadmin" else None
        })

    if not ranked or top_similarity < settings.EVIDENCE_COVERAGE_THRESHOLD:
        gap = _record_gap(db, user, clean, rule_key, confidence, top_similarity, "INSUFFICIENT_EVIDENCE_COVERAGE")
        return _finalize_answer(db, user, clean, started, {
            "status": "REVIEW_PENDING", "answer": "I don't have enough governed evidence to answer that safely yet. I’ve sent this question to the superadmin for review.", "sources": [], "handled_by": "safe_fallback", "review_ref": gap.gap_ref if user.role == "superadmin" else None
        })

    eligible = [x for x in ranked if x["row"].approved and not x["row"].superseded and (x["row"].status or "").lower() == "active"]
    if not eligible:
        gap = _record_gap(db, user, clean, rule_key, confidence, top_similarity, "NO_APPROVED_CANONICAL_SOURCE")
        return _finalize_answer(db, user, clean, started, {
            "status": "REVIEW_PENDING", "answer": "The available evidence is not strong enough to publish as a governed answer. I’ve sent it for superadmin review.", "sources": [], "handled_by": "safe_fallback", "review_ref": gap.gap_ref if user.role == "superadmin" else None
        })

    split_brain = _approved_conflict(eligible)
    if split_brain:
        gap = _record_gap(db, user, clean, rule_key, confidence, top_similarity, "CANONICAL_CONFLICT")
        append_entry(db, "CANONICAL_CONFLICT_BLOCKED", user.email, {
            "gap_ref": gap.gap_ref,
            "left": split_brain["left"].evidence_ref,
            "right": split_brain["right"].evidence_ref,
        })
        return _finalize_answer(db, user, clean, started, {
            "status": "REVIEW_PENDING", "answer": "Two current approved sources disagree, so I won’t choose between them silently. I’ve quarantined the decision for superadmin resolution.", "sources": [], "handled_by": "canonical_conflict_gate", "review_ref": gap.gap_ref if user.role == "superadmin" else None
        })

    canonical = max(eligible, key=lambda x: (x["row"].authority_level, x["governance_score"]))
    sources = [_safe_source(canonical["row"])]
    append_entry(db, "QUESTION_ANSWERED", user.email, {"rule_key": rule_key, "evidence_ref": canonical["row"].evidence_ref, "domain_confidence": round(confidence, 4), "coverage": round(top_similarity, 4), "router": route["router"]})
    return _finalize_answer(db, user, clean, started, {
        "status": "ANSWERED", "answer": canonical["row"].body, "sources": sources, "handled_by": "governed_evidence"
    }, evidence_ref=canonical["row"].evidence_ref)


def _disagreement_reason(canonical: Evidence, other: Evidence, compare: dict) -> list[str]:
    reasons = []
    for collision in compare.get("collisions", []):
        if collision.get("explanation"):
            reasons.append(collision["explanation"])
    if other.superseded or (other.status or "").lower() in {"outdated", "superseded"}:
        reasons.append("This source is outdated or superseded.")
    if other.authority_level < canonical.authority_level:
        reasons.append(f"It has lower authority ({other.authority_level}) than {canonical.authority} ({canonical.authority_level}).")
    if other.version and canonical.version and other.version != canonical.version:
        reasons.append(f"Version drift: {other.version} differs from the current governed version {canonical.version}.")
    if other.claim != canonical.claim and not reasons:
        reasons.append("The source asserts a different policy claim from the current governed source.")
    return list(dict.fromkeys(reasons))[:4]


def analyse_question(db: Session, question: str, predicted_domain: str | None = None) -> dict:
    clean = redact_sensitive(question, db)
    route = _domain_prediction(db, clean)
    model = route["model"]
    domain = model.get("domain", {})
    rule_key = predicted_domain or route["rule_key"]
    ranked = evidence_rank(db, clean, rule_key=rule_key) if rule_key else evidence_rank(db, clean)
    candidates = ranked[:10]

    current_approved = [x for x in candidates if x["row"].approved and not x["row"].superseded and (x["row"].status or "").lower() == "active"]
    canonical = max(current_approved, key=lambda x: (x["row"].authority_level, x["governance_score"]), default=None)
    split_brain = _approved_conflict(current_approved)
    support, conflict, context = [], [], []

    if canonical:
        c_atoms = extract_policy_atoms(canonical["row"].body, canonical["row"].rule_key)
        for item in candidates:
            e = item["row"]
            if e.evidence_ref == canonical["row"].evidence_ref:
                relation = "support"
                reasons = ["Current approved highest-authority source."]
            else:
                comp = compare_policy_atoms(c_atoms, extract_policy_atoms(e.body, e.rule_key))
                if comp.get("collision") or e.superseded or (e.status or "").lower() in {"outdated", "superseded"}:
                    relation = "conflict"
                    reasons = _disagreement_reason(canonical["row"], e, comp)
                elif e.claim == canonical["row"].claim and e.approved:
                    relation = "support"
                    reasons = ["The claim aligns with the current governed source."]
                else:
                    relation = "context"
                    reasons = ["Relevant evidence, but it is not allowed to define policy by itself."]
            payload = {
                "evidence_ref": e.evidence_ref,
                "source": e.source,
                "title": e.title,
                "body": e.body,
                "claim": e.claim,
                "authority": e.authority,
                "authority_level": e.authority_level,
                "version": e.version,
                "status": e.status,
                "approved": e.approved,
                "superseded": e.superseded,
                "relevance": item["relevance"],
                "governance_score": item["governance_score"],
                "source_scope": item["origin"].source_scope if item.get("origin") else "unknown",
                "collection_reason": item["origin"].collection_reason if item.get("origin") else "Origin metadata unavailable",
                "collection_relevance": round(float(item["origin"].relevance_score or 0), 4) if item.get("origin") else 0.0,
                "private_message_excluded": bool(item["origin"].private_message_excluded) if item.get("origin") else True,
                "reasons": reasons,
            }
            {"support": support, "conflict": conflict, "context": context}[relation].append(payload)
    else:
        for item in candidates:
            e = item["row"]
            context.append({
                "evidence_ref": e.evidence_ref, "source": e.source, "title": e.title, "body": e.body,
                "claim": e.claim, "authority": e.authority, "authority_level": e.authority_level,
                "version": e.version, "status": e.status, "approved": e.approved, "superseded": e.superseded,
                "relevance": item["relevance"], "governance_score": item["governance_score"],
                "source_scope": item["origin"].source_scope if item.get("origin") else "unknown",
                "collection_reason": item["origin"].collection_reason if item.get("origin") else "Origin metadata unavailable",
                "collection_relevance": round(float(item["origin"].relevance_score or 0), 4) if item.get("origin") else 0.0,
                "private_message_excluded": bool(item["origin"].private_message_excluded) if item.get("origin") else True,
                "reasons": ["No canonical source is strong enough to define the answer; this is context only."],
            })

    stance = model.get("stance", {})
    top = candidates[0] if candidates else None
    if split_brain:
        recommendation = ""
    elif canonical:
        if canonical["relevance"] >= get_settings().EVIDENCE_COVERAGE_THRESHOLD:
            recommendation = canonical["row"].body
        else:
            recommendation = (
                f"The current governed policy confirms only this: {canonical['row'].body} "
                "The new evidence type in this question is not explicitly covered, so do not treat it as approved until a superadmin publishes a decision."
            )
    else:
        recommendation = ""

    confidence = 0.0
    if canonical and not split_brain:
        margin = canonical["governance_score"] - (candidates[1]["governance_score"] if len(candidates) > 1 else 0.0)
        confidence = min(0.99, 0.55 + 0.22 * float(domain.get("confidence") or 0) + 0.15 * canonical["relevance"] + 0.08 * max(margin, 0))

    disagree = [r for x in conflict for r in x.get("reasons", [])]
    if split_brain:
        disagree.insert(0, "Two current approved sources contain a policy collision. JurisTwin blocks automatic publication until a human resolves the split-brain state.")

    return {
        "question": clean,
        "predicted_domain": rule_key,
        "recommendation": recommendation,
        "recommendation_confidence": round(confidence, 4),
        "supporting": support,
        "conflicting": conflict,
        "context": context,
        "canonical_conflict": bool(split_brain),
        "why_sources_disagree": list(dict.fromkeys(disagree))[:10],
        "technical_trace": {
            "domain_model": "TF-IDF word + character n-grams → Logistic Regression",
            "router_mode": route["router"],
            "domain_label": domain.get("label"),
            "domain_confidence": domain.get("confidence"),
            "domain_probabilities": domain.get("probabilities", {}),
            "stance_label": stance.get("label"),
            "stance_confidence": stance.get("confidence"),
            "retrieval": "TF-IDF word/character cosine similarity",
            "governance_score_formula": "45% relevance + 25% authority + 15% approval + 10% recency + 5% active status",
            "symbolic_verifier": "Policy Atom Reasoner (modality / threshold / deadline collisions)",
            "canonical_split_brain_gate": "Any collision between current approved sources blocks automatic publication",
            "top_evidence_similarity": top["relevance"] if top else 0.0,
            "publication_rule": "Only a human superadmin can turn an unresolved gap into reusable decision memory.",
            "privacy_collection_boundary": "Relevant approved group channels + formal/shared sources only; PM/DM and unrelated group chatter are excluded before retrieval.",
        },
    }


def gap_detail(db: Session, gap: KnowledgeGap) -> dict:
    analysis = analyse_question(db, gap.question, gap.predicted_domain)
    return {
        "gap_ref": gap.gap_ref,
        "question": gap.question,
        "predicted_domain": gap.predicted_domain,
        "domain_confidence": round(gap.domain_confidence or 0, 4),
        "top_evidence_similarity": round(gap.top_evidence_similarity or 0, 4),
        "reason": gap.reason,
        "status": gap.status,
        "occurrence_count": gap.occurrence_count,
        "first_seen_at": iso(gap.first_seen_at),
        "last_seen_at": iso(gap.last_seen_at),
        "resolution_ref": gap.resolution_ref,
        "analysis": analysis,
    }


def publish_gap(db: Session, gap: KnowledgeGap, admin: User, answer: str, source_refs: list[str], uncertainty_note: str | None, match_threshold: float):
    if gap.status == "resolved" and gap.resolution_ref:
        existing = db.execute(select(ResolutionPattern).where(ResolutionPattern.resolution_ref == gap.resolution_ref)).scalar_one_or_none()
        return existing

    refs = list(dict.fromkeys(source_refs))
    analysis = analyse_question(db, gap.question, gap.predicted_domain)
    safe_refs = {x["evidence_ref"] for x in analysis.get("supporting", []) if x.get("approved") and not x.get("superseded") and (x.get("status") or "").lower() == "active"}
    forbidden = [r for r in refs if r not in safe_refs]
    if forbidden:
        raise ValueError("Only current approved supporting sources may be attached to a published resolution. Remove: " + ", ".join(forbidden))
    selected_evidence: list[Evidence] = []
    if refs:
        selected_evidence = db.execute(select(Evidence).where(Evidence.evidence_ref.in_(refs))).scalars().all()
        valid = {e.evidence_ref for e in selected_evidence}
        missing = [r for r in refs if r not in valid]
        if missing:
            raise ValueError(f"Unknown evidence reference(s): {', '.join(missing)}")

        # Final-response lineage gate: a source can be generally relevant to the knowledge gap but
        # still fail to support the exact wording the human is about to publish. We therefore
        # compare the final answer itself with every attached source and reject contradictory or
        # extremely weak attribution. The superadmin can still publish source-less with an explicit
        # uncertainty note when the evidence does not directly support the decision.
        final_atoms = extract_policy_atoms(answer, gap.predicted_domain or "general_policy_rule")
        for evidence in selected_evidence:
            source_atoms = extract_policy_atoms(evidence.body, evidence.rule_key)
            collision = compare_policy_atoms(source_atoms, final_atoms)
            if collision.get("collision"):
                raise ValueError(
                    f"Attached source {evidence.evidence_ref} conflicts with the final response wording. "
                    "Remove the source or revise the response."
                )
            support_similarity = (_tfidf_scores(answer, [_evidence_text(evidence)]) or [0.0])[0]
            if support_similarity < 0.06:
                raise ValueError(
                    f"Attached source {evidence.evidence_ref} is too weakly related to the final response to be cited as lineage. "
                    "Remove it and record an uncertainty note instead."
                )
    if not refs and not (uncertainty_note or "").strip():
        raise ValueError("When evidence is insufficient, record an uncertainty / exception note before publishing a manual decision.")

    resolution = ResolutionPattern(
        resolution_ref=f"RS-{uuid4().hex[:10].upper()}",
        example_question=gap.question,
        normalized_example=gap.normalized_question,
        answer=answer.strip(),
        rule_key=gap.predicted_domain,
        source_refs_json=dumps(refs),
        uncertainty_note=(uncertainty_note or "").strip() or None,
        match_threshold=match_threshold,
        created_by=admin.email,
        active=True,
    )
    db.add(resolution)
    db.flush()
    gap.status = "resolved"
    gap.resolution_ref = resolution.resolution_ref
    gap.resolved_at = utcnow()
    append_entry(db, "KNOWLEDGE_GAP_PUBLISHED", admin.email, {
        "gap_ref": gap.gap_ref,
        "resolution_ref": resolution.resolution_ref,
        "source_refs": refs,
        "has_uncertainty_note": bool(resolution.uncertainty_note),
        "match_threshold": match_threshold,
    })
    db.commit()
    db.refresh(resolution)
    return resolution

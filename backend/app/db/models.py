from datetime import datetime, timezone
from sqlalchemy import Boolean, Column, DateTime, Float, Integer, String, Text
from .database import Base


def now_utc():
    return datetime.now(timezone.utc)


class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    email = Column(String(180), unique=True, index=True, nullable=False)
    name = Column(String(120), nullable=False)
    role = Column(String(40), nullable=False, index=True)
    password_hash = Column(String(240), nullable=False)
    active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), default=now_utc, nullable=False)


class Evidence(Base):
    __tablename__ = "evidence"
    id = Column(Integer, primary_key=True)
    evidence_ref = Column(String(64), unique=True, index=True, nullable=False)
    source = Column(String(100), nullable=False, index=True)
    title = Column(String(220), nullable=False)
    body = Column(Text, nullable=False)
    rule_key = Column(String(100), nullable=False, index=True)
    claim = Column(String(180), nullable=False)
    authority = Column(String(120), nullable=False)
    authority_level = Column(Integer, default=1, nullable=False)
    version = Column(String(40), nullable=True)
    status = Column(String(40), default="active", nullable=False, index=True)
    sensitivity = Column(String(40), default="internal", nullable=False)
    approved = Column(Boolean, default=False, nullable=False)
    superseded = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime(timezone=True), default=now_utc, nullable=False)


class EvidenceOrigin(Base):
    __tablename__ = "evidence_origins"
    id = Column(Integer, primary_key=True)
    evidence_ref = Column(String(64), unique=True, index=True, nullable=False)
    connector = Column(String(80), nullable=False)
    source_scope = Column(String(40), nullable=False, index=True)
    collection_reason = Column(String(240), nullable=False)
    private_message_excluded = Column(Boolean, default=True, nullable=False)
    relevance_score = Column(Float, default=1.0, nullable=False)
    created_at = Column(DateTime(timezone=True), default=now_utc, nullable=False)


class KnowledgeGap(Base):
    __tablename__ = "knowledge_gaps"
    id = Column(Integer, primary_key=True)
    gap_ref = Column(String(48), unique=True, index=True, nullable=False)
    fingerprint = Column(String(64), unique=True, index=True, nullable=False)
    question = Column(Text, nullable=False)
    normalized_question = Column(Text, nullable=False)
    predicted_domain = Column(String(100), nullable=True, index=True)
    domain_confidence = Column(Float, default=0.0, nullable=False)
    top_evidence_similarity = Column(Float, default=0.0, nullable=False)
    reason = Column(String(240), nullable=False)
    status = Column(String(40), default="open", nullable=False, index=True)
    occurrence_count = Column(Integer, default=1, nullable=False)
    first_seen_at = Column(DateTime(timezone=True), default=now_utc, nullable=False)
    last_seen_at = Column(DateTime(timezone=True), default=now_utc, nullable=False)
    resolved_at = Column(DateTime(timezone=True), nullable=True)
    resolution_ref = Column(String(48), nullable=True, index=True)


class ResolutionPattern(Base):
    __tablename__ = "resolution_patterns"
    id = Column(Integer, primary_key=True)
    resolution_ref = Column(String(48), unique=True, index=True, nullable=False)
    example_question = Column(Text, nullable=False)
    normalized_example = Column(Text, nullable=False)
    answer = Column(Text, nullable=False)
    rule_key = Column(String(100), nullable=True, index=True)
    source_refs_json = Column(Text, default="[]", nullable=False)
    uncertainty_note = Column(Text, nullable=True)
    match_threshold = Column(Float, default=0.62, nullable=False)
    created_by = Column(String(180), nullable=False)
    active = Column(Boolean, default=True, nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), default=now_utc, nullable=False)


class RolePolicy(Base):
    __tablename__ = "role_policies"
    id = Column(Integer, primary_key=True)
    role = Column(String(40), unique=True, index=True, nullable=False)
    display_name = Column(String(80), nullable=False)
    description = Column(Text, nullable=False)
    enabled = Column(Boolean, default=True, nullable=False)
    can_manage_governance = Column(Boolean, default=False, nullable=False)
    can_view_sensitive_evidence = Column(Boolean, default=False, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=now_utc, nullable=False)


class SecurityShield(Base):
    __tablename__ = "security_shields"
    id = Column(Integer, primary_key=True)
    key = Column(String(80), unique=True, index=True, nullable=False)
    name = Column(String(120), nullable=False)
    description = Column(Text, nullable=False)
    enabled = Column(Boolean, default=True, nullable=False)
    updated_by = Column(String(180), nullable=True)
    updated_at = Column(DateTime(timezone=True), default=now_utc, nullable=False)


class LedgerEntry(Base):
    __tablename__ = "ledger_entries"
    id = Column(Integer, primary_key=True)
    txid = Column(String(80), unique=True, index=True, nullable=False)
    action = Column(String(120), nullable=False, index=True)
    actor = Column(String(180), nullable=False)
    payload_json = Column(Text, nullable=False)
    previous_hash = Column(String(96), nullable=True)
    entry_hash = Column(String(96), unique=True, nullable=False)
    created_at = Column(DateTime(timezone=True), default=now_utc, nullable=False)


class Interaction(Base):
    """Privacy-minimised telemetry used for live adoption and quality validation.

    The stored question is already PII-masked. Raw prompts are never copied into this table.
    """
    __tablename__ = "interactions"
    id = Column(Integer, primary_key=True)
    interaction_ref = Column(String(48), unique=True, index=True, nullable=False)
    user_id = Column(Integer, nullable=False, index=True)
    user_role = Column(String(40), nullable=False, index=True)
    question_masked = Column(Text, nullable=False)
    question_fingerprint = Column(String(64), nullable=False, index=True)
    status = Column(String(40), nullable=False, index=True)
    handled_by = Column(String(80), nullable=False, index=True)
    latency_ms = Column(Float, default=0.0, nullable=False)
    evidence_ref = Column(String(64), nullable=True, index=True)
    resolution_ref = Column(String(48), nullable=True, index=True)
    created_at = Column(DateTime(timezone=True), default=now_utc, nullable=False)


class AnswerFeedback(Base):
    __tablename__ = "answer_feedback"
    id = Column(Integer, primary_key=True)
    feedback_ref = Column(String(48), unique=True, index=True, nullable=False)
    interaction_ref = Column(String(48), index=True, nullable=False)
    helpful = Column(Boolean, nullable=False, index=True)
    comment_masked = Column(Text, nullable=True)
    escalated = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime(timezone=True), default=now_utc, nullable=False)


class ResilienceRun(Base):
    __tablename__ = "resilience_runs"
    id = Column(Integer, primary_key=True)
    run_ref = Column(String(48), unique=True, index=True, nullable=False)
    score = Column(Integer, nullable=False)
    status = Column(String(40), nullable=False)
    checks_json = Column(Text, nullable=False)
    created_by = Column(String(180), nullable=False)
    created_at = Column(DateTime(timezone=True), default=now_utc, nullable=False)

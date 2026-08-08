from datetime import datetime, timezone
from sqlalchemy import Boolean, Column, DateTime, Float, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import relationship
from .database import Base


def now_utc():
    return datetime.now(timezone.utc)

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    email = Column(String(160), unique=True, index=True, nullable=False)
    name = Column(String(120), nullable=False)
    role = Column(String(40), nullable=False, index=True)
    password_hash = Column(String(220), nullable=False)
    active = Column(Boolean, default=True, nullable=False)
    assigned_case_refs = Column(Text, default="[]", nullable=False)

class CustomerCase(Base):
    __tablename__ = "cases"
    id = Column(Integer, primary_key=True)
    case_ref = Column(String(40), unique=True, index=True, nullable=False)
    customer_name = Column(String(120), nullable=False)
    customer_type = Column(String(80), nullable=False)
    application_type = Column(String(140), nullable=False)
    owner_email = Column(String(160), index=True)
    status = Column(String(60), default="active", index=True)
    risk_status = Column(String(30), default="Low", index=True)
    sentiment = Column(String(40), default="Neutral")
    pending_days = Column(Float, default=0.0)
    conflict_ref = Column(String(40), index=True, nullable=True)
    current_blocker = Column(String(180), nullable=True)
    protected = Column(Boolean, default=False)
    metadata_json = Column(Text, default="{}")
    created_at = Column(DateTime(timezone=True), default=now_utc)

class CaseEvent(Base):
    __tablename__ = "case_events"
    id = Column(Integer, primary_key=True)
    case_id = Column(Integer, ForeignKey("cases.id", ondelete="CASCADE"), index=True, nullable=False)
    source = Column(String(80), nullable=False)
    title = Column(String(160), nullable=False)
    description = Column(Text, nullable=False)
    event_time = Column(DateTime(timezone=True), nullable=False)
    severity = Column(String(30), default="info")
    case = relationship("CustomerCase")

class Evidence(Base):
    __tablename__ = "evidence"
    id = Column(Integer, primary_key=True)
    evidence_ref = Column(String(60), unique=True, index=True, nullable=False)
    source = Column(String(80), index=True, nullable=False)
    title = Column(String(180), nullable=False)
    body = Column(Text, nullable=False)
    rule_key = Column(String(80), index=True, nullable=True)
    claim = Column(Text, nullable=True)
    authority = Column(String(120), nullable=True)
    authority_level = Column(Integer, default=1)
    version = Column(String(40), nullable=True)
    status = Column(String(40), default="active", index=True)
    sensitivity = Column(String(40), default="internal", index=True)
    case_ref = Column(String(40), nullable=True, index=True)
    approved = Column(Boolean, default=False)
    superseded = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), default=now_utc)
    metadata_json = Column(Text, default="{}")

class Conflict(Base):
    __tablename__ = "conflicts"
    id = Column(Integer, primary_key=True)
    conflict_ref = Column(String(40), unique=True, index=True, nullable=False)
    name = Column(String(180), nullable=False)
    rule_key = Column(String(80), index=True, nullable=False)
    severity = Column(String(30), nullable=False)
    status = Column(String(40), default="unresolved", index=True)
    root_cause = Column(Text, nullable=False)
    recommendation = Column(Text, nullable=False)
    confidence = Column(Float, default=0.0)
    affected_customers = Column(Integer, default=0)
    systems_affected = Column(Integer, default=0)
    approved_evidence_ref = Column(String(60), nullable=True)
    created_at = Column(DateTime(timezone=True), default=now_utc)
    resolved_at = Column(DateTime(timezone=True), nullable=True)

class ConflictEvidence(Base):
    __tablename__ = "conflict_evidence"
    id = Column(Integer, primary_key=True)
    conflict_id = Column(Integer, ForeignKey("conflicts.id", ondelete="CASCADE"), index=True, nullable=False)
    evidence_id = Column(Integer, ForeignKey("evidence.id", ondelete="CASCADE"), index=True, nullable=False)
    relation = Column(String(40), nullable=False)
    __table_args__ = (UniqueConstraint("conflict_id", "evidence_id", name="uq_conflict_evidence"),)

class Simulation(Base):
    __tablename__ = "simulations"
    id = Column(Integer, primary_key=True)
    sim_ref = Column(String(40), unique=True, index=True, nullable=False)
    conflict_ref = Column(String(40), index=True, nullable=False)
    weights_json = Column(Text, default="{}")
    options_json = Column(Text, nullable=False)
    recommended_option = Column(String(10), nullable=False)
    confidence = Column(Float, nullable=False)
    created_by = Column(String(160), nullable=False)
    created_at = Column(DateTime(timezone=True), default=now_utc)

class Approval(Base):
    __tablename__ = "approvals"
    id = Column(Integer, primary_key=True)
    approval_ref = Column(String(40), unique=True, index=True, nullable=False)
    sim_ref = Column(String(40), index=True, nullable=False)
    conflict_ref = Column(String(40), index=True, nullable=False)
    selected_option = Column(String(10), nullable=False)
    status = Column(String(40), default="pending", index=True)
    requested_by = Column(String(160), nullable=False)
    approved_by = Column(String(160), nullable=True)
    comments = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), default=now_utc)
    decided_at = Column(DateTime(timezone=True), nullable=True)

class DecisionContract(Base):
    __tablename__ = "decision_contracts"
    id = Column(Integer, primary_key=True)
    decision_ref = Column(String(40), unique=True, index=True, nullable=False)
    rule_key = Column(String(80), index=True, nullable=False)
    approved_rule = Column(Text, nullable=False)
    approved_by = Column(String(220), nullable=False)
    effective_at = Column(DateTime(timezone=True), nullable=False)
    supersedes = Column(String(160), nullable=True)
    affected_json = Column(Text, nullable=False)
    status = Column(String(40), default="active", index=True)
    version = Column(String(40), nullable=False)
    source_approval_ref = Column(String(40), nullable=False)
    created_at = Column(DateTime(timezone=True), default=now_utc)

class LedgerEntry(Base):
    __tablename__ = "ledger_entries"
    id = Column(Integer, primary_key=True)
    txid = Column(String(80), unique=True, index=True, nullable=False)
    decision_ref = Column(String(40), index=True, nullable=True)
    action = Column(String(120), nullable=False)
    actor = Column(String(160), nullable=False)
    payload_json = Column(Text, nullable=False)
    previous_hash = Column(String(64), nullable=True)
    entry_hash = Column(String(64), unique=True, nullable=False)
    created_at = Column(DateTime(timezone=True), default=now_utc)

class SecurityAlert(Base):
    __tablename__ = "security_alerts"
    id = Column(Integer, primary_key=True)
    alert_ref = Column(String(40), unique=True, index=True, nullable=False)
    severity = Column(String(30), nullable=False)
    status = Column(String(40), default="open", index=True)
    title = Column(String(180), nullable=False)
    user_ref = Column(String(80), nullable=False)
    document = Column(String(180), nullable=False)
    action = Column(String(240), nullable=False)
    conflict_decision_ref = Column(String(40), nullable=True)
    reasons_json = Column(Text, nullable=False)
    timeline_json = Column(Text, nullable=False)
    occurred_at = Column(DateTime(timezone=True), nullable=False)
    restored_at = Column(DateTime(timezone=True), nullable=True)

class Integration(Base):
    __tablename__ = "integrations"
    id = Column(Integer, primary_key=True)
    key = Column(String(80), unique=True, index=True, nullable=False)
    name = Column(String(120), nullable=False)
    kind = Column(String(80), nullable=False)
    status = Column(String(40), default="connected")
    object_count = Column(Integer, default=0)
    last_sync_at = Column(DateTime(timezone=True), nullable=True)
    shield_status = Column(String(80), default="ACTIVE SHIELDING ON")
    details_json = Column(Text, default="{}")

class RolePolicy(Base):
    __tablename__ = "role_policies"
    id = Column(Integer, primary_key=True)
    role = Column(String(40), unique=True, index=True, nullable=False)
    display_name = Column(String(80), nullable=False)
    description = Column(Text, nullable=False)
    enabled = Column(Boolean, default=True, nullable=False)
    max_sensitivity = Column(Integer, default=1, nullable=False)
    can_override = Column(Boolean, default=False, nullable=False)
    can_modify_twin = Column(Boolean, default=False, nullable=False)
    can_export_ledger = Column(Boolean, default=False, nullable=False)
    can_review_bodyguard = Column(Boolean, default=False, nullable=False)
    updated_by = Column(String(160), nullable=True)
    updated_at = Column(DateTime(timezone=True), default=now_utc, onupdate=now_utc)

class SecurityShield(Base):
    __tablename__ = "security_shields"
    id = Column(Integer, primary_key=True)
    key = Column(String(80), unique=True, index=True, nullable=False)
    name = Column(String(120), nullable=False)
    description = Column(Text, nullable=False)
    enabled = Column(Boolean, default=True, nullable=False)
    value_json = Column(Text, default="{}", nullable=False)
    updated_by = Column(String(160), nullable=True)
    updated_at = Column(DateTime(timezone=True), default=now_utc, onupdate=now_utc)

class DecisionVersion(Base):
    __tablename__ = "decision_versions"
    id = Column(Integer, primary_key=True)
    decision_ref = Column(String(40), index=True, nullable=False)
    version = Column(String(40), nullable=False)
    rule_text = Column(Text, nullable=False)
    change_type = Column(String(80), nullable=False)
    actor = Column(String(160), nullable=False)
    status = Column(String(40), default="historical", index=True)
    metadata_json = Column(Text, default="{}", nullable=False)
    created_at = Column(DateTime(timezone=True), default=now_utc)
    __table_args__ = (UniqueConstraint("decision_ref", "version", name="uq_decision_version"),)

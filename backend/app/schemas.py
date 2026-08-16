from typing import Any
from pydantic import BaseModel, Field

class LoginRequest(BaseModel):
    email: str
    password: str

class MemorySearchRequest(BaseModel):
    query: str = ""
    limit: int = Field(default=10, ge=1, le=50)
    filters: dict[str, Any] = {}
    preview_role: str | None = None

class MemoryAnswerRequest(BaseModel):
    question: str = Field(min_length=5, max_length=500)
    preview_role: str | None = None

class MemoryIngestRequest(BaseModel):
    source: str
    title: str
    body: str
    rule_key: str | None = None
    claim: str | None = None
    authority: str | None = None
    authority_level: int = 1
    version: str | None = None
    sensitivity: str = "internal"
    case_ref: str | None = None
    approved: bool = False
    metadata: dict[str, Any] = {}

class SimulationRequest(BaseModel):
    weights: dict[str, float] | None = None

class SubmitApprovalRequest(BaseModel):
    selected_option: str | None = None
    comments: str | None = None

class ApprovalDecisionRequest(BaseModel):
    comments: str | None = None

class SearchRequest(BaseModel):
    query: str
    limit: int = Field(default=10, ge=1, le=50)

class RolePolicyUpdate(BaseModel):
    enabled: bool | None = None
    max_sensitivity: int | None = Field(default=None, ge=0, le=3)
    can_override: bool | None = None
    can_modify_twin: bool | None = None
    can_export_ledger: bool | None = None
    can_review_bodyguard: bool | None = None

class ShieldUpdate(BaseModel):
    enabled: bool | None = None
    value: dict[str, Any] | None = None

class IntegrationConfigRequest(BaseModel):
    config: dict[str, Any] = {}

class BodyguardActionRequest(BaseModel):
    comments: str | None = None

class LiveChallengeRequest(BaseModel):
    source: str = Field(default="Judge Live Input", min_length=2, max_length=80)
    title: str = Field(default="Unseen policy evidence", min_length=3, max_length=180)
    body: str = Field(min_length=8, max_length=5000)
    rule_key: str | None = Field(default=None, max_length=80)
    authority: str = Field(default="Live external evidence", min_length=2, max_length=120)
    authority_level: int = Field(default=2, ge=1, le=5)
    sensitivity: str = Field(default="internal", pattern="^(public|internal|confidential|restricted)$")


class EvidenceDropRequest(BaseModel):
    filename: str = Field(min_length=3, max_length=180)
    content: str = Field(min_length=8, max_length=150000)
    mime_type: str = Field(default="text/plain", max_length=120)
    authority: str = Field(default="Judge-supplied file", min_length=2, max_length=120)
    authority_level: int = Field(default=2, ge=1, le=5)
    sensitivity: str = Field(default="internal", pattern="^(public|internal|confidential|restricted)$")


class SignedWebhookRequest(BaseModel):
    event_id: str = Field(min_length=4, max_length=100)
    source: str = Field(min_length=2, max_length=80)
    title: str = Field(min_length=3, max_length=180)
    body: str = Field(min_length=8, max_length=5000)
    authority: str = Field(default="External connector", min_length=2, max_length=120)
    authority_level: int = Field(default=2, ge=1, le=5)
    sensitivity: str = Field(default="internal", pattern="^(public|internal|confidential|restricted)$")


class ProofVerifyRequest(BaseModel):
    # ``bundle_digest`` is the field emitted by the proof-pack response. ``digest`` remains accepted
    # for backward compatibility with the offline verifier and earlier clients.
    digest: str | None = Field(default=None, min_length=64, max_length=64, pattern="^[0-9a-fA-F]{64}$")
    bundle_digest: str | None = Field(default=None, min_length=64, max_length=64, pattern="^[0-9a-fA-F]{64}$")
    signature: str = Field(min_length=64, max_length=64, pattern="^[0-9a-fA-F]{64}$")

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

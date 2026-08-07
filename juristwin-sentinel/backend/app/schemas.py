from typing import Any
from pydantic import BaseModel, Field

class LoginRequest(BaseModel):
    email: str
    password: str

class MemorySearchRequest(BaseModel):
    query: str = ""
    limit: int = Field(default=10, ge=1, le=50)

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

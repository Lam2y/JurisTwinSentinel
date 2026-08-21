from typing import Literal
from pydantic import BaseModel, Field


class LoginRequest(BaseModel):
    email: str = Field(min_length=3, max_length=180)
    password: str = Field(min_length=6, max_length=180)


class AskRequest(BaseModel):
    question: str = Field(min_length=3, max_length=1200)


class FeedbackRequest(BaseModel):
    interaction_ref: str = Field(min_length=4, max_length=48)
    helpful: bool
    comment: str | None = Field(default=None, max_length=1000)


class PublishResolutionRequest(BaseModel):
    answer: str = Field(min_length=3, max_length=5000)
    source_refs: list[str] = Field(default_factory=list, max_length=20)
    uncertainty_note: str | None = Field(default=None, max_length=2000)
    match_threshold: float = Field(default=0.62, ge=0.45, le=0.95)


class EvidenceIngestRequest(BaseModel):
    source: str = Field(min_length=2, max_length=100)
    title: str = Field(min_length=3, max_length=220)
    body: str = Field(min_length=5, max_length=8000)
    rule_key: Literal["income_document_rule", "loan_restructure_rule", "notification_deadline"] | None = None
    claim: str | None = Field(default=None, max_length=180)
    authority: str = Field(default="Submitted evidence", min_length=2, max_length=120)
    authority_level: int = Field(default=2, ge=1, le=5)
    version: str | None = Field(default=None, max_length=40)
    sensitivity: Literal["public", "internal", "confidential"] = "internal"
    source_scope: Literal["group_channel", "shared_repository", "formal_approval", "private_message"] = "shared_repository"


class PatternStateRequest(BaseModel):
    active: bool
    reason: str | None = Field(default=None, max_length=500)


class ShieldUpdateRequest(BaseModel):
    enabled: bool


class TwinRunRequest(BaseModel):
    delay: float = Field(default=0.40, ge=0.0, le=1.0)
    complaint: float = Field(default=0.35, ge=0.0, le=1.0)
    alignment: float = Field(default=0.25, ge=0.0, le=1.0)


class CustomerExportRequest(BaseModel):
    passphrase: str = Field(min_length=10, max_length=200)
    include_feedback: bool = True


class SecureTransferPacket(BaseModel):
    transfer_ref: str = Field(min_length=4, max_length=80)
    source_system: str = Field(min_length=2, max_length=120)
    purpose: str = Field(min_length=3, max_length=240)
    cipher: Literal["AES-256-GCM"] = "AES-256-GCM"
    payload_sha256: str = Field(min_length=64, max_length=64, pattern=r"^[0-9a-fA-F]{64}$")
    ciphertext_b64: str = Field(min_length=8, max_length=500000)

from datetime import timedelta
from sqlalchemy import select
from sqlalchemy.orm import Session
from ..core.config import get_settings
from ..core.security import hash_password
from ..db.models import Evidence, EvidenceOrigin, RolePolicy, SecurityShield, User
from ..services.common import utcnow
from ..services.ledger import append_entry


def seed_database(db: Session):
    settings = get_settings()
    if settings.DEMO_MODE and not db.execute(select(User).limit(1)).scalar_one_or_none():
        db.add_all([
            User(email="user@juristech.com", name="Regular User", role="regular_user", password_hash=hash_password(settings.DEMO_PASSWORD)),
            User(email="superadmin@juristech.com", name="Superadmin", role="superadmin", password_hash=hash_password(settings.DEMO_PASSWORD)),
        ])

    if not db.execute(select(RolePolicy).limit(1)).scalar_one_or_none():
        db.add_all([
            RolePolicy(role="regular_user", display_name="Regular User", description="Ask JurisTwin and receive only governed answers with safe sources.", enabled=True, can_manage_governance=False, can_view_sensitive_evidence=False),
            RolePolicy(role="superadmin", display_name="Superadmin", description="Resolve knowledge gaps, publish reusable decisions, manage controls and inspect evidence.", enabled=True, can_manage_governance=True, can_view_sensitive_evidence=True),
        ])

    if not db.execute(select(SecurityShield).limit(1)).scalar_one_or_none():
        db.add_all([
            SecurityShield(key="rbac", name="Role isolation", description="Regular users cannot call superadmin governance endpoints.", enabled=True),
            SecurityShield(key="pii_masking", name="PII masking", description="Potential email, phone and long account-number fragments are masked before unresolved questions are persisted.", enabled=True),
            SecurityShield(key="no_training", name="Client-data training isolation", description="Enterprise evidence is retrieval context only and is never added to the bundled ML training corpus.", enabled=True),
            SecurityShield(key="audit_chain", name="Tamper-evident audit chain", description="Security-sensitive actions are server-keyed HMAC-SHA256 chained for tamper detection and verification.", enabled=True),
            SecurityShield(key="abstention", name="Safe abstention", description="Low-confidence or insufficient-evidence questions become review items instead of hallucinated answers.", enabled=True),
            SecurityShield(key="pattern_revalidation", name="Decision-memory revalidation", description="Reusable decisions re-check their cited evidence at answer time and stop if the source becomes stale or invalid.", enabled=True),
            SecurityShield(key="feedback_escalation", name="User feedback escalation", description="A governed answer marked Needs review is routed back to the superadmin queue instead of being ignored.", enabled=True),
            SecurityShield(key="group_chat_scope", name="Group-channel privacy scope", description="Chat ingestion is restricted to approved group channels; private messages and 1:1 conversations are excluded.", enabled=True),
            SecurityShield(key="encrypted_export", name="Encrypted customer export", description="Customer interaction exports are PII-minimised, AES-256-GCM encrypted, superadmin-only and audit logged.", enabled=True),
            SecurityShield(key="secure_transfer", name="Secure system transfer", description="System-to-system transfers require encrypted transport and server-side scoped credentials; API keys are never exposed to the browser.", enabled=True),
        ])

    if not db.execute(select(Evidence).limit(1)).scalar_one_or_none():
        now = utcnow()
        rows = [
            # Income-document domain: authoritative current rule + stale contradictions + context.
            Evidence(evidence_ref="EV-INCOME-PO-001", source="Outlook Approval", title="Gig-worker income evidence waiver", body="For gig workers, verified bank statements may be accepted instead of payslips under the active income-evidence waiver.", rule_key="income_document_rule", claim="bank_statement_accepted", authority="Product Owner", authority_level=5, version="v4.2", status="active", sensitivity="internal", approved=True, superseded=False, created_at=now-timedelta(days=6)),
            Evidence(evidence_ref="EV-INCOME-FSD-003", source="FSD", title="Legacy income verification requirement", body="Income verification requires three months of payslips for every gig-worker application.", rule_key="income_document_rule", claim="payslips_required", authority="Functional Lead", authority_level=4, version="v3.0", status="outdated", sensitivity="confidential", approved=False, superseded=True, created_at=now-timedelta(days=120)),
            Evidence(evidence_ref="EV-INCOME-TEAMS-008", source="Teams Operations Channel", title="Operations handling message", body="Continue requesting payslips for gig workers until the old guide is updated.", rule_key="income_document_rule", claim="payslips_required", authority="Operations Officer", authority_level=2, version="current chat", status="active", sensitivity="internal", approved=False, superseded=False, created_at=now-timedelta(days=3)),
            Evidence(evidence_ref="EV-INCOME-QA-011", source="QA Repository", title="Income verification regression note", body="Several regression tests still expect payslip-only behaviour and must be aligned to the approved waiver.", rule_key="income_document_rule", claim="legacy_test_dependency", authority="QA Analyst", authority_level=2, version="suite-3", status="active", sensitivity="internal", approved=False, superseded=False, created_at=now-timedelta(days=4)),
            # Loan restructure domain.
            Evidence(evidence_ref="EV-LOAN-RISK-011", source="Risk Committee Policy", title="Restructuring threshold v5.1", body="Loan restructuring may be approved only when the risk score is 60 or below and the affordability review passes.", rule_key="loan_restructure_rule", claim="risk_threshold_60", authority="Risk Committee", authority_level=5, version="v5.1", status="active", sensitivity="internal", approved=True, superseded=False, created_at=now-timedelta(days=10)),
            Evidence(evidence_ref="EV-LOAN-LEGACY-004", source="Legacy Desk Guide", title="Old restructuring threshold", body="Restructuring approval is allowed for risk scores up to 70.", rule_key="loan_restructure_rule", claim="risk_threshold_70", authority="Credit Operations", authority_level=2, version="v4.3", status="outdated", sensitivity="internal", approved=False, superseded=True, created_at=now-timedelta(days=210)),
            Evidence(evidence_ref="EV-LOAN-QA-014", source="QA Repository", title="Restructuring regression pack", body="The latest regression pack validates affordability and risk-threshold edge cases against policy v5.1.", rule_key="loan_restructure_rule", claim="qa_current", authority="QA Analyst", authority_level=3, version="v5.1", status="active", sensitivity="internal", approved=False, superseded=False, created_at=now-timedelta(days=7)),
            # Notification domain.
            Evidence(evidence_ref="EV-NOTIFY-COMP-021", source="Compliance Approval", title="Customer notification SLA", body="Adverse decision notifications must be sent within three business days.", rule_key="notification_deadline", claim="business_days_3", authority="Compliance Manager", authority_level=5, version="v2.1", status="active", sensitivity="internal", approved=True, superseded=False, created_at=now-timedelta(days=8)),
            Evidence(evidence_ref="EV-NOTIFY-LEGACY-019", source="Legacy Procedure", title="Old customer notification timer", body="Customer notifications must be sent within three calendar days.", rule_key="notification_deadline", claim="calendar_days_3", authority="Operations", authority_level=2, version="v1.7", status="superseded", sensitivity="internal", approved=False, superseded=True, created_at=now-timedelta(days=200)),
            Evidence(evidence_ref="EV-NOTIFY-OPS-022", source="Teams Operations Channel", title="Manual follow-up instruction", body="Some operations instructions still use calendar-day language for customer follow-up.", rule_key="notification_deadline", claim="legacy_instruction", authority="Operations Officer", authority_level=2, version="current chat", status="active", sensitivity="internal", approved=False, superseded=False, created_at=now-timedelta(days=2)),
        ]
        db.add_all(rows)
        db.flush()
        append_entry(db, "SYSTEM_SEEDED", "system", {"evidence_count": len(rows), "primary_roles": ["regular_user", "superadmin"]})

    # Privacy scope metadata: collaboration chat is collected from approved group channels only.
    if not db.execute(select(EvidenceOrigin).limit(1)).scalar_one_or_none():
        origin_rows = [
            ("EV-INCOME-PO-001", "Outlook", "formal_approval", "Explicit business approval used as governed policy evidence."),
            ("EV-INCOME-FSD-003", "Document Repository", "shared_repository", "Relevant governed/legacy specification needed for contradiction analysis."),
            ("EV-INCOME-TEAMS-008", "Microsoft Teams", "group_channel", "Approved Operations group channel; private messages are not collected."),
            ("EV-INCOME-QA-011", "QA Repository", "shared_repository", "Relevant shared QA artefact used to assess downstream process drift."),
            ("EV-LOAN-RISK-011", "Risk Repository", "formal_approval", "Approved risk policy with decision authority."),
            ("EV-LOAN-LEGACY-004", "Document Repository", "shared_repository", "Legacy rule retained only to diagnose contradiction/version drift."),
            ("EV-LOAN-QA-014", "QA Repository", "shared_repository", "Shared regression evidence relevant to the active threshold."),
            ("EV-NOTIFY-COMP-021", "Compliance Repository", "formal_approval", "Approved compliance SLA."),
            ("EV-NOTIFY-LEGACY-019", "Document Repository", "shared_repository", "Legacy procedure retained only for contradiction analysis."),
            ("EV-NOTIFY-OPS-022", "Microsoft Teams", "group_channel", "Approved Operations group channel; private messages are not collected."),
        ]
        db.add_all([EvidenceOrigin(evidence_ref=ref, connector=connector, source_scope=scope, collection_reason=reason, private_message_excluded=True) for ref, connector, scope, reason in origin_rows])


    db.commit()

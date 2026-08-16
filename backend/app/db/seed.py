from datetime import datetime, timezone, timedelta
from sqlalchemy import delete, select
from sqlalchemy.orm import Session
from .models import *
from ..core.config import get_settings
from ..core.security import hash_password
from ..services.common import dumps, utcnow
from ..services.ledger import append_entry

DEMO_CASE = "JT-2026-084"
FLAGSHIP_CONFLICT = "CF-INCOME-001"


def reset_database(db: Session):
    # Keep users so the JWT that invoked reset remains valid on PostgreSQL where sequences do not reset.
    for model in [ConflictEvidence, LiveChallenge, LedgerEntry, SecurityAlert, DecisionVersion, DecisionContract, Approval, Simulation, CaseEvent, CustomerCase, Conflict, Evidence, Integration, SecurityShield, RolePolicy]:
        db.execute(delete(model))
    for u in db.execute(select(User)).scalars().all():
        u.active = True
    db.commit()
    seed_database(db)


def seed_database(db: Session):
    # Seed users once; operational demo state can be reset independently.
    settings = get_settings()
    if not db.execute(select(User).limit(1)).scalar_one_or_none():
        users = [
        ("operations@regulatedbank.com", "Michelle Tan", "manager", [DEMO_CASE]),
        ("officer@regulatedbank.com", "Daniel Lee", "officer", [DEMO_CASE, "JT-2026-086"]),
        ("intern@regulatedbank.com", "Aisha Lim", "intern", []),
        ("compliance@regulatedbank.com", "Farah Wong", "compliance_manager", [DEMO_CASE]),
        ("product@regulatedbank.com", "Product Owner", "product_owner", [DEMO_CASE]),
        ("qa014@regulatedbank.com", "QA-014", "qa_analyst", [DEMO_CASE]),
        ]
        for email, name, role, assigned in users:
            db.add(User(email=email, name=name, role=role, password_hash=hash_password(settings.DEMO_PASSWORD), assigned_case_refs=dumps(assigned)))
        db.flush()

    # If operational state already exists, startup is idempotent.
    if db.execute(select(CustomerCase).limit(1)).scalar_one_or_none():
        return

    role_policies = [
        ("manager", "Manager", "Full decryption authority & override permissions", True, 3, True, True, True, True),
        ("officer", "Officer", "Assigned customer twin record actions", True, 2, False, False, False, False),
        ("intern", "Intern", "Restricted case viewer, total PII redaction", True, 1, False, False, False, False),
        ("compliance_manager", "Compliance Auditor", "Read-only ledger access plus governance controls", True, 3, True, False, True, True),
        ("product_owner", "Product Owner", "Digital Twin weight modifications and sandbox simulations", True, 3, True, True, True, True),
        ("qa_analyst", "QA Analyst", "Waiver verification triggers & draft document reviews", True, 2, False, False, False, True),
    ]
    for role, display, desc, enabled, sensitivity, override, twin, export, review in role_policies:
        db.add(RolePolicy(role=role, display_name=display, description=desc, enabled=enabled, max_sensitivity=sensitivity, can_override=override, can_modify_twin=twin, can_export_ledger=export, can_review_bodyguard=review))

    shields = [
        ("data_masking", "Data Sensitivity Masking", "Shield PII across lower authority tiers", True, {"mode":"role-aware"}),
        ("dlp", "Active DLP Protection", "Prevent unapproved downloads of restricted evidence", True, {"restricted_downloads":"blocked"}),
        ("ledger_retention", "7-Year Ledger Retention", "Lock audited records into non-mutable DB state", True, {"years":7}),
        ("ooh_guard", "OOH Modification Guard", "Flag approved decision modifications during OOH hours", True, {"start":"19:00","end":"07:00"}),
    ]
    for key, name, desc, enabled, value in shields:
        db.add(SecurityShield(key=key, name=name, description=desc, enabled=enabled, value_json=dumps(value)))

    now = utcnow()
    integrations = [
        ("outlook", "Outlook Extractor", "mail", "connected", 12410, now-timedelta(minutes=3), {"metric":"mail objects", "errors":0, "adapter_mode":"deterministic_finals_adapter"}),
        ("teams", "MS Teams Listener", "chat", "connected", 45201, now-timedelta(minutes=1), {"metric":"chat lines", "errors":0, "adapter_mode":"deterministic_finals_adapter"}),
        ("gmail", "Gmail Connector", "mail", "inactive", 0, None, {"metric":"objects", "errors":0, "note":"Configuration pending", "adapter_mode":"deterministic_finals_adapter"}),
        ("sharepoint", "SharePoint Indexer", "documents", "connected", 1420, now-timedelta(minutes=12), {"metric":"files indexed", "errors":1, "note":"1 sync warning", "adapter_mode":"deterministic_finals_adapter"}),
        ("onedrive", "OneDrive Loader", "documents", "connected", 893, now-timedelta(hours=1), {"metric":"files indexed", "errors":0, "adapter_mode":"deterministic_finals_adapter"}),
        ("clickup", "ClickUp Workspace", "tasks", "connected", 512, now-timedelta(minutes=6), {"metric":"tickets synced", "errors":2, "note":"2 error blocks", "adapter_mode":"deterministic_finals_adapter"}),
        ("customer_core", "Customer Core API", "customer", "connected", 128, now, {"metric":"customer records", "errors":0, "note":"Consensus validated", "realtime":True}),
        ("qa", "QA Repository", "qa", "connected", 38, now-timedelta(minutes=15), {"metric":"policies tracked", "errors":0, "adapter_mode":"deterministic_finals_adapter"}),
        ("postgres", "PostgreSQL DB", "database", "connected", 1426, now, {"metric":"records mirrored", "errors":0, "note":"Mirror transactional", "realtime":True}),
        ("vector", "Local Semantic Retrieval Index", "semantic", "connected", 142400, now, {"metric":"indexed evidence terms", "errors":0, "engine":"BM25 + cosine", "pilot_target":"ChromaDB", "adapter_mode":"local_runtime", "note":"Finals runtime uses explainable local retrieval; ChromaDB is a pilot-target adapter."}),
        ("webhook", "Signed Webhook Gateway", "ingress", "connected", 0, now, {"metric":"authenticated live events", "errors":0, "adapter_mode":"live_http_ingress", "auth":"HMAC-SHA256", "replay_protection":True, "realtime":True, "note":"Genuine external HTTP ingress; use send_live_webhook.py from a second terminal."}),
    ]
    for key, name, kind, status, count, last_sync, details in integrations:
        db.add(Integration(key=key, name=name, kind=kind, status=status, object_count=count, last_sync_at=last_sync, details_json=dumps(details)))

    # 128 active cases. All three seeded conflicts have real operational cohorts so a judge can
    # click any conflict and drive it through simulation → governance → decision publication.
    for i in range(128):
        case_ref = DEMO_CASE if i == 0 else f"JT-2026-{85+i:03d}"
        if i < 27:
            conflict_ref, cohort = FLAGSHIP_CONFLICT, "gig-worker-income"
            customer_type, application_type = "Gig worker", "Financial Assistance Application"
            risk_status, blocker = "High", "Income document rule conflict"
            pending = 4.2
        elif i < 38:
            conflict_ref, cohort = "CF-RESTRUCTURE-002", "loan-restructure"
            customer_type, application_type = "Borrower", "Loan Restructuring Application"
            risk_status, blocker = "Medium", "Restructuring approval threshold mismatch"
            pending = 3.8
        elif i < 44:
            conflict_ref, cohort = "CF-NOTIFY-003", "customer-notification"
            customer_type, application_type = "Retail customer", "Adverse Decision Notification"
            risk_status, blocker = "Medium", "Notification SLA definition mismatch"
            pending = 3.0
        else:
            conflict_ref, cohort = None, "baseline"
            customer_type, application_type = "Retail customer", "Retail Banking Application"
            risk_status, blocker = "Low", None
            pending = round(0.3 + (i % 20)*0.1, 1)
        customer = "Aina Rahman" if i == 0 else f"Customer {i+1:03d}"
        db.add(CustomerCase(
            case_ref=case_ref, customer_name=customer, customer_type=customer_type,
            application_type=application_type, owner_email="officer@regulatedbank.com", status="active",
            risk_status=risk_status, sentiment="Frustrated" if i == 0 else ("Concerned" if conflict_ref else "Neutral"),
            pending_days=pending, conflict_ref=conflict_ref, current_blocker=blocker, protected=(i >= 34),
            metadata_json=dumps({"cohort": cohort, "application_value": 250000 if i == 0 else 50000 + i*500}),
        ))
    db.flush()
    flagship = db.execute(select(CustomerCase).where(CustomerCase.case_ref == DEMO_CASE)).scalar_one()
    base = datetime(2026, 8, 6, 10, 30, tzinfo=timezone.utc)
    events = [
        ("FSD v3.0", "FSD v3.0", "Flagged missing payslips per standard ruleset.", base, "warning"),
        ("Outlook", "Outlook Approval", "Product Owner approved: 'Bank statements may be accepted in place of payslips.'", base + timedelta(minutes=45), "success"),
        ("Teams", "Teams Message", "Operations staff directed: 'Continue requesting payslips anyway to be safe.'", base + timedelta(minutes=72), "warning"),
        ("Customer", "Customer Complaint", "'You keep asking for papers I don't have. Please resolve!'", base + timedelta(minutes=155), "critical"),
    ]
    for source, title, desc, t, severity in events:
        db.add(CaseEvent(case_id=flagship.id, source=source, title=title, description=desc, event_time=t, severity=severity))

    evidence_rows = [
        ("EV-BANK-084", "Customer Document Vault", "Bank Statement", "Aina Rahman submitted three consecutive monthly bank statements with recurring salary-equivalent credits. Document verified against the active income-evidence waiver.", "income_document_rule", "verified_bank_statement", "Tier 2 Verification", 4, "v4.2", "active", "restricted", DEMO_CASE, True, False),
        ("EV-OUTLOOK-001", "Outlook Approval", "PO_Waiver_Mail_Jul20", "Product Owner authorises alternative income evidence for gig workers. Bank statements may be accepted in place of payslips.", "income_document_rule", "bank_statement_accepted", "Product Owner", 5, "v4.0", "active", "confidential", DEMO_CASE, True, False),
        ("EV-TEAMS-001", "Teams Message", "Teams_Chat_Log_OpsOps", "Continue requesting payslips anyway to be safe until the FSD is updated.", "income_document_rule", "payslips_required", "Operations Officer", 2, "current message", "active", "internal", DEMO_CASE, False, False),
        ("EV-FSD-003", "FSD", "FSD_Requirements_v3_Doc", "Income verification requires three months of payslips.", "income_document_rule", "payslips_required", "Functional Lead", 4, "v3.0", "outdated", "confidential", DEMO_CASE, False, True),
        ("EV-GUIDE-002", "Training Guide", "Operations Training Guide", "Request three months of payslips for all gig-worker income verification cases.", "income_document_rule", "payslips_required", "Operations Training", 2, "v2.8", "outdated", "internal", DEMO_CASE, False, False),
        ("EV-CORE-084", "Customer Core System", "Customer Case JT-2026-084", "Application stalled because income document is marked missing even though bank statement is verified.", "income_document_rule", "operational_stall", "Customer Core", 3, "live", "active", "restricted", DEMO_CASE, False, False),
        ("EV-COMPLAINT-084", "Gmail Connector", "Customer Complaint", "You keep asking for papers I don't have. Please resolve.", "income_document_rule", "customer_frustrated", "Customer", 1, "live", "active", "restricted", DEMO_CASE, False, False),
        ("EV-QA-084", "QA Repository", "Internal QA Memo", "Eight QA tests still assert payslips-only behaviour.", "income_document_rule", "qa_outdated", "QA Analyst", 3, "v3-suite", "active", "confidential", DEMO_CASE, False, False),
        ("EV-CONSENSUS-001", "Decision Ledger", "Consensus Ledger Protocol", "Consensus rules path mapped dynamically from Credit Policy v4.2 with complete approval lineage.", "consensus_protocol", "governed_path", "Compliance Manager", 6, "v4.2", "active", "confidential", None, True, False),
        ("EV-RISK-011", "SharePoint Indexer", "Loan Restructuring SOP", "Risk Committee v5.1 permits delegated loan restructuring only when the risk score is 60 or below and affordability review passes.", "loan_restructure_rule", "risk_threshold_60", "Risk Committee", 5, "v5.1", "active", "restricted", "JT-2026-112", True, False),
        ("EV-RISK-LEGACY", "SharePoint Indexer", "Legacy Restructuring Desk Guide", "Legacy desk guidance allows restructuring approval up to risk score 70.", "loan_restructure_rule", "risk_threshold_70", "Credit Operations", 2, "v4.3", "outdated", "internal", "JT-2026-112", False, False),
        ("EV-NOTIFY-021", "Outlook Extractor", "Customer Notification SLA Approval", "Compliance approved a three business-day notification deadline for adverse decisions.", "notification_deadline", "business_days_3", "Compliance Manager", 5, "v2.1", "active", "confidential", "JT-2026-123", True, False),
        ("EV-LEGACY-019", "SharePoint Indexer", "Legacy Notification Procedure", "Customer notifications must be sent within three calendar days.", "notification_deadline", "calendar_days_3", "Operations", 2, "v1.7", "superseded", "internal", "JT-2026-123", False, True),
        ("EV-QA-RESTRUCTURE", "QA Repository", "Restructuring Regression Pack", "Regression pack tracks 14 approval edge cases against the latest restructuring policy.", "loan_restructure_rule", "qa_current", "QA Analyst", 3, "v5.1", "active", "internal", "JT-2026-112", False, False),
        ("EV-TEAMS-NOTIFY", "MS Teams Listener", "Notification Ops Chat", "Operations team is still using calendar-day language in manual customer follow-up instructions.", "notification_deadline", "legacy_instruction", "Operations Officer", 2, "current", "active", "internal", "JT-2026-123", False, False),
        ("EV-CORE-091", "Customer Core API", "Restructuring Case Mirror", "Customer case is waiting for a threshold decision from the risk engine.", "loan_restructure_rule", "operational_wait", "Customer Core", 3, "live", "active", "restricted", "JT-2026-112", False, False),
    ]
    evidences = {}
    for row in evidence_rows:
        project = "Sentinel" if row[4] == "income_document_rule" else ("Credit Operations" if row[4] == "loan_restructure_rule" else ("Compliance Operations" if row[4] == "notification_deadline" else "Governance Core"))
        customer = "Aina Rahman" if row[11] == DEMO_CASE else ("System Audit" if not row[11] else row[11])
        tier = 3 if row[7] >= 5 else (2 if row[7] >= 3 else 1)
        e = Evidence(evidence_ref=row[0], source=row[1], title=row[2], body=row[3], rule_key=row[4], claim=row[5], authority=row[6], authority_level=row[7], version=row[8], status=row[9], sensitivity=row[10], case_ref=row[11], approved=row[12], superseded=row[13], metadata_json=dumps({"project": project, "customer": customer, "decision_tier": tier}))
        db.add(e); db.flush(); evidences[e.evidence_ref] = e

    conflicts = [
        Conflict(conflict_ref=FLAGSHIP_CONFLICT, name="Income-document eligibility", rule_key="income_document_rule", severity="Critical", status="unresolved",
                 root_cause="FSD v3.0 and training materials were not updated following the Product Owner's bank-statement waiver authorization. Operations continue using legacy criteria.",
                 recommendation="Align the complete process: update FSD and training, notify officers, review affected applications, update QA tests and block duplicate requests.",
                 confidence=0.942, affected_customers=27, systems_affected=5, approved_evidence_ref="EV-OUTLOOK-001"),
        Conflict(conflict_ref="CF-RESTRUCTURE-002", name="Loan restructuring approval mismatch", rule_key="loan_restructure_rule", severity="High", status="unresolved",
                 root_cause="Risk engine threshold and restructuring SOP were updated on different dates.", recommendation="Synchronise approval threshold and recalculate the 11 affected cases.", confidence=0.89, affected_customers=11, systems_affected=3),
        Conflict(conflict_ref="CF-NOTIFY-003", name="Customer notification deadline", rule_key="notification_deadline", severity="Medium", status="unresolved",
                 root_cause="Legacy SLA timer uses calendar days while new compliance policy uses business days.", recommendation="Publish one canonical SLA definition and update notification scheduler.", confidence=0.83, affected_customers=6, systems_affected=2),
    ]
    for c in conflicts: db.add(c)
    db.flush()
    conflict_map = {c.conflict_ref: c for c in db.execute(select(Conflict)).scalars().all()}
    relation_sets = {
        FLAGSHIP_CONFLICT: {
            "EV-OUTLOOK-001": "approved", "EV-TEAMS-001": "informal", "EV-FSD-003": "conflict",
            "EV-GUIDE-002": "conflict", "EV-CORE-084": "operational", "EV-COMPLAINT-084": "context", "EV-QA-084": "conflict",
        },
        "CF-RESTRUCTURE-002": {
            "EV-RISK-011": "approved", "EV-RISK-LEGACY": "conflict", "EV-QA-RESTRUCTURE": "context", "EV-CORE-091": "operational",
        },
        "CF-NOTIFY-003": {
            "EV-NOTIFY-021": "approved", "EV-LEGACY-019": "conflict", "EV-TEAMS-NOTIFY": "informal",
        },
    }
    for conflict_ref, relations in relation_sets.items():
        conflict = conflict_map[conflict_ref]
        for ref, relation in relations.items():
            db.add(ConflictEvidence(conflict_id=conflict.id, evidence_id=evidences[ref].id, relation=relation))

    # Pre-seed a small immutable audit history (not the final decision contract).
    append_entry(db, "EVIDENCE_INGESTED", "outlook-extractor", {"evidence_ref": "EV-OUTLOOK-001", "authority": "Product Owner"})
    append_entry(db, "CONFLICT_DETECTED", "conflict-engine", {"conflict_ref": FLAGSHIP_CONFLICT, "affected_customers": 27})
    db.commit()

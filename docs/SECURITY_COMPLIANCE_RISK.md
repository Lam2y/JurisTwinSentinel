# Security, Compliance & Risk Resilience — Finals Proof v11

## Positioning

JurisTwin Sentinel is a hackathon prototype with **compliance-by-design evidence**, not a certified compliant production system. This distinction should be stated clearly in Q&A.

The current implementation maps controls to relevant reference frameworks including Malaysia’s PDPA, Bank Negara Malaysia’s revised Risk Management in Technology (RMiT) policy, NIST AI RMF / GenAI risk guidance and OWASP API Security practices.

## Control inventory

### Identity and authorization
- JWT identity.
- Two roles with backend-enforced authorization.
- Regular user cannot call `/api/admin/*` or protected governance routes.
- Feedback endpoint checks interaction ownership.
- Critical RBAC and audit-chain controls cannot be disabled from the UI.

### Data privacy
- Email, phone and long account-like identifiers masked before unresolved prompts/feedback are persisted.
- Evidence intake rejects likely PII.
- Enterprise evidence is used for retrieval; it is not appended to the learned classifier corpus.
- Resolved review items older than the configured retention period are purged on startup.
- Audit lineage and published decision memory remain so governance stays explainable.

### AI decision safety
- confidence-aware abstention;
- evidence coverage gate;
- approved/current source requirement;
- canonical split-brain detector;
- pattern source revalidation;
- deterministic fallback if learned routing fails;
- human publication authority;
- uncertainty note for source-less manual resolutions;
- decision-memory rollback;
- user negative-feedback escalation.

### API/application hardening
- 1 MB request body boundary;
- Pydantic validation;
- per-path burst rate containment;
- restricted CORS;
- CSP;
- X-Frame-Options DENY;
- nosniff;
- no-store cache policy;
- no-referrer;
- browser permissions disabled for camera/mic/geolocation;
- request ID and processing-time headers;
- global unexpected-error containment.

### Audit integrity
The ledger uses a server-keyed HMAC-SHA256 chain. Each security-sensitive entry depends on the prior hash. The regression suite proves that modifying an old payload causes verification failure.

The demo creates a stable local generated key if no environment secret exists. Production should use a managed secret store.

## Risk register

| Risk | Severity | Primary control |
|---|---|---|
| Hallucinated policy answer | Critical | confidence + coverage + canonical gates |
| Contradictory source leakage | Critical | narrow regular-user publication payload |
| Two approved sources disagree | Critical | canonical split-brain fail-closed gate |
| Unauthorized governance | High | backend RBAC |
| PII stored in review queue | High | pre-persistence masking / ingest rejection |
| Audit history tampering | High | HMAC-SHA256 chain |
| Bad human resolution reused | High | match threshold + lineage revalidation + rollback |
| Misleading source attribution | High | final-response/source consistency gate |
| ML layer unavailable | Medium | deterministic router + abstention |
| Stale review data retained | Medium | startup retention enforcement |

## Live resilience self-test

The superadmin can run the self-test from Management Controls. The result is persisted and audit logged. Current checks cover:

1. database round-trip;
2. least-privilege RBAC;
3. PII minimisation;
4. audit-chain integrity;
5. hybrid AI readiness;
6. governed evidence availability;
7. contradiction detector;
8. critical safety shields;
9. request/input containment;
10. offline core continuity;
11. review-data retention enforcement.

## Framework mapping — careful wording for judges

### Malaysia PDPA 2010 + Amendment Act 2024
Relevant design themes: security, data minimisation, accountability and data-management controls. JurisTwin demonstrates PII minimisation, purpose-limited retrieval, least privilege, auditable governance and retention enforcement. This is not a legal compliance determination.

### BNM RMiT — revised policy issued 28 November 2025
Relevant design themes include technology/cyber risk, resilience, secure digital services and secure adoption of advanced technology. JurisTwin demonstrates access controls, auditability, fail-closed AI behavior, self-testing, offline continuity and reversible governance. Applicability depends on the deploying regulated entity and use case.

### NIST AI RMF 1.0 / Generative AI Profile
JurisTwin maps to Govern/Map/Measure/Manage through human decision authority, model/risk transparency, measured runtime behavior, safe abstention, risk register, feedback and rollback.

### OWASP API Security
JurisTwin addresses authentication/authorization, request validation, resource containment, object ownership, restricted cross-origin access and browser/API hardening.

## What not to claim

Do not say:
- “BNM certified.”
- “PDPA compliant” as a blanket legal claim.
- “NIST certified.”
- “unhackable.”
- “zero risk.”

Say:

“We mapped the prototype controls to relevant security and AI-risk guidance, and the UI shows the implementation evidence. Formal compliance requires the deploying institution’s legal, security and regulatory assessment.”


## v11 privacy collection boundary

- Approved group-channel messages are eligible only when policy-relevant.
- PM/DM/1:1 content is blocked before evidence persistence.
- Unrelated group chatter is rejected by the policy-domain relevance gate.
- Formal approvals and governed shared repositories remain eligible as authoritative enterprise evidence.
- Evidence-origin metadata is visible to Superadmins and participates in the retrieval boundary.

## v11 customer-data export

Customer-data export is Superadmin-only, PII-minimised and AES-256-GCM encrypted. A one-time operator passphrase derives the encryption key using PBKDF2-HMAC-SHA256; the passphrase is not persisted. Every successful encrypted export is audit logged.

## v11 system-to-system transfer

The integration boundary accepts ciphertext-only packets and requires a scoped API key, timestamped HMAC-SHA256 signature, ciphertext digest and replay-window validation. Production can enforce HTTPS/TLS. Browser-facing APIs expose only the API-key fingerprint.

## v11 audit proof

The Audit Evidence appendix translates the live HMAC-SHA256 ledger into three judge-readable views: Accountability, Tamper Evidence and Data Lifecycle. The full event ledger remains available for technical Q&A.

## v11 risk additions

The runtime risk register explicitly includes private-message overcollection, customer-export exposure and system-transfer interception/spoofing, with implemented controls and residual limitations.

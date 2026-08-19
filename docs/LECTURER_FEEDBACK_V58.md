# JurisTwin Sentinel v5.8 — Lecturer Feedback Implementation

This build turns source governance, privacy, export control, auditability, and freshness into first-class product controls rather than presentation-only claims.

## 1. Definite management answer with governed sources

Ask JurisTwin now presents one management-facing answer first, followed by the exact governed source(s) used to reach it.

Resolution is deliberately not a naïve global majority vote. JurisTwin first removes ineligible/private sources, then applies authority precedence. If there is no approved canonical source, majority is used only among sources at the same highest authority tier. This prevents many casual messages from overruling one formally approved policy.

## 2. Source Scope Control

A new **Data Governance** page lets authorised managers/compliance users control which connector sources are eligible for retrieval and which may act as policy authority.

Default privacy posture:

- Microsoft Teams: approved group/channel conversations only; personal/1:1 DMs are blocked.
- Outlook/Gmail: official management/policy mail may be policy evidence; casual coworker mail is excluded.
- SharePoint: governed libraries may be authoritative.
- Customer Core: operational impact/context only; it cannot define policy.
- QA repositories: context only unless formally approved.
- OneDrive: excluded by default.
- Live webhook evidence: appears immediately but is quarantined until governance establishes authority.
- Client data is never enabled for model training.

The configurable action is **index/retrieval scope**, not training on client communications.

## 3. Customer-data security and export control

Customer export is enforced server-side with RBAC:

- Masked export: Manager and Compliance.
- Full export: Compliance only.
- Other roles: forbidden.

Every allowed or blocked export attempt is written to the tamper-evident decision ledger with actor and reason.

## 4. Transfer security and secrets

The Data Governance page explains the data path from connector authentication through source-scope filtering, DLP/RBAC controls and the governed index.

Implemented/represented controls include signed HMAC-SHA256 webhook ingress and server-side environment variables for secrets. Production deployment guidance requires TLS 1.2+/1.3 at the reverse proxy/API gateway and encrypted managed storage. The local finals runtime is described truthfully as loopback/local HTTP rather than claiming TLS that is not present in the demo.

## 5. Audit trail

Every Ask JurisTwin answer and memory search is logged with the authenticated actor. Audit records include a policy-safe question excerpt, SHA-256 question fingerprint, rule key, resolution mode, and sources used. Source-policy changes and customer exports are also ledgered.

The Data Governance page provides an Audit Log view for rapid investigation of who queried, changed, or exported governed information.

## 6. Real-time behavior

Answers are recomputed on every request against current governed state. Connector/source policy updates affect subsequent answers immediately. Signed live evidence appears immediately in Evidence Lab but cannot silently become policy authority.

The Data Governance page refreshes its governance/freshness view periodically while open so the demo visibly behaves as a live system rather than a static dashboard.

## Verification

- Backend automated tests: **57/57 passed**.
- Championship preflight: **32/32 passed**.
- JavaScript syntax validation: passed.
- Manual governance smoke tests verified source exclusion, governed-answer resolution, masked export, forbidden full export for Manager, and audit/security overview endpoints.

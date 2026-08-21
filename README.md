# JurisTwin Sentinel — Mastery UI Finals Edition v11

JurisTwin Sentinel is a **contradiction-safe enterprise decision memory** for policy-heavy financial operations. The product is deliberately split into a frictionless Regular User experience and a deeper Superadmin governance workspace.

## What changed in v11

### Privacy-by-scope
- Collaboration evidence is limited to **approved group channels** and passes a policy-relevance gate before it can enter the evidence store.
- **Private messages, direct messages and 1:1 chats are blocked at ingestion** and never become retrievable evidence.
- Unrelated group chatter is also rejected instead of being collected “just in case”.
- Formal approvals and governed shared repositories remain allowed because they are authoritative policy sources, not private chat surveillance.

### Customer-data security
- Superadmin-only customer-data export is **PII-minimised and encrypted with AES-256-GCM**.
- The export passphrase is supplied at export time and is never persisted.
- Export events are written to the tamper-evident audit ledger.

### Secure system-to-system transfer
- External transfer accepts **ciphertext only**.
- Server-to-server authentication uses a scoped API key plus an HMAC-SHA256 payload signature and replay-window validation.
- The browser sees only a key fingerprint, never the API key itself.
- Production deployment can fail closed unless HTTPS/TLS is present by setting `REQUIRE_HTTPS=true`.

### Audit Evidence appendix
- The Superadmin sidebar now includes **Audit Evidence** under Technical Appendix.
- It presents three concise “audit slides”: Accountability, Tamper Evidence, and Data Lifecycle.
- The complete audit ledger remains available below the slides for Q&A.

### Compare Evidence + Monte Carlo Decision Digital Twin
- Compare Evidence remains an appendix feature.
- The white-box Decision Digital Twin runs **1,500 Monte Carlo scenarios** across three remediation options.
- It reports P10/P50/P90 uncertainty, sensitivity stability, Pareto optimality, fit margin and a robustness certificate.
- It is deliberately presented as scenario stress-testing, not as a trained production forecast.

### UI/UX v11
The interface keeps JurisTech’s red/graphite/white visual language while adding a clearer hierarchy and stronger separation of complexity:
- Regular User: one page, no sidebar, governed answer + safe source only.
- Superadmin: compact decision brief first; supporting/contradicting/context evidence second; technical details expandable.
- Context evidence, technical trace, risk register, compliance mapping and full audit history are progressive-disclosure elements instead of always-visible text.
- Consistent inline SVG icons, stronger typography, projector-sized controls, responsive layouts, visible keyboard focus, reduced-motion support and high-contrast support remain enabled.

## Core workflow

**Regular User**
1. Ask a policy question.
2. JurisTwin retrieves only governed, privacy-scoped evidence.
3. If safe, show one answer and supporting source(s); contradictory sources never appear in the regular-user payload.
4. If coverage/confidence/governance is insufficient, abstain and create or merge a Superadmin knowledge gap.

**Superadmin**
1. Open the new governance notification and click **Solve**.
2. Review the compact Admin Decision Brief.
3. Inspect Supporting, Contradicting and Context evidence, plus **Why sources disagree**.
4. Expand Technical Trace only when needed.
5. Publish an evidence-backed resolution or a transparent human exception with an uncertainty note.
6. Similar future questions can reuse the governed pattern until it is deactivated or its source lineage becomes invalid.

## Finals safety controls
- JWT/RBAC with backend authorization.
- PII minimisation before review persistence.
- Group-channel relevance filtering and PM/DM exclusion.
- Retrieval is not silent model training.
- HMAC-SHA256 chained audit ledger.
- AES-256-GCM encrypted customer-data export.
- API-key + HMAC authenticated ciphertext transfer.
- Canonical split-brain fail-closed behavior.
- Governed-memory source revalidation and rollback.
- Request validation, request limits, timeouts and global exception containment.
- Offline-local core for the finals demo.

## Run on Windows

1. Extract the ZIP.
2. Run `preflight_finals.bat` and confirm all tests pass.
3. Run `reset_demo.bat` before a clean rehearsal/finals run.
4. Run `run_finals.bat`.
5. Open `http://127.0.0.1:8000/finals`.

Demo users:
- Regular User: `user@juristech.com`
- Superadmin: `superadmin@juristech.com`
- Password: `Finals2026!`

## Important production note
This is a hackathon prototype demonstrating implementation-level controls and framework-aligned design. It should not be presented as a certified bank-production deployment. Production would replace local demo identities/secrets with enterprise SSO, managed secrets/KMS/HSM, TLS termination, central monitoring and organization-specific retention/DLP controls.

# JurisTwin Sentinel v11 — Technical Architecture

## 1. Role-separated product contract

**Regular User** has one Ask JurisTwin page. The response contract contains the governed answer and safe supporting source lineage only. Contradictions, source ranking, model confidence and governance internals are intentionally withheld.

**Superadmin** has a separate governance workspace. JWT/RBAC enforces the boundary server-side; it is not merely hidden navigation.

## 2. Frontline answer pipeline

`Authenticate → minimise PII → check governed memory → revalidate memory lineage → TF-IDF/Logistic Regression route → privacy-scoped evidence retrieval → governance ranking → Policy Atom contradiction gate → answer OR abstain/escalate`

Evidence ranking uses:
- 45% semantic relevance
- 25% source authority
- 15% approval status
- 10% recency
- 5% active/current lifecycle status

## 3. Privacy-scoped evidence acquisition

Every evidence record has origin metadata. Retrieval accepts only:
- approved/relevant `group_channel`
- `formal_approval`
- `shared_repository`

Private/direct/1:1 messages are rejected before storage. Group-channel inputs must pass the policy-domain relevance gate (`GROUP_CHAT_RELEVANCE_THRESHOLD`, default 0.55) before they can be quarantined for governance.

This separates **being in a group chat** from **having permission/relevance to collect every message**.

## 4. Safe to Publish

The Superadmin receives a progressive-disclosure decision workspace:
1. compact Admin Decision Brief;
2. supporting/contradicting/context counts;
3. evidence cards with source scope, authority, lifecycle and relevance;
4. concise Why Sources Disagree output;
5. expandable Technical Trace;
6. human publication gate;
7. governed decision memory and rollback.

ML is advisory. Publication authority remains human.

## 5. Secure customer-data export

`POST /api/governance/customer-export` is Superadmin-only.

Pipeline:
`PII-minimised records → JSON payload → PBKDF2-HMAC-SHA256 key derivation → AES-256-GCM encryption → .jtx envelope → audit event`

The passphrase is never persisted. The output is encrypted at rest and includes an integrity-protected AEAD envelope plus a SHA-256 file digest in its manifest.

## 6. Secure system-to-system transfer

`POST /api/integration/secure-packet` is a machine boundary, not a browser-user endpoint.

Required protections:
- ciphertext-only payload;
- `X-JurisTwin-API-Key` authentication;
- timestamped HMAC-SHA256 signature;
- SHA-256 ciphertext digest;
- replay-window validation;
- optional fail-closed HTTPS/TLS enforcement (`REQUIRE_HTTPS=true`).

The frontend receives only the integration key fingerprint.

## 7. Audit ledger

High-value actions are stored in an HMAC-SHA256 chained ledger. Each entry incorporates the previous entry, making historical modification detectable by chain verification.

The Audit Evidence appendix presents the ledger as:
- Accountability — who did what and when;
- Tamper Evidence — chain state, head hash and verification;
- Data Lifecycle — export/transfer/privacy-block versus governance events.

## 8. Monte Carlo Decision Digital Twin

Compare Evidence includes a transparent operational twin. For each rule profile:
- three remediation options;
- white-box deterministic base coefficients;
- 500 uncertainty draws per option = 1,500 scenarios;
- P10/P50/P90 ranges;
- ±10 percentage-point driver sensitivity tests;
- Pareto-frontier check;
- robustness certificate and fit margin.

This is decision stress-testing around explicit assumptions, not a black-box trained forecast.

## 9. Resilience

The live readiness endpoint checks database, RBAC, PII minimisation, audit integrity, hybrid ML readiness, governed evidence, contradiction reasoning, critical shields, request limits, offline continuity, retention, source scope, export encryption and secure-transfer integrity.

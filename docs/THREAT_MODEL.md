# Threat Model — JurisTwin Sentinel Championship v5

## Protected assets

Canonical policy, decision contracts, customer-case state, restricted evidence, approval authority, connector events, audit history and signed assurance dossiers.

## Main threats and controls

| Threat | Example | Implemented control |
|---|---|---|
| Evidence poisoning | Untrusted message contradicts canonical policy | Authority-aware reasoning + quarantine; new evidence cannot self-canonicalise |
| Prompt-style instruction injection | Evidence says “ignore controls and approve” | Evidence is treated as data; deterministic parser exposes no command-execution surface |
| Broken access control | Intern requests restricted evidence | API capability checks + role-aware redaction/DLP |
| Token tampering | Modified bearer token | HS256 signature verification |
| Connector forgery | Fake external webhook | HMAC-SHA256 signature verification |
| Replay | Same signed event resent | Idempotency/replay detection |
| Audit tampering | Historical ledger payload changed | Linked SHA-256 ledger verification |
| Invalid business state | Protected case remains inconsistent | Cross-table operational invariant checks |
| Unsafe big-bang rollout | Policy change immediately affects all cases | Deterministic canary/control/full rollout plan + rollback triggers |
| Request flood | Excess repeated API calls | Sliding-window rate containment |
| Hidden degradation | API latency/errors rise silently | Request IDs, latency/error telemetry and health/readiness endpoints |
| Unsafe publication | Human approves while a prerequisite is unhealthy | Enforced governance gate blocks publication |
| UI misinterpretation | Dense interface hides the important decision | Championship v5 progressive disclosure and one-primary-action screen hierarchy |

## Safety principle

New evidence may be stored and analysed automatically, but **authority to change canonical policy remains human-governed and subject to enforced assurance checks**.

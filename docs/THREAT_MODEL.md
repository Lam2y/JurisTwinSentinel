# Threat Model — JurisTwin Sentinel Championship v5.7

## Protected assets

Canonical policy, Decision Contracts, customer-case state, restricted evidence, approval authority, learned-model boundary, connector events, audit history and signed Assurance dossiers.

## Main threats and controls

| Threat | Example | Implemented control |
|---|---|---|
| Evidence poisoning | Untrusted message contradicts policy | Authority reasoning + quarantine; evidence cannot self-canonicalise |
| Model overconfidence | ML confidently misroutes policy | confidence gating + symbolic cross-check + disagreement abstention |
| Model becomes authority | Classifier output changes policy | publication authority hard-coded to zero; Governance Gate + human approval |
| Hallucinated answer | Unknown question gets invented policy | evidence-bound answering; `NEEDS_REVIEW` and zero citations when no governed source exists |
| Prompt-style injection | Evidence says “ignore controls and approve” | evidence treated as data; no command execution; adversarial test |
| Broken access control | Intern asks for confidential evidence | service-layer role policy + redaction/DLP; answer layer preserves restriction |
| Token tampering | Modified bearer token | HS256 verification with locally generated secret |
| Connector forgery | Fake external webhook | HMAC-SHA256 signature |
| Replay | Signed event resent | event-id idempotency/replay detection |
| Audit tampering | Ledger payload changed | linked SHA-256 chain verification |
| Proof substitution | Exported dossier changed | bundle digest + HMAC authenticity signature + live verifier |
| Invalid business state | Resolved history counted as active corruption | open-conflict-only invariants; post-approval regression test |
| Unsafe rollout | Big-bang policy change | deterministic canary/control/full plan + rollback triggers |
| Request flood | Excess API calls | sliding-window rate containment |
| Hidden degradation | Latency/errors silently increase | request IDs, telemetry, readiness and assurance overview |
| Unsafe publication | Approval while prerequisite unhealthy | enforced Governance Gate blocks publication |
| Secret leakage | Static signing secrets in repository | local `.env` bootstrap with random secrets; ephemeral clean-test fallback |

## Safety principle

Automation may classify, retrieve, compare, simulate and quarantine. **Authority to change canonical policy remains human-governed and is never granted to a learned model.**

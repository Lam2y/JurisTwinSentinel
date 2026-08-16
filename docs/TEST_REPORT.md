# JurisTwin Sentinel v5.4 — Release Verification Report

## Automated regression

Release baseline: **39/39 tests PASS**.

The suite covers original application workflows plus:

- learned AI model training/metrics and zero-publication boundary;
- cross-domain unseen evidence generalisation;
- policy modality, numeric-threshold and temporal-semantics collisions;
- all three seeded conflicts end-to-end;
- post-approval health/readiness regression;
- exact emitted Proof Pack live verification;
- evidence-bound plain-language answers;
- role-aware answer redaction;
- out-of-domain answer refusal;
- frontend anti-hardcoding/static contracts.

## Championship preflight

Release baseline: **20/20 controls PASS — 100%**.

Controls:

1. Authentication
2. Deterministic reset
3. Service health
4. Security headers
5. Runtime secret hygiene
6. Automatic port failover
7. Pitch-aligned JurisTech frontend
8. Readiness proof
9. Hybrid learned AI
10. Track 2 verified answer
11. Digital Twin robustness certificate
12. Governance Gate
13. Adversarial harness
14. Unseen evidence reasoning
15. Explainable blast radius
16. Proof Pack digest
17. Live Proof verification
18. Ledger verification
19. Operational invariants
20. Runtime telemetry

## Adversarial harness

Attack Sentinel baseline: **16/16 HARDENED**.

The harness includes malformed evidence, prompt-like hostile text isolation, ledger tamper detection, RBAC/DLP, canonicalisation poisoning prevention, transaction rollback, redaction, JWT tampering, webhook forgery, safe-state invariants, rollout reconciliation, signed Proof Pack integrity, learned-AI governance boundaries and statistical abstention.

## Post-approval acceptance gate

The previous v5.3 regression where approval degraded assurance is fixed. After publishing JT-084:

- operational invariants = **HEALTHY**;
- readiness = **READY · 100%**;
- assurance overview = **OPERATIONAL**;
- Attack Sentinel = **HARDENED · 100%**.

The same invariant remains healthy after independently publishing the other two seeded policy domains.

## Fresh-process HTTP rehearsal

The release was also exercised through a real Uvicorn process on a fresh SQLite database rather than only through `TestClient`:

- `/finals`, login, passive session discovery and health: **HTTP 200**;
- evidence-bound Track 2 answer: **CONFLICT_PRESENT** with governed citations before approval;
- completely unseen judge evidence: **CONTRADICTION**, quarantined, blast radius **27**;
- all three seeded conflicts: simulation → 100% Governance Gate → approval → propagation → Decision Replay → signed Proof Pack → live proof verification;
- readiness after all three publications: **READY · 100%**;
- Attack Sentinel: **16/16 HARDENED**.

A deliberately later contradictory judge event correctly re-opens the answer state as `CONFLICT_PRESENT` while still binding the answer to the already-published Decision Contract. This is intentional safe-state behavior rather than a regression: newly arrived contradictory evidence cannot be ignored simply because an earlier decision exists.

## Concurrent write / ledger stress

A real HTTP stress run sent **60 live evidence writes with 20-way concurrency**:

- **60/60 HTTP 200**;
- completed in approximately **1.9 seconds** on the release test host;
- ledger after the run: **62 linked entries, chain verified**;
- readiness after the run: **READY · 100%**.

This is a release-host stress observation, not a production throughput/SLA claim.

## Frontend validation

The responsive shell, native scrolling, sheet close paths and graph drag/bounds mechanics inherit the previously browser-validated v5.2 foundation at 1024×768, 1440×900 and 1920×1080. v5.4 changes are guarded by JavaScript syntax validation, frontend static-contract tests and API/E2E tests. Perform one final visual rehearsal on the actual competition laptop after extraction.

# API Contract

All authenticated endpoints use `Authorization: Bearer <JWT>`.

| Method | Endpoint | Purpose |
|---|---|---|
| POST | `/api/auth/login` | Login and issue role token |
| GET | `/api/auth/me` | Current identity |
| GET | `/api/system/health` | DB + ledger health |
| GET | `/api/system/config` | RBAC + security shield configuration |
| GET | `/api/dashboard` | Live Command Center metrics |
| GET | `/api/cases` | Role-aware case list |
| GET | `/api/cases/{case_ref}` | Case + timeline + evidence + conflict |
| GET | `/api/conflicts` | Conflict list |
| GET | `/api/conflicts/{ref}` | Conflict detail + graph |
| GET | `/api/conflicts/{ref}/graph` | Evidence topology |
| POST | `/api/conflicts/detect` | Re-scan active evidence |
| GET | `/api/simulations/conflict/{ref}` | Latest or auto-created simulation |
| POST | `/api/simulations/conflict/{ref}/run` | Run weighted white-box simulation |
| GET | `/api/approvals` | Approval queue |
| POST | `/api/approvals/simulation/{sim_ref}/submit` | Submit selected future |
| POST | `/api/approvals/{ref}/approve` | Publish + propagate governed decision |
| POST | `/api/approvals/{ref}/reject` | Reject proposal |
| POST | `/api/memory/search` | Permission-aware explainable retrieval |
| POST | `/api/memory/answer` | Evidence-bound plain-language governed answer |
| POST | `/api/memory/ingest` | Ingest new governed evidence |
| GET | `/api/memory/sources` | Evidence source list |
| GET | `/api/ledger/decisions` | Decision Contracts |
| GET | `/api/ledger/decisions/{ref}` | Contract + audit trail |
| GET | `/api/ledger/verify` | Recalculate full hash chain |
| GET | `/api/ledger/export.csv` | Export audit ledger as CSV |
| GET | `/api/bodyguard/alerts` | Security incidents |
| POST | `/api/bodyguard/simulate-attack` | Safe demo mutation incident |
| POST | `/api/bodyguard/alerts/{ref}/restore` | Restore approved version |
| GET | `/api/integrations` | Connector state |
| POST | `/api/integrations/{key}/sync` | Execute demo sync |
| POST | `/api/search` | Search cases/conflicts/decisions/evidence |
| GET | `/api/demo/story` | Finals navigation sequence |
| GET | `/api/demo/status` | Cross-module story state |
| POST | `/api/demo/reset` | Deterministic reset |

## v2.0 finals proof endpoints

### POST `/api/live/challenge`
Accepts unseen policy evidence at runtime. Performs local domain/stance analysis, canonical retrieval, contradiction classification, blast-radius analysis, evidence persistence, optional conflict materialisation and audit logging. Injected evidence is non-canonical by default.

### GET `/api/live/challenges?limit=10`
Returns recent judge challenge records and their persisted analysis.

### GET `/api/system/readiness`
Authenticated pre-flight proof across database, ledger, RBAC, shields, integrations, canonical evidence, conflicts, case state and challenge engine.

### GET `/api/ledger/recent?limit=20`
Returns recent hash-ledger entries plus full-chain verification. Used to prove live challenge events even before a decision contract has been published.


## v3.0 Sentinel Arena endpoints

- `POST /api/live/evidence-drop` — deterministic text-file evidence ingress (TXT/MD/CSV/JSON/EML/LOG payload from browser File API).
- `GET /api/live/challenges/{challenge_ref}/impact` — explainable BFS dependency/blast-radius traversal.
- `POST /api/live/red-team` — non-persistent adversarial safety harness.
- `POST /api/live/webhook` — HMAC-SHA256 authenticated real machine-to-machine HTTP evidence ingress with replay protection. Signature material: `event_id + "|" + body`. Header: `X-JurisTwin-Signature`.

The standard `/api/live/challenge` response now includes `analysis.policy_atoms` and `analysis.impact_graph` so the verdict and affected-case count are independently explainable.


## v5.7 Hybrid AI + Track 2 endpoints

- `GET /api/live/ai-model` — measured local model card, tasks, held-out development metrics, abstention and governance boundary.
- `POST /api/memory/answer` — plain-language question → learned policy-domain routing → approved evidence / Decision Contract answer with role-aware citations and conflict warning. Unknown questions safely return `NEEDS_REVIEW`.
- `POST /api/assurance/verify-proof` — verifies the exact emitted Proof Pack `bundle_digest` + HMAC signature. Legacy `digest` is also accepted.

All three seeded conflicts are valid `{ref}` values for graph, simulation, governance, approval, replay and Proof Pack flows.

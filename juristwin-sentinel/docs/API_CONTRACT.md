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
| POST | `/api/memory/search` | Permission-aware semantic retrieval |
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

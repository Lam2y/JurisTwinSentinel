# Architecture

```text
Outlook / Teams / SharePoint / ClickUp / Customer Core / QA
                         │
                         ▼
                Integration Adapters
                         │
                         ▼
              Governed Evidence Store
          SQL metadata + semantic retrieval
                         │
               ┌─────────┴─────────┐
               ▼                   ▼
       Conflict Engine       RBAC / Redaction
               │
               ▼
       Decision Digital Twin
    explicit levers + weighted loss
               │
               ▼
       Human Approval Gateway
               │
        ┌──────┴────────┐
        ▼               ▼
Decision Contract   Propagation Engine
        │               │
        └──────┬────────┘
               ▼
       SHA-256 Decision Ledger
               │
               ▼
          AI Bodyguard
 anomaly → explain → restore → ledger
```

## Why this is finals-safe

- SQLite is default: no external database service is required on stage.
- PostgreSQL is supported via the same SQLAlchemy models for pilot credibility.
- The frontend and zero-build finals UI call the same API state.
- Every mutating finals action is idempotent or resettable.
- `/api/demo/reset` returns the system to the exact starting storyline.

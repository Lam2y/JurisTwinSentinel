# JurisTwin Sentinel — Championship v5.7 Architecture

```text
Enterprise systems / judge input / signed webhook
                       │
                       ▼
               Integration Adapters
                       │
                       ▼
              Governed Evidence Store
                       │
            ┌──────────┴──────────┐
            ▼                     ▼
     Role-aware Memory        RBAC / DLP
            │
            ├──── plain-language question
            │              ↓
            │       Learned NLP router
            │              ↓
            │       Evidence-bound answer
            │
            ▼
     Learned Policy AI
 domain + stance probabilities
            │
            ▼
    Policy Atom Reasoner
 modality / numeric / temporal collision
            │
            ▼
 Authority-Weighted Hybrid Consensus
            │
            ▼
     Conflict Intelligence
            │
            ▼
 Explainable Blast-Radius Graph
 BFS over live case dependencies
            │
            ▼
      Decision Digital Twin
 Monte Carlo + sensitivity + Pareto
            │
            ▼
       Governance Gate
            │
        ┌───┴─────────────┐
        ▼                 ▼
 Human approval     Progressive rollout
        │                 │
        └────────┬────────┘
                 ▼
        Decision Contract
                 │
                 ▼
       SHA-256 Decision Ledger
                 │
         ┌───────┴────────┐
         ▼                ▼
   AI Bodyguard      Decision Replay
         │                │
         └───────┬────────┘
                 ▼
       HMAC-signed Proof Pack
```

## Hybrid AI safety model

JurisTwin does not let a learned model decide organisational truth. The learned classifier provides generalisation to unseen wording; the symbolic reasoner and authority rules provide inspectability; uncertainty/disagreement can abstain; only the Governance Gate plus an authorised human can publish.

## Frontend

The finals UI is a responsive, zero-build SPA served by FastAPI. It requires no Node runtime or internet on the presentation laptop.

Judge-facing destinations remain intentionally limited to:

1. Overview
2. Conflict Map
3. Digital Twin
4. Assurance
5. Evidence Lab

Deeper capabilities live behind Platform / Final Flow panels so technical depth does not become visual clutter.

## Finals-safe engineering

- SQLite offline default; PostgreSQL support through the same SQLAlchemy models.
- Local ML retraining from a bundled corpus; no external AI dependency.
- First-time setup generates random local cryptographic secrets.
- Mutating demo actions are resettable/idempotent.
- All three seeded conflicts are independently executable end-to-end.
- `/api/demo/reset` returns a deterministic starting state.
- Graph coordinates live in SVG viewBox space and remain bounded.
- Native View Transitions are progressive enhancement only; reduced-motion is supported.

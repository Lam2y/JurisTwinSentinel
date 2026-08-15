# JurisTwin Sentinel — Championship v5 Architecture

```text
External evidence / signed webhook / judge file
                     │
                     ▼
             Integration Adapters
                     │
                     ▼
            Governed Evidence Store
                     │
          ┌──────────┴──────────┐
          ▼                     ▼
  Policy Atom Reasoner      RBAC / DLP
          │
          ▼
   Conflict Intelligence
 authority + modality collision
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
      ┌───┴───────────┐
      ▼               ▼
Decision Contract   Progressive Rollout
      │               │
      └───────┬───────┘
              ▼
      SHA-256 Decision Ledger
              │
              ▼
       Assurance / Bodyguard
```

## Finals frontend

Championship v5 ships a responsive, zero-build single-page application served by FastAPI. The runtime does not require Node.js, npm, a CDN, external fonts, or internet access.

The judge-facing information architecture is intentionally limited to five destinations:

1. **Overview** — problem, exposure and the next action.
2. **Conflict Map** — one bounded, draggable dependency graph with contextual inspection.
3. **Digital Twin** — decision alternatives and robustness, without forcing judges through raw simulation detail.
4. **Assurance** — governance readiness, proof and adversarial controls.
5. **Evidence** — live judge challenge / file drop and immediate reasoning result.

Deeper technical detail is progressively disclosed through a single reusable side sheet rather than permanent dashboard panels.

## Why this is finals-safe

- SQLite is the offline default; PostgreSQL remains supported through the same SQLAlchemy models.
- The finals SPA and API operate on the same persisted state.
- No frontend build tool is needed on the presentation laptop.
- Mutating demo actions are resettable or idempotent.
- `/api/demo/reset` returns the system to a deterministic starting state.
- Native View Transitions are used when supported, with a CSS fallback and reduced-motion support.
- Graph coordinates are maintained in SVG viewBox space and clamped to node dimensions, so nodes cannot be dragged outside the visible workspace.

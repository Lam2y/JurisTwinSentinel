# JurisTwin Sentinel — Grand Finals Working System

JurisTwin Sentinel is a **white-box decision digital twin protected by an AI Bodyguard**. This repository converts the finalist prototype into an actual stateful system: evidence is ingested, permission-filtered, compared for conflicts, simulated through explicit white-box levers, routed for human approval, published as a governed Decision Contract, propagated to affected cases, written to an append-only SHA-256 ledger, and protected by a restorable security workflow.

## Fastest finals launch — Windows

1. Double-click `setup_windows.bat` once.
2. Double-click `run_finals.bat`.
3. Open `http://127.0.0.1:8000/finals`.

Demo credentials:

- Email: `operations@regulatedbank.com`
- Password: `Finals2026!`

`/finals` is intentionally served directly by FastAPI and has **no Node/npm dependency at presentation time**. It calls the exact same live APIs as the optional React frontend.

## What is genuinely functional

- JWT authentication and role-aware access: manager, officer, intern, compliance manager, product owner.
- 128 SQL-backed active cases; 27 are initially linked to the flagship income-document conflict.
- Secure Enterprise Memory with deterministic semantic retrieval, permission gating and intern redaction.
- Conflict graph linking approved, informal, outdated, operational and customer evidence.
- White-box future simulation with visible intervention levers and adjustable weights.
- Human approval workflow that **changes the whole system state**: conflict resolved, legacy evidence superseded, new decision evidence published, affected cases re-evaluated, dashboard metrics updated.
- Decision Contract JT-084 and append-only SHA-256 ledger with chain verification.
- AI Bodyguard demo incident, explainable reasons, restore action and ledger proof.
- Integration sync endpoints for Outlook, Teams, SharePoint, OneDrive, ClickUp, Customer Core, QA, PostgreSQL and vector memory.
- Guided demo storyline + deterministic reset.
- Swagger docs at `http://127.0.0.1:8000/docs`.

## Manual launch

```bash
cd backend
python -m venv .venv
# Windows: .venv\Scripts\activate
# macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
python run.py
```

## Full end-to-end test

```bash
cd backend
pytest -q
```

The test logs in, resets the database, opens the case, checks the graph, runs the simulator, submits and approves Option C, validates propagated dashboard changes, verifies the cryptographic ledger, triggers the Bodyguard incident, restores the approved version and verifies the ledger again.

## PostgreSQL mode

By default the finals build uses SQLite because it is the safest stage-demo dependency. To use PostgreSQL:

```env
DATABASE_URL=postgresql+psycopg2://postgres:postgres@localhost:5432/juristwin
```

Or run `docker compose up --build`.

## Judge-facing honesty

The workflow and persistence are real. The simulator is intentionally **white-box and calibrated** to the finalist scenario (4.2d/64%, 2.7d/39%, 1.1d/17%) rather than pretending a production ML model is already validated. A pilot would retrain/calibrate those coefficients using real enterprise history. That distinction makes the demo technically credible rather than overclaiming.

## Verification

See `docs/TEST_REPORT.md` for the automated end-to-end and RBAC verification report, and `docs/GRAND_FINALS_CHECKLIST.md` for stage preparation and technical Q&A positioning.

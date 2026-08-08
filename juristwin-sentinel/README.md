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


## v1.3 — Complete Prototype-Matched Grand Finals Front-end

The `/finals` interface now renders the original ten 1440×1024 JurisTwin prototype screens directly from `reference/Prototype-reference.txt` converted into browser-ready HTML. The supplied screenshot layouts are represented as real DOM screens rather than image backgrounds. Navigation and key buttons are wired to the existing FastAPI APIs.

Screens: Login, Command Center, Case Workspace, Conflict Intelligence, Decision Digital Twin, **Approve Recommended Resolution**, Decision Ledger, **AI Bodyguard Security Center**, Secure Enterprise Memory, and Integrations & Administration.

v1.3 explicitly includes the two finalist workflow screens supplied as visual references. The Bodyguard incident metadata layout was corrected so Triggering User, Role / Authority, Document, Time of Incident, Conflict Decision, and Impact render as a clean 3×2 evidence grid instead of overlapping. Approval confirmation and Bodyguard restore confirmation are now driven by backend state.

For stage use, run `run_finals.bat` and open `http://127.0.0.1:8000/finals`. The optional Vite frontend uses the same exact static UI and proxies `/api` and `/static` to FastAPI.

## v1.4 Grand Finals visibility controls

The live prototype now includes a projector-friendly readability and motion layer.

- **C** — toggle high-contrast projector mode.
- **F** — toggle focus mode (uses more width on 16:9 displays; slight vertical scroll may be needed).
- **M** — pause/resume interface motion.
- **Ctrl + Shift + R** — reset the deterministic finals dataset.

These controls are also available from the small floating buttons on the right edge of `/finals`.

Motion includes KPI count-ups, page/card entrance transitions, primary-action feedback, evidence-network animation, Digital Twin metric bars, approval-step reveals, and Bodyguard incident-sequence animation. `prefers-reduced-motion` is respected.

## v1.5 Finals Interaction Build

The finals UI now includes draggable evidence graph nodes with live SVG connectors, interactive KPI/evidence/version/security cards, Digital Twin option selection, clickable Memory filters and role previews, live health/ledger inspectors, and interactive administration controls. See `docs/INTERACTION_GUIDE.md`.

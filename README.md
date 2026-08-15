# JurisTwin Sentinel — JurisTech Pitch-Aligned Edition v5.3

JurisTwin Sentinel is a decision-integrity control plane for enterprises. It detects when authoritative evidence contradicts operational guidance, traces the affected customers and systems, stress-tests the response, requires governed approval, propagates the decision, and preserves a replayable cryptographic proof.

## Launch on Windows

1. Run `setup_windows.bat` once.
2. Run `run_finals.bat`.
3. Open `http://127.0.0.1:8000/finals`.

Demo login:

- Email: `operations@regulatedbank.com`
- Password: `Finals2026!`

The finals UI is served by FastAPI and needs **no Node/npm runtime**.

## The five screens judges need

1. **Overview** — one conflict, current exposure, decision-integrity score.
2. **Conflict Map** — draggable evidence network with bounded nodes and live relationships.
3. **Digital Twin** — 1,500 scenario stress test, sensitivity and robustness certificate.
4. **Assurance** — readiness, governance gate, proof pack and adversarial self-test.
5. **Evidence Lab** — type or drop unseen policy evidence and let JurisTwin reason over it live.

Use **Final Flow** for the exact pitch-deck operating loop: **Connect → Expose → Simulate → Recommend → Approve → Protect**. Use **Challenge Sentinel** for the strongest unscripted proof. Use **Platform** when a judge asks to inspect the full pitch-deck feature set or the v4 assurance controls.

Keyboard shortcuts:

- `Alt + J` Judge input
- `Alt + C` Conflict map
- `Alt + T` Digital twin
- `Alt + A` Assurance
- `Alt + P` Presentation Mode for projectors
- `Alt + F` Final Flow
- `Esc` closes every side sheet

## Functional architecture

```text
Unseen / enterprise evidence
        ↓
Provenance + policy atoms
        ↓
Authority-aware contradiction reasoning
        ↓
Dependency graph + BFS blast radius
        ↓
Decision Digital Twin
        ↓
Governance Gate
        ↓
Human approval + controlled propagation
        ↓
SHA-256 ledger + signed assurance proof
        ↓
Decision replay + adversarial protection
```

### Implemented technical controls

- FastAPI + SQLAlchemy with SQLite finals mode and PostgreSQL support.
- JWT authentication, RBAC, DLP/redaction and security shields.
- Stateful enterprise evidence and customer-case data.
- Explainable Policy Atom Reasoner.
- Draggable SVG conflict network; every node is clamped to the visible canvas.
- BFS dependency/blast-radius traversal.
- 1,500-scenario deterministic Monte Carlo Digital Twin with sensitivity analysis.
- Enforced pre-publication Governance Gate.
- Progressive rollout planning and safe-state invariants.
- Append-only SHA-256 decision ledger.
- HMAC-SHA256 signed Decision Assurance Proof Pack.
- HMAC-authenticated real HTTP webhook with replay protection.
- Runtime request tracing, latency/error telemetry, rate containment and security headers.
- Adversarial self-test harness.
- Docker/Compose, CI and release-manifest support.

## Frontend design

v5.3 uses a JurisTech-inspired brand direction: generous white space, large black typography and Juris red for primary actions/authority. Dark analytical canvases are reserved for the conflict network and decision proof moments. The responsive zero-build SPA uses native View Transitions when supported, native document scrolling, a reusable side-sheet interaction model, a single non-stacking status capsule, and progressive disclosure.

The **Platform** drawer explicitly preserves every pitch-deck feature while also surfacing the v4 championship controls: Secure Enterprise Memory, Living Decision Digital Twin, White-Box Future Simulator, AI Bodyguard, Decision Ledger, Policy Reasoner, Enterprise Connectors, Progressive Rollout, Decision Replay, Decision Assurance, the exact Operating Model, product positioning and Pilot & Scale. Presentation Mode (`Alt + P`) provides an additional projector-readability boost.

Source mirror: `frontend/src/`

Deployable files: `backend/app/static/finals.html`, `sentinel.css`, `sentinel.js`

## Verification

```bash
cd backend
pytest -q
python scripts/industry_preflight.py
```

The release is expected to pass all automated backend tests and the complete industry preflight before presentation.

## Real machine-to-machine ingress

With JurisTwin already running, open a second terminal from the project root:

```bash
backend\.venv\Scripts\python.exe backend\scripts\send_live_webhook.py
```

The event is sent through an actual HTTP POST, authenticated with HMAC-SHA256 and replay-protected.

## Claims boundary

This is an **enterprise-grade proof of concept**, not production banking software. Outlook/Teams/SharePoint adapters use deterministic finals data unless a real enterprise tenant is connected. The Policy Atom Reasoner and Digital Twin are intentionally white-box and explainable rather than pretending an unvalidated black-box model is production-ready.

Read next:

- `FINAL_README_FIRST.txt`
- `docs/DEMO_FLOW_v53.md`
- `docs/PITCH_DECK_FEATURE_COVERAGE.md`
- `docs/UI_UX_v5_3.md`
- `docs/CLAIMS_BOUNDARY.md`
- `docs/THREAT_MODEL.md`

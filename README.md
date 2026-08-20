# JurisTwin Sentinel — Manager-Friendly Decision Assurance Platform v6.1


> **v6.1 Executive UX build:** keeps every v6.0 lecturer requirement and backend control, but removes dashboard overload. Main pages now use shorter copy, fewer visible proof items, concise status cards, shorter labels, and progressive disclosure for technical detail. Security remains obvious through simple states such as **DMs BLOCKED**, **Client AI Training OFF**, **Live Refresh ON**, and role-based export verdicts.

> **v6.0 Lecturer-Complete build:** maps every lecturer recommendation to a working, manager-visible control. It adds the in-system **Management Controls** comparison page, functional approved Teams-group / official-sender / SharePoint-library scope enforcement, answer-first source lineage, authority-first + same-tier-majority conflict resolution, explicit privacy/export/transfer/audit controls, live freshness, and stale-demo-data self-healing for the Governance Gate. See `docs/LECTURER_REQUIREMENTS_V60.md`.

> **v5.9 Manager-First UX build:** keeps all v5.8 privacy, source-governance, export and audit controls, but presents them in plain business language with a persistent security trust strip, simpler navigation, obvious role-based data protections and technical detail moved behind optional panels. See `docs/MANAGER_UX_V59.md`.

> **v5.8 Lecturer Recommendations build:** adds governed source selection, privacy-aware retrieval scope, authority-first/majority-fallback resolution, customer export RBAC, transfer-security controls, actor-level audit logging, and real-time source freshness. See `docs/LECTURER_FEEDBACK_V58.md`.

JurisTwin Sentinel is a **hybrid-AI decision-integrity control plane** for regulated enterprises. It connects fragmented evidence, gives permission-safe plain-language answers, detects contradictory policy, traces downstream exposure, stress-tests response options, enforces human governance, propagates approved decisions and preserves replayable cryptographic proof.

v6.0 is the lecturer-complete finals build designed around the exact operating story:

> **CONNECT → EXPOSE → SIMULATE → RECOMMEND → APPROVE → PROTECT**

## Windows launch

1. Run `setup_windows.bat` once.
2. Run `run_finals.bat`.
3. Open the Finals URL printed by `run_finals.bat` (normally `http://127.0.0.1:8000/finals`; JurisTwin automatically fails over to the next free local port if 8000 is busy).

Demo login:

- **Email:** `operations@regulatedbank.com`
- **Password:** `Finals2026!`

`setup_windows.bat` now generates a local `.env` containing independent cryptographically random JWT, webhook, Proof Pack and optional PostgreSQL secrets. The `.env` file is ignored from release provenance and should never be committed.

The finals UI is served directly by FastAPI and requires **no Node/npm runtime or internet connection**.

## Manager-first destinations

1. **Ask JurisTwin** — one governed answer first, with its main official source, supporting lineage, privacy exclusions and freshness.
2. **Management Controls** — live Original → Now mapping of all lecturer-requested capabilities and links to test each control.
3. **Why Sources Disagree** — manager-readable conflict explanation with the evidence graph available as optional proof.
4. **Compare Solutions** — business-first A/B/C decision comparison backed by the Digital Twin.
5. **Safe to Publish?** — enforced Governance Gate, readiness, replay and Audit Proof.
6. **Test New Evidence** — live unseen-evidence challenge that cannot silently overwrite governed policy.
7. **Privacy & Security** — source scope, export rights, protected transfer, freshness and who-did-what audit.

Use **Final Flow** for the six-stage pitch story. Use **Platform** to expose the full technical stack without cluttering the main demonstration.

## Inherited finals hardening + v6.0 manager controls


### Adversarial finals hardening

- Attack Sentinel JWT tamper testing now mutates an interior base64url signature character, eliminating a machine-secret-dependent false failure discovered on Windows.
- `industry_preflight.py` reconfigures stdout/stderr to UTF-8 itself, so a default cp1252 console cannot crash on status glyphs.
- `run_finals.bat` now delegates to a heartbeat launcher that prints visible startup progress while scikit-learn warms, waits for the real health endpoint, opens the browser only when healthy, and fails over from an occupied port automatically.
- `setup_windows.bat` uses the virtual-environment Python explicitly, repairs incomplete venvs, supports standard CPython 3.10–3.14 while preferring 3.12/3.11, warms the local AI stack, and runs a compact preflight before declaring setup complete.
- Vendor fixture connectors no longer increment fake object counts. The **Signed Webhook Gateway** is surfaced as the genuine HMAC-authenticated live HTTP ingress, and its accepted-event count is driven only by real signed requests.
- The Track-2 answer now exposes a one-click **How AI verified this** proof with held-out Macro-F1, deterministic verifier, offline status and **model publication authority = 0**.

### Judge Clarity Layer
Every conflict now names and quotes the exact governed sources that disagree, explains why they conflict, why the canonical source wins and the customer consequence. Digital Twin recommendations explain Why not A / Why not B / Why C in plain English before exposing Monte Carlo, sensitivity and Pareto proof. Judge Challenge uses the same evidence-first explanation pattern.


### Genuine learned AI, without giving a model decision authority

A bundled labelled development corpus trains two local statistical NLP classifiers on startup:

- policy-domain classification;
- policy-stance classification.

Architecture: **word + character TF-IDF → Logistic Regression**.

Measured deterministic held-out development benchmark:

- Domain macro-F1: **0.9035**
- Stance macro-F1: **0.9666**

The learned model only proposes intent. A white-box Policy Atom Reasoner, authority controls and abstention logic verify the proposal. The model has **zero publication authority**.

### Evidence-bound plain-language answers

Secure Enterprise Memory now answers normal questions such as:

> *Can gig workers use bank statements as income evidence?*

The learned layer routes the question, but answer text is bound to approved evidence or an active Decision Contract. An open contradiction is surfaced instead of hidden; lower-authority roles receive redaction; unknown questions return **NEEDS_REVIEW** instead of invented policy.

### Every seeded conflict is now fully drivable

All three policy domains support the complete governed workflow:

- `CF-INCOME-001` → `JT-084`
- `CF-RESTRUCTURE-002` → `JT-RESTRUCTURE-002`
- `CF-NOTIFY-003` → `JT-NOTIFY-003`

Each has its own evidence graph, Digital Twin scenario, governance gate, approval, propagation, replay and signed Proof Pack.

### Assessment blockers removed

- Post-approval readiness remains **READY · 100%**.
- Overview no longer mixes fields from different conflicts.
- Proof Pack now has a live **Verify this proof** control and API verification path.
- Flagship-only hardcoding is removed from the core workflow.
- Hybrid learned AI closes the previous regex-only technical-depth ceiling.

## Functional architecture

```text
Enterprise / judge evidence
        ↓
Provenance + permission controls
        ↓
Learned NLP proposal
        ↓
Symbolic Policy Atom verification
        ↓
Authority-Weighted Hybrid Consensus
        ↓
Conflict Intelligence / abstention
        ↓
Dependency graph + BFS blast radius
        ↓
Decision Digital Twin
Monte Carlo + sensitivity + Pareto
        ↓
Enforced Governance Gate
        ↓
Human approval + controlled propagation
        ↓
Progressive rollout
        ↓
SHA-256 Decision Ledger
        ↓
HMAC-signed Assurance Proof Pack
        ↓
Decision Replay + AI Bodyguard
```

## Implemented technical controls

- FastAPI + SQLAlchemy with SQLite finals mode and PostgreSQL support.
- Local learned NLP pipeline with measured development metrics and safe abstention.
- Evidence-bound, role-aware plain-language answers.
- Permission-aware hybrid Enterprise Memory retrieval.
- Policy Atom extraction and explicit modality/numeric/temporal collision rules.
- Authority-Weighted Hybrid Consensus for explainable multi-signal arbitration.
- BFS dependency/blast-radius traversal.
- 1,500-scenario deterministic Monte Carlo Twin with uncertainty, sensitivity and Pareto analysis.
- Enforced pre-publication Governance Gate.
- Progressive CANARY → CONTROLLED → FULL rollout planning.
- JWT authentication, RBAC, DLP/redaction and security shields.
- Append-only SHA-256 ledger.
- Proof-carrying Decision Assurance packs that cryptographically bind evidence, learned-model boundary, reasoning, impact, simulation, governance and ledger state; live HMAC verification included.
- HMAC-authenticated real HTTP webhook with replay protection.
- Decision Replay / time machine.
- AI Bodyguard incident containment and version restoration.
- Operational safe-state invariants.
- Request IDs, latency/error telemetry, rate containment and security headers.
- Adversarial self-test harness.
- Docker/Compose, CI and release-manifest verification.

## Finals verification

```bat
backend\.venv\Scripts\python.exe -X utf8 -m pytest -q
backend\.venv\Scripts\python.exe -X utf8 backend\scripts\industry_preflight.py
```

On Windows, the easiest option is simply `run_preflight.bat`. Never depend on a bare `python` PATH alias during finals.

Expected v6.0 release baseline:

- **57/57 automated tests**
- **32/32 championship preflight controls**
- **16/16 adversarial controls**
- post-approval readiness **READY · 100%**
- fresh-process stress: **60/60 concurrent live evidence writes succeeded**, ledger chain verified, readiness remained **100%**

## Real machine-to-machine ingress

With JurisTwin already running, open a second terminal from the project root:

```bat
backend\.venv\Scripts\python.exe backend\scripts\send_live_webhook.py
```

The script loads the locally generated `.env`, sends a real HTTP POST, signs it with HMAC-SHA256 and exercises replay protection.

## Claims boundary

JurisTwin v5.7 is an **enterprise-grade proof of concept**, not regulator-certified production banking software.

- Vendor-branded connector counts use deterministic finals adapters unless a real tenant is connected.
- The machine-to-machine webhook is a genuine live HTTP integration contract.
- The learned classifier is real and measured, but its metrics are a development benchmark, not production validation.
- Digital Twin coefficients are transparent prototype-calibrated assumptions, stress-tested rather than falsely presented as learned production forecasts.
- No learned model may publish or canonicalise policy; human governance remains mandatory.

Read next:

- `FINAL_README_FIRST.txt`
- `docs/DEMO_FLOW_v54.md`
- `docs/JUDGING_GAP_CLOSURE_v54.md`
- `docs/AI_MODEL_CARD.md`
- `docs/PITCH_DECK_FEATURE_COVERAGE.md`
- `docs/CLAIMS_BOUNDARY.md`
- `docs/THREAT_MODEL.md`

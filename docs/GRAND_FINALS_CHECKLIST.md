# Grand Finals Technical Checklist — Championship v5.7

## Before leaving for the venue

- Run `setup_windows.bat` while internet is available.
- Confirm a local `.env` was generated; do not share it.
- Run `backend\.venv\Scripts\python.exe -m pytest -q` → **57/57 PASS**.
- Run `backend\.venv\Scripts\python.exe backend\scripts\industry_preflight.py` → **32/32 PASS · 100%**.
- Launch `run_finals.bat` and perform one complete flagship demo. Confirm the browser uses the port printed by the launcher; port 8000 automatically fails over if occupied.
- Approve JT-084 and confirm **Readiness stays READY · 100%**.
- Open Proof Pack and click **Verify this proof**.
- Reset the scenario before judging.
- Keep ZIP + extracted folder locally and a second offline copy.
- Disable sleep, notification popups and Windows auto-update during judging.
- Use Chrome/Edge at 100% zoom; turn on Presentation Mode (`Alt+P`) if needed.

## On stage

1. **Ask JurisTwin:** ask the prepared plain-language question immediately, show multi-source conflict/citations, switch to Intern once for redaction.
2. **Evidence Lab:** let a judge give unseen policy text/file.
3. **Conflict Map:** show the collision, drag one node, explain the 27-case BFS blast radius.
4. **Digital Twin:** A/B/C, then show 1,500-scenario robustness — do not narrate every metric.
5. **Governance Gate:** 100% PASS → approve JT-084.
6. **AI Bodyguard:** simulate QA-014 modification → restore.
7. **Proof:** Proof Pack → Verify this proof.

## Technical Q&A anchors

**“Where is the AI?”**  
JurisTwin trains a local two-task statistical NLP model on startup. Show the AI Model Card and held-out macro-F1. The model proposes intent; symbolic policy atoms and authority controls verify; it cannot publish policy.

**“Can the AI hallucinate?”**  
Ask an unrelated policy question. The answer layer returns `NEEDS_REVIEW` and zero citations rather than inventing policy.

**“Is the flagship hardcoded?”**  
Switch to the restructuring or notification conflict and run its distinct Twin/gate/decision/proof workflow.

**“Is the simulator trained ML?”**  
No. The Twin is intentionally white-box and prototype-calibrated. It is stress-tested across 1,500 Monte Carlo scenarios, sensitivity and Pareto analysis. Learned production coefficients require enterprise history and formal validation.

**“Is the ledger blockchain?”**  
No. It is an append-only SHA-256 linked ledger, which gives the required tamper evidence without unnecessary consensus infrastructure.

**“Are Microsoft integrations live?”**  
Vendor-branded finals adapters are deterministic unless tenant credentials are supplied. The signed webhook is a real live machine-to-machine HTTP path and can be demonstrated from a second process.

**“Why is this Track 2 rather than a chatbot?”**  
Secure Enterprise Memory now provides plain-language, role-aware, cited answers — but JurisTwin's differentiator is making those answers trustworthy when enterprise sources conflict.

# Grand Finals Technical Checklist — Championship v5

## Before leaving for the venue

- Run `setup_windows.bat` while internet is available.
- Run `backend\.venv\Scripts\python.exe -m pytest -q` and confirm **23/23** tests pass.
- Run `backend\.venv\Scripts\python.exe backend\scripts\industry_preflight.py` and confirm **15/15** controls pass.
- Launch `run_finals.bat`, perform one complete demo, then reset the system.
- Keep both the ZIP and extracted folder locally; keep a second copy on USB/cloud.
- Disable sleep, notification popups and Windows auto-update during judging.
- Use Chrome/Edge at 100% zoom unless the venue projector requires otherwise.

## On stage

1. Launch `run_finals.bat` and open `http://127.0.0.1:8000/finals`.
2. Login and confirm the compact LIVE status is healthy.
3. **Overview:** establish the contradiction and the 27 exposed customers in seconds.
4. **Evidence:** ask a judge for unseen policy text/file and submit it.
5. **Conflict Map:** show the explicit policy collision and drag a node to prove the graph is live; open the affected-case path only if asked.
6. **Digital Twin:** show the three decision options and robustness certificate; avoid narrating every metric.
7. **Assurance:** show the governance gate and, for technical judges, run Attack Sentinel or the signed Proof Pack.
8. Reset only if a second judging group needs the exact initial story.

## Presentation discipline

- Do not read paragraphs from the interface; the interface is designed around headline → evidence → action.
- Use one screen for one claim.
- Open side-sheet detail only in response to judge curiosity or technical Q&A.
- Avoid showing Swagger unless a technical judge specifically asks to inspect APIs.
- Do not claim the deterministic finals connector adapters are live Microsoft tenant integrations.

## Technical Q&A anchors

**“Is the simulator really AI/ML?”**  
The finals Twin is an explainable white-box decision model. It is stress-tested across 1,500 Monte Carlo scenarios, sensitivity checks and Pareto analysis. Production coefficients would be calibrated and validated on enterprise history; the hackathon build deliberately avoids presenting unvalidated ML as fact.

**“Is the ledger blockchain?”**  
No. It is an append-only SHA-256 linked ledger, which provides the tamper evidence this control problem needs without unnecessary blockchain infrastructure.

**“Are Outlook/Teams actually connected?”**  
The ingestion contract and signed machine-to-machine webhook are real. Vendor-branded adapters use deterministic finals data unless a real tenant and credentials are supplied; we do not embed regulated credentials in a public demo.

**“What makes this different from RAG?”**  
RAG retrieves information. JurisTwin reasons about conflicting authority, calculates downstream exposure, stress-tests decisions, requires governed approval, propagates the resulting decision and preserves replayable proof.

**“How is access control enforced?”**  
At the API/service layer. Tests verify that restricted evidence is redacted for users without the required capability.

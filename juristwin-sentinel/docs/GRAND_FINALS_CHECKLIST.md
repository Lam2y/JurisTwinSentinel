# Grand Finals Technical Checklist

## Before leaving for the venue

- Run `setup_windows.bat` once while internet is available.
- Run `backend\pytest -q` and confirm all tests pass.
- Launch `run_finals.bat` and complete the full guided flow once.
- Click Reset before closing the laptop so the next launch starts clean.
- Keep the ZIP and extracted folder in two locations (local drive + USB/cloud).
- Disable Windows sleep/auto-update during the judging window.

## On stage

1. Launch `run_finals.bat`.
2. Use `http://127.0.0.1:8000/finals` as the primary demo.
3. Keep `http://127.0.0.1:8000/docs` open in another tab for technical Q&A.
4. Use the built-in **Start Guided Demo** flow.
5. If anything gets into the wrong state, use **Reset**. The reset is deterministic.

## Technical Q&A answers to be ready for

**“Is the simulator really AI/ML?”**  
The current finals build is a transparent white-box decision model calibrated to the scenario. The workflow, persistence, governance and propagation are real. Production coefficients would be trained and validated on enterprise history during a pilot. We chose explainability over pretending an unvalidated model was production-ready.

**“Is the ledger blockchain?”**  
No. It is an append-only SHA-256 hash chain. That is enough to demonstrate tamper evidence without adding unnecessary blockchain infrastructure. A production deployment could anchor hashes externally if required.

**“Are the connectors actually connected to Outlook/Teams?”**  
The integration layer, state, sync APIs and ingestion contract are functional. The finals environment uses deterministic connector adapters because real client credentials and regulated customer data should not be embedded in a public hackathon demo.

**“What makes this different from RAG?”**  
RAG retrieves evidence. JurisTwin additionally detects contradictions, models authority/version state, simulates downstream consequences, requires human approval, propagates the governed decision and protects it afterwards with a verifiable ledger and Bodyguard workflow.

**“How is access control enforced?”**  
At the API/service layer, not just the UI. The automated test logs in as an intern and verifies restricted evidence is returned redacted.

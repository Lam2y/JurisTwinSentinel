# JurisTwin Sentinel v5.7 — Adversarial MaxScore Hardening

This release closes the remaining demo-machine and credibility risks identified by the independent Windows re-evaluation.

## Closed risks

1. **JWT red-team portability** — the tamper probe now mutates an interior base64url signature character; regression-tested across 64 generated secrets.
2. **Windows cp1252 preflight crash** — the preflight script forces UTF-8 output internally and is regression-tested under `PYTHONIOENCODING=cp1252`.
3. **Cold-start false-crash perception** — `finals_launcher.py` prints startup heartbeats, waits for real health, then opens the browser.
4. **Python/venv drift** — setup uses the venv interpreter explicitly, repairs incomplete environments, supports standard CPython 3.10–3.14 and pre-warms local AI.
5. **Fake connector-sync trap** — deterministic vendor fixtures never mutate counts. The Signed Webhook Gateway is the visible real HTTP ingress.
6. **Technical-depth visibility** — Track-2 answers expose measured AI verification one click deep: domain/stance Macro-F1, symbolic verifier, offline execution and publication authority = 0.

## Release gate

- 55/55 automated tests
- 32/32 championship preflight controls
- 16/16 Attack Sentinel controls
- fresh Uvicorn HTTP smoke: READY 100 after approval
- real signed webhook accepted and tracked
- 60/60 concurrent evidence writes at 20-way concurrency; ledger verified; readiness remained 100

## Finals claim discipline

- Vendor connector object counts are finals fixtures, not live Microsoft/Google tenants.
- The signed webhook is the genuine live machine-to-machine ingress contract.
- Retrieval is explainable BM25 + cosine locally; ChromaDB is a pilot target.
- The Digital Twin is white-box and prototype-calibrated; Monte Carlo/sensitivity/Pareto stress assumptions rather than pretending to be a learned forecast.
- Learned TF-IDF + Logistic Regression models route policy domain/stance; symbolic reasoning and humans govern publication.

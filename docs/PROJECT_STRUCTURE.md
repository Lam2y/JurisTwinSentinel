# Project Structure — Championship v5.7

```text
JurisTwinSentinel-Championship-v5.7-Track2-MaxScore/
├── backend/
│   ├── app/
│   │   ├── core/                 # config + JWT/RBAC + secure env loading
│   │   ├── data/                 # labelled policy ML development corpus
│   │   ├── db/                   # SQLAlchemy models, seed, database setup
│   │   ├── routers/              # REST endpoints
│   │   ├── services/             # learned AI, reasoner, twin, impact, ledger, assurance
│   │   └── static/               # deployed zero-build finals SPA
│   ├── scripts/                  # preflight, webhook, browser opener, verifiers
│   ├── tests/                    # 38-test regression suite
│   ├── requirements.txt
│   └── run.py
├── frontend/
│   └── src/                      # readable source mirror of deployed SPA
├── demo_inputs/
├── docs/
│   ├── DEMO_FLOW_v54.md
│   ├── JUDGING_GAP_CLOSURE_v54.md
│   ├── AI_MODEL_CARD.md
│   ├── ARCHITECTURE.md
│   ├── API_CONTRACT.md
│   ├── CLAIMS_BOUNDARY.md
│   ├── PITCH_DECK_FEATURE_COVERAGE.md
│   ├── THREAT_MODEL.md
│   └── TEST_REPORT.md
├── tools/
│   ├── bootstrap_env.py          # generates local random signing/auth secrets
│   ├── generate_release_manifest.py
│   └── verify_release_manifest.py
├── .env.example
├── .gitignore
├── setup_windows.bat
├── run_finals.bat
├── docker-compose.yml
├── Makefile
└── FINAL_README_FIRST.txt
```

The finals frontend intentionally has no npm dependency at presentation time. FastAPI serves the UI and APIs on one origin, reducing setup, CORS, CDN and build failure risk.

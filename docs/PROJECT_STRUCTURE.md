# Project Structure — Championship v5

```text
JurisTwinSentinel-Championship-v5.0/
├── backend/
│   ├── app/
│   │   ├── core/                 # config + JWT/RBAC security
│   │   ├── db/                   # SQLAlchemy models, seed and database setup
│   │   ├── routers/              # REST endpoints
│   │   ├── services/             # reasoner, twin, impact graph, ledger, assurance
│   │   └── static/
│   │       ├── finals.html       # finals SPA shell
│   │       ├── sentinel.css      # responsive championship design system
│   │       ├── sentinel.js       # live SPA + interactions
│   │       └── favicon.svg
│   ├── scripts/                  # preflight, webhook, smoke, proof verification
│   ├── tests/                    # automated regression + UI contract tests
│   ├── requirements.txt
│   └── run.py
├── frontend/
│   └── src/                      # readable mirror of deployed finals frontend
├── demo_inputs/                  # unseen-input examples
├── docs/
│   ├── DEMO_FLOW_v5.md
│   ├── UI_UX_v5.md
│   ├── ARCHITECTURE.md
│   ├── API_CONTRACT.md
│   ├── CLAIMS_BOUNDARY.md
│   ├── THREAT_MODEL.md
│   └── TEST_REPORT.md
├── tools/                        # release manifest generation/verification
├── setup_windows.bat
├── run_finals.bat
├── docker-compose.yml
├── Makefile
└── FINAL_README_FIRST.txt
```

The finals frontend intentionally has no npm dependency at presentation time. FastAPI serves the complete application on one origin, which reduces setup, CORS and build failure risk on the presentation laptop.

# Project Structure

```text
juristwin-sentinel-finals/
├── README.md
├── docker-compose.yml
├── setup_windows.bat
├── run_finals.bat
├── run_finals.sh
├── backend/
│   ├── app/
│   │   ├── main.py
│   │   ├── schemas.py
│   │   ├── core/
│   │   │   ├── config.py
│   │   │   └── security.py
│   │   ├── db/
│   │   │   ├── database.py
│   │   │   ├── models.py
│   │   │   └── seed.py
│   │   ├── services/
│   │   │   ├── common.py
│   │   │   ├── memory.py
│   │   │   ├── conflict_engine.py
│   │   │   ├── twin_engine.py
│   │   │   ├── ledger.py
│   │   │   └── bodyguard.py
│   │   ├── routers/
│   │   │   ├── auth.py
│   │   │   ├── system.py
│   │   │   ├── dashboard.py
│   │   │   ├── cases.py
│   │   │   ├── conflicts.py
│   │   │   ├── simulations.py
│   │   │   ├── approvals.py
│   │   │   ├── memory.py
│   │   │   ├── ledger.py
│   │   │   ├── bodyguard.py
│   │   │   ├── integrations.py
│   │   │   ├── search.py
│   │   │   └── demo.py
│   │   └── static/
│   │       ├── finals.html
│   │       ├── styles.css
│   │       └── app.js
│   ├── tests/test_e2e.py
│   ├── scripts/smoke_demo.py
│   ├── requirements.txt
│   ├── Dockerfile
│   └── run.py
├── docs/
│   ├── PROJECT_STRUCTURE.md
│   ├── ARCHITECTURE.md
│   ├── API_CONTRACT.md
│   ├── GRAND_FINALS_DEMO_SCRIPT.md
│   └── PROTOTYPE_TO_FUNCTION.md
└── reference/Prototype-reference.txt
```

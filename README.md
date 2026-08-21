JurisTwin Sentinel — Mastery UI v11

JurisTwin Sentinel is a governed enterprise decision-intelligence prototype for detecting conflicting organizational knowledge, safely answering policy questions, escalating uncertainty to authorized Superadmins, and converting approved resolutions into reusable governed decision memory.

1. Run the Prototype

Requirements

Windows 10/11 recommended for the provided .bat launchers

Python 3.10+

pip

Modern browser such as Chrome or Edge

Fastest Setup

Extract the repository, then from the project root run:

preflight_finals.bat

This prepares the environment and runs the automated regression suite.

For a clean demo state:

reset_demo.bat

Start JurisTwin:

run_finals.bat

Then open:

http://127.0.0.1:8000/finals

Manual Backend Setup

If the batch launcher cannot be used:

cd backend
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python run.py

If PowerShell blocks virtual-environment activation:

Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\.venv\Scripts\Activate.ps1

Demo Accounts

Regular User

Email: user@juristech.com
Password: Finals2026!

Superadmin

Email: superadmin@juristech.com
Password: Finals2026!

Demo credentials are for the hackathon prototype only and must be replaced by enterprise identity/SSO controls for production deployment.

2. Test the Prototype

Recommended

Run:

preflight_finals.bat

The current Mastery UI v11 regression suite validates 33 critical behaviors, including:

governed-answer generation;

contradictory-source suppression for Regular Users;

unknown-question abstention and escalation;

semantic knowledge-gap deduplication;

Superadmin evidence resolution;

governed decision-memory reuse and rollback;

source revalidation;

RBAC enforcement;

PII masking;

PM/DM ingestion rejection;

irrelevant group-chat rejection;

approved relevant group-channel ingestion;

encrypted customer-data export;

API-key and HMAC verification;

replay protection;

audit-chain integrity;

Monte Carlo Digital Twin execution;

frontend accessibility controls.

Latest validated build result: 33 / 33 tests passed.

Clean Demo Reset

Before repeating the full finals workflow:

reset_demo.bat

This prevents previously governed demo decisions from changing the expected fallback behavior.

3. Dependencies

The authoritative Python dependency list is:

backend/requirements.txt

Install all backend dependencies with:

python -m pip install -r backend/requirements.txt

Main Technology Dependencies

Layer

Technology

Purpose

API

FastAPI

Backend REST API and application services

Server

Uvicorn

ASGI application server

Persistence

SQLAlchemy

ORM and database abstraction

Prototype DB

SQLite

Lightweight local hackathon persistence

Production DB path

PostgreSQL-compatible configuration

Enterprise deployment path

Authentication

JWT-based authentication

Session and role authorization

ML

scikit-learn

TF-IDF and Logistic Regression pipelines

Numerical analysis

NumPy

Monte Carlo / analytical operations

Security

Python cryptographic primitives

HMAC, hashing and encrypted export controls

Frontend

HTML, CSS, JavaScript

Responsive role-specific UI

Testing

pytest

Automated regression tests

Use backend/requirements.txt as the exact source of package names and pinned/version constraints for this repository.

4. Architecture

Enterprise Sources
        |
        v
+---------------------------+
| Privacy Collection Gate   |
| - Approved group channels |
| - Relevant content only   |
| - PM / DM / 1:1 blocked   |
| - PII checks              |
+---------------------------+
        |
        v
+---------------------------+
| Governed Evidence Store   |
+---------------------------+
        |
        v
+---------------------------+
| AI / Decision Pipeline    |
| TF-IDF retrieval          |
| Logistic Regression       |
| Evidence ranking          |
| Policy Atom Reasoner      |
+---------------------------+
        |
        +------------------------------+
        |                              |
        v                              v
  Sufficient evidence             Uncertainty
        |                              |
        v                              v
 Regular User Answer          Knowledge Gap Queue
 supporting sources only              |
                                       v
                              Superadmin Review
                                       |
                        +--------------+-------------+
                        | Supporting / Contradiction |
                        | Context / Why Disagree     |
                        +--------------+-------------+
                                       |
                                       v
                              Human Publish Gate
                                       |
                                       v
                            Governed Decision Memory
                                       |
                                       v
                           Similar Future Questions

Architectural Principle

AI recommends and explains; an authorized human governs publication.

JurisTwin deliberately separates retrieval, recommendation, and publication authority. New organizational policy is not silently created by an ML model.

5. Role Architecture

Regular User

The Regular User has a deliberately minimal single-page experience:

Ask JurisTwin → Answer → Verified Sources

Regular Users do not see contradictory evidence, internal confidence traces, governance scoring, audit controls, or administrative functions.

When evidence is insufficient, JurisTwin safely abstains and creates a Superadmin review task instead of inventing an answer.

Superadmin

The Superadmin receives additional governance capabilities:

Ask JurisTwin;

Safe to Publish;

Adoption & Impact;

Management Controls;

Privacy & Data Security;

Compare Evidence;

Audit Evidence;

Judge Proof.

The Safe to Publish workspace separates evidence into:

Supporting

Contradicting

Context

and provides a concise Why Sources Disagree explanation plus expandable technical traces.

6. AI and Decision Logic

TF-IDF + Logistic Regression

JurisTwin uses TF-IDF word and character features with Logistic Regression for policy-domain routing/classification.

Evidence Retrieval and Ranking

Retrieved evidence is scored using:

45% Semantic Relevance
25% Source Authority
15% Approval Status
10% Recency
 5% Active Lifecycle Status

Policy Atom Reasoner

A deterministic white-box layer checks explicit policy disagreement such as:

may versus must;

permitted versus prohibited;

conflicting numeric thresholds;

deadline differences;

calendar versus business days;

superseded versions;

incompatible policy conditions.

This complements statistical retrieval instead of relying on semantic similarity alone.

Governed Decision Memory

A Superadmin-approved resolution may be reused for semantically similar future questions using a hybrid of:

TF-IDF similarity;

token overlap;

policy-domain consistency.

If the similarity threshold is not satisfied, JurisTwin abstains again.

7. Privacy and Security

Collaboration Privacy Boundary

JurisTwin does not treat all collaboration messages as collectible evidence.

Approved Group Channel
        |
        v
Relevance Gate
        |
        v
PII + Lifecycle Validation
        |
        v
Governed Evidence

Blocked:

private messages;

DMs;

1-to-1 conversations;

unrelated group-channel chatter.

Formal approved enterprise documents and governed repositories remain separate permitted sources.

Customer-Data Export

Superadmin customer-data exports use:

PII-minimized payloads;

AES-256-GCM encryption;

PBKDF2-HMAC-SHA256 key derivation;

one-time Superadmin passphrase;

SHA-256 fingerprinting;

audit logging.

System-to-System Transfer

The integration boundary is designed around:

HTTPS/TLS in production;

server-side API keys;

HMAC-SHA256 request signatures;

timestamp validation;

replay protection;

payload digest verification.

API secrets are not exposed to browser-side JavaScript.

Auditability

Sensitive governance/security actions are written to a tamper-evident HMAC-SHA256 chained audit ledger.

8. Monte Carlo Decision Digital Twin

The Compare Evidence appendix retains the JurisTwin Decision Digital Twin.

Current prototype configuration:

500 Monte Carlo simulations
× 3 remediation strategies
= 1,500 scenarios

It evaluates decision options under uncertainty using operational factors such as:

delay;

complaint probability;

policy alignment;

affected cases;

duplicate requests;

overall decision fit.

Outputs include:

P10 / P50 / P90 ranges;

sensitivity analysis;

Pareto optimality;

recommendation stability;

robustness certificate.

The Digital Twin is a transparent prototype what-if/stress-testing layer, not a claimed production forecasting model.

9. Key API / Backend Design Notes

FastAPI provides the service/API layer.

SQLAlchemy separates persistence logic from application logic.

SQLite enables reliable offline hackathon execution.

The architecture supports a PostgreSQL production migration path.

RBAC is enforced by the backend, not merely by hiding frontend controls.

Unknown questions fail closed into the governance queue.

Source lifecycle is revalidated before governed memory is reused.

Superadmin decisions can be deactivated/rolled back.

Canonical conflicts between authoritative current sources fail closed.

Request validation, request-size controls, security headers, and exception containment protect the primary workflow.

The core demo does not depend on an external CDN.

10. Repository Structure

The main project areas are organized conceptually as:

JurisTwinSentinel/
|
|-- backend/
|   |-- application/API logic
|   |-- models and persistence
|   |-- ML / retrieval / governance logic
|   |-- security controls
|   |-- tests
|   `-- requirements.txt
|
|-- frontend / static application assets
|
|-- docs/
|   |-- architecture notes
|   |-- finals demo flow
|   |-- security/compliance notes
|   |-- UI/UX notes
|   `-- test evidence
|
|-- run_finals.bat
|-- preflight_finals.bat
|-- reset_demo.bat
`-- README.md

Refer to the actual repository tree for exact module/file names.

11. Recommended Finals Demo

Log in as Regular User.

Ask: Can gig workers use bank statements as income evidence?

Show the governed answer and safe supporting source.

Ask: Do QR merchant settlement records count as income proof for self-employed applicants?

Show JurisTwin safely abstaining.

Log in as Superadmin.

Open the newly created review task and click Solve.

Show Supporting, Contradicting, Context, and Why Sources Disagree.

Publish a human-governed response.

Return as Regular User and ask a paraphrased version.

Show governed decision-memory reuse.

Demonstrate Privacy & Data Security / Audit Evidence.

Open Compare Evidence to show the 1,500-scenario Monte Carlo Digital Twin.

12. Production Considerations

This repository is a hackathon prototype. A production deployment would additionally require organization-specific controls such as:

enterprise SSO/OIDC;

managed secrets/key management;

production PostgreSQL/high-availability persistence;

organization-approved retention policies;

infrastructure monitoring and alerting;

production TLS termination;

enterprise backup/disaster recovery;

formal security testing;

organization-specific compliance/legal validation.

The prototype demonstrates the architecture and control mechanisms; it does not claim production certification.

13. One-Line Pitch

JurisTwin Sentinel is the governance layer that stops conflicting enterprise knowledge from becoming conflicting customer decisions.

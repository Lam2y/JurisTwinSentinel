# JurisTwin Sentinel — Championship Finals v7.0

## Why this build exists

The final-round rubric rewards what the judges can see working live. v7.0 therefore keeps the existing technical architecture but reorganises the experience around visible, scoreable proof rather than adding risky last-minute subsystems.

## Rubric-to-live-proof map

| Criterion | Weight | v7.0 proof shown live |
|---|---:|---|
| Core Functionality & Feature Execution | 30% | Natural-language governed answer, same-question role switch, live evidence-boundary mutation, judge-controlled unseen text/file input, process simulation, human publication, backend export enforcement |
| Technical Depth & Architecture | 25% | Local learned policy classifier, symbolic Policy Atom verification, source governance, authority-first resolution, BM25 + cosine retrieval, BFS impact graph, 1,500-scenario Monte Carlo/sensitivity/Pareto certificate, RBAC, signed ingress, decision ledger and proof verification |
| UX & Interface Usability | 20% | One linear sidebar story, answer-first hierarchy, first-minute conflict/impact reveal, one-click role proof, real source toggles, readable A/B/C decision contrast, explicit AI/human authority boundary, persistent security result |
| Technical Innovation & Creativity | 15% | Conflict-not-consensus behavior, authority-before-frequency, dynamic evidence boundary, AI with zero publication authority, process-level response simulation and decision-integrity proof |
| System Stability & Error Handling | 10% | 72 automated tests, championship preflight, deterministic reset, automatic port failover, launcher auto-prepare, safe abstention, input/file validation, GET-only transient retry, backend RBAC/403 enforcement |

## v7.0 score-moving changes

### First-minute impact
The answer view now exposes the conflict and blast radius immediately rather than making the judge wait for the conflict page. The backend answer contract also returns an explicit `impact` object and `runtime_trace` object, keeping the visual claims tied to server-side state.

### Same-question role proof
Managers can preview the exact same question as an Intern. Restricted evidence is redacted by the backend role policy; this is not a frontend-only hide/show trick.

### Live evidence-boundary mutation
Management Controls exposes live retrieval toggles. Turning SharePoint/FSD retrieval off changes the next governed source pool while leaving the higher-authority Outlook answer intact. This demonstrates that source governance changes runtime behavior without allowing lower-authority noise to change truth.

### Process optimisation, not three generic cards
The simulator now labels the options as `RISK REMAINS`, `PARTIAL FIX` and `PROCESS FIX`, while the recommended complete-process option visibly covers FSD, training, officers, affected cases and QA controls. Robustness still comes from the existing 1,500-scenario white-box simulation.

### Human authority as the climax
The publication screen now makes `AI PUBLICATION AUTHORITY = 0%` and `HUMAN AUTHORITY = REQUIRED` the central visual. After approval, the page retains the decision ID, approver, protected-case count and proof-verification action.

### Judge Challenge Mode
Unseen judge text or supported files are processed at runtime. The result page now exposes the actual measured pipeline stages stored by the backend, including live latency, before showing contradiction/abstention, quarantine and blast radius.

### Persistent backend security proof
The export test no longer relies on a short toast. The interface keeps the backend result visible, including HTTP status, so a denied full export is unmistakably a server-side control.

### Demo resilience
The finals launcher now waits for health, resets the deterministic scenario, confirms system readiness and warms the local AI before opening the browser. GET requests retry once for transient transport/502/503/504 errors; mutation requests are never automatically replayed.

## Claims boundary

This remains an honest prototype. Deterministic vendor adapters are labelled as such; the signed webhook is the genuine live ingress contract. The runtime retrieval engine is BM25 + cosine. The Decision Twin is white-box and prototype-calibrated. Client evidence does not train the policy classifier. The ledger is not blockchain.

That honesty protects Technical Depth: judges can inspect what is genuinely implemented without finding a mismatch between pitch language and runtime behavior.

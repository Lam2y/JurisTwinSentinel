# JurisTwin Sentinel — Judge Q&A Battlecard

Keep answers direct. Give the one-sentence answer first; expand only if the judge asks.

## 1. “What exactly is JurisTwin?”
**A contradiction-safe enterprise decision memory.** It gives employees one governed answer from approved evidence, and sends uncertainty or disagreement to a human governance workflow instead of letting AI guess.

## 2. “Where is the AI / ML?”
TF-IDF word and character features represent text; Logistic Regression routes policy domains and stance; TF-IDF retrieves relevant evidence; a deterministic Policy Atom layer verifies concrete policy collisions.

## 3. “Why not just use an LLM or normal RAG?”
Normal retrieval can return two contradictory documents and leave the model to choose. JurisTwin makes evidence authority, lifecycle, approval and contradiction explicit gates before an answer is allowed to reach the user.

## 4. “Does the ML make the final decision?”
No. ML is advisory for routing and relevance. The publication gate and human superadmin are the final authority.

## 5. “What happens when the AI does not know?”
It abstains, creates or merges a knowledge gap, alerts the superadmin, and waits for a governed resolution. Guessing is treated as a failure mode.

## 6. “How do you prove it is not hardcoded?”
Ask a new question live, add new evidence live, publish a new resolution, then rephrase the question. The database state and semantic match change the future answer without editing code.

## 7. “How do similar future questions get the same answer?”
A human-approved decision is stored as governed pattern memory. Reuse scores 65% TF-IDF similarity, 25% token overlap and 10% domain consistency, and must clear the approved threshold.

## 8. “Is that model retraining?”
No. We deliberately separate governed memory from model retraining. Client evidence is retrieval context and is not appended to the classifier corpus.

## 9. “What if the stored resolution becomes outdated?”
If it cites evidence, that evidence is revalidated on reuse. Superseded or inactive lineage blocks the answer and sends it back to review. Superadmins can also deactivate a decision memory explicitly.

## 10. “What if two approved policies disagree?”
JurisTwin fails closed. It publishes neither source, creates a canonical-conflict review item and requires governance resolution.

## 11. “Why TF-IDF and Logistic Regression instead of a huge model?”
For this policy-routing layer they are fast, local, deterministic enough to inspect, work offline and give confidence/probability traces. We combine them with symbolic checks and human governance rather than pretending one model solves policy authority.

## 12. “What is your evidence ranking formula?”
45% semantic relevance, 25% authority, 15% approval, 10% recency and 5% active lifecycle. Ranking is advisory; only approved/current evidence can publish.

## 13. “How does the contradiction engine work?”
The Policy Atom Reasoner converts policy statements into comparable properties such as permission/prohibition, numeric thresholds and deadline semantics, then reports collisions in plain language.

## 14. “What happens if the ML service breaks?”
The core model is local, but if the learned router fails the system can fall back to deterministic evidence-domain similarity. All publication safety gates remain active and the system can still abstain safely.

## 15. “How do you protect privacy?”
We mask common PII before unresolved prompts or feedback are stored, reject PII in policy evidence intake, restrict governance by role, separate retrieval from training and enforce a resolved-review retention window.

## 16. “How do you protect the audit trail?”
Security-sensitive events are linked with a server-keyed HMAC-SHA256 chain. Our automated tests physically alter an old ledger payload and verify the chain becomes invalid.

## 17. “Are you compliant with BNM / PDPA?”
We claim **design alignment, not certification**. The prototype maps concrete controls to PDPA, revised BNM RMiT, NIST AI RMF and OWASP guidance; formal compliance depends on the deploying institution and legal/security review.

## 18. “What makes this resilient?”
Fail-closed answer gates, offline core logic, database health checks, deterministic fallback, source revalidation, rollback, request containment, exception handling, retention enforcement and a live 11-check resilience test.

## 19. “Where is your market validation?”
We do not fabricate customer traction. The prototype measures real usage—answer/escalation rate, reuse, feedback and latency—and demonstrates an API/database/deployment path. The ROI panel is clearly an assumption-based scenario tool.

## 20. “Who would buy/use this?”
Organizations where decisions depend on policies scattered across email, SOPs, approvals and operational messages—especially regulated financial operations, compliance, risk, servicing and customer-support teams.

## 21. “What is the business value?”
Reduce time spent reconciling policy, prevent inconsistent customer decisions, preserve who approved what, and turn repeated unresolved questions into governed reusable knowledge.

## 22. “How would you integrate this with a bank?”
Replace demo login with enterprise SSO/OIDC, use managed PostgreSQL, ingest approved enterprise evidence through controlled connectors/APIs, map authority to the institution’s governance model and export audit events to centralized monitoring.

## 23. “Can it scale?”
The application layer is stateless except for persistence and the demo uses SQLite for reliability. SQLAlchemy and `psycopg` provide the PostgreSQL path; production would add managed DB, workers/caching where needed, migration tooling and centralized observability.

## 24. “Why only two users?”
It makes the authorization model and user journey unambiguous for the hackathon: frontline consumption versus governance authority. A production RBAC model can subdivide the superadmin capabilities into policy owner, reviewer, security and auditor roles.

## 25. “What are the biggest limitations?”
The ML benchmark is a curated development benchmark, demo identity is local, SQLite is the hackathon default, enterprise connectors/SSO are not completed, and compliance mapping is not certification. We expose these boundaries in the product.

## 26. “What is your most innovative technical idea?”
The answer firewall plus governed self-healing loop: AI may inspect contradictory enterprise evidence, but it cannot silently publish policy; unresolved knowledge becomes a human decision that can be reused semantically, revalidated and rolled back.

## 27. “Why will users trust it?”
Because the user sees the answer and safe source lineage, while governance can inspect exactly why competing sources were rejected. Trust comes from bounded behavior and evidence, not from asking users to trust a black box.

## 28. “What if the user says the answer is wrong?”
“Needs review” is not discarded. It creates a governed review item tied to the original interaction so the organization can correct the decision memory.

## 29. “What if someone uploads malicious or irrelevant evidence?”
It is quarantined as unapproved, checked for PII and collisions, and cannot change frontline policy simply because it was uploaded.

## 30. “What would you build next?”
Enterprise SSO, formal multi-stage evidence approval, connector-based evidence ingestion, managed PostgreSQL/migrations, centralized observability, richer document provenance/signatures and an organization-specific evaluation corpus.


## 31. “Do you read employees’ private messages?”
No. PM, DM and 1:1 sources are blocked at ingestion. Approved group-channel material must also pass a policy-relevance gate, so JurisTwin does not collect unrelated group chatter.

## 32. “Why are formal approvals still allowed if you say group chat only?”
The restriction applies to collaboration chat privacy. Formal approvals and governed repositories are separate authoritative enterprise sources needed to establish the canonical rule; private conversations are not.

## 33. “How do you protect exported customer data?”
The Superadmin export is PII-minimised and encrypted with AES-256-GCM. The export passphrase is never persisted, and the export action is audit logged.

## 34. “How do two systems exchange the data securely?”
The integration endpoint accepts ciphertext only. The server validates a scoped API key, HMAC-SHA256 signature, payload digest and timestamp replay window; production can require HTTPS/TLS.

## 35. “Is the API key inside the JavaScript?”
No. The browser sees only a short fingerprint. The actual integration secret is server-side and excluded from the project package.

## 36. “What does the audit log prove?”
It proves accountability and tamper evidence: who performed a governed action, when it happened, and whether the HMAC-chained event history still verifies. Export, transfer and privacy-block events are included too.

## 37. “What is the Monte Carlo Digital Twin doing?”
It stress-tests three remediation choices across 1,500 scenarios using explicit operational assumptions. It reports uncertainty bands, sensitivity stability, Pareto optimality and a robustness certificate; it is not presented as a trained production forecast.

## 38. “Why does the Superadmin see more than the employee?”
Least privilege and cognitive load. The employee needs a defensible answer, while the authorized decision owner needs source scope, authority, lifecycle, contradictions and reasoning. Deeper model and audit details stay expandable so the admin page does not become a wall of text.

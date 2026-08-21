# Latest Finals Rubric — Mastery Mapping

The official Phase 3 finalist rubric weights the system as follows:

- **Technical Execution & Functionality — 30%**
- **Security, Compliance & Risk Resilience — 25%**
- **Market Feasibility & Validation — 20%**
- **UX/UI Polish & Accessibility — 15%**
- **Defensibility & Q&A — 10%**

**v11 additions:** privacy-scoped group-channel ingestion, encrypted customer export, authenticated ciphertext transfer, Audit Evidence slides, a 1,500-scenario Monte Carlo Decision Digital Twin and a deeper progressive-disclosure Superadmin UI.

This build is designed to give the team a **live proof object** for every category rather than relying on claims in the pitch.

> No software change can guarantee a judge score. “Mastery target” below means the implementation has been deliberately optimized to satisfy the rubric’s exceptional/mastery intent and to make the evidence easy to demonstrate.

---

## 1. Technical Execution & Functionality — 30% — Mastery target

### What the judges can see live
- Known policy question → immediate governed answer + source.
- Novel policy question → safe abstention + persisted superadmin notification.
- Semantic duplicate question → same queue item, occurrence count increases.
- Safe to Publish → supporting/conflicting/context evidence + disagreement explanation.
- Runtime evidence intake → new evidence appears in the analysis immediately but remains quarantined.
- Superadmin publication → persistent reusable governed memory.
- Rephrased question → newly published response reused without exact-string matching.
- Rollback → deactivated decision memory returns the subject to review.
- Negative user feedback → answered item re-enters governance.
- Canonical split-brain → two current approved sources disagree and the user answer path fails closed.

### Backend proof
- FastAPI APIs.
- SQLAlchemy transactional persistence.
- JWT/RBAC.
- TF-IDF word + character n-grams.
- Logistic Regression routing/stance layer.
- Dynamic evidence retrieval.
- Governance-weighted ranking.
- Deterministic Policy Atom contradiction reasoner.
- Human-governed semantic memory.
- HMAC-SHA256 ledger.
- 25-test automated regression suite.

### Demo sentence
“JurisTwin does not only answer a prepared example. I can introduce a new question or evidence item live, create state in the database, govern the resolution and prove the next paraphrase behaves differently because of that decision.”

---

## 2. Security, Compliance & Risk Resilience — 25% — Mastery target

This is now the second-largest category, so the build treats it as a primary feature rather than an appendix checkbox.

### Security controls
- Backend-enforced least-privilege RBAC.
- Per-interaction ownership checks for feedback.
- PII masking before review persistence.
- PII rejection on evidence intake.
- Retrieval/training separation.
- HMAC-SHA256 chained audit trail.
- Stable signing secret across demo restarts; production environment/secret-manager path.
- Restricted CORS, no-store, CSP, frame denial, MIME sniff protection and permissions policy.
- Request-size limit, field validation and rate containment.

### AI / policy risk controls
- Confidence gate.
- Evidence coverage gate.
- Approved/current source gate.
- Canonical split-brain gate.
- Pattern-source revalidation.
- Deterministic model fallback.
- Human publication authority.
- Reversible decision memory.
- User-feedback escalation.

### Operational resilience
- Database pre-ping.
- Offline core model/reasoner.
- Startup model warm-up.
- Global exception containment.
- Live 11-check resilience test with persisted history.
- Automated preflight script.
- Clean-state reset script.
- Docker health check, persistent volume and restart policy.
- Resolved review-data retention enforcement.

### Compliance positioning
The UI maps implementation evidence to Malaysia PDPA, the revised BNM RMiT, NIST AI RMF and OWASP API Security. The product explicitly labels these as **design alignment, not certification or legal advice**.

### Demo sentence
“Security is not a slide here. I can run the resilience test now, show the live result, prove that a regular user gets 403 on governance APIs, and show that tampering with an audit record is detectable by our chained HMAC.”

---

## 3. Market Feasibility & Validation — 20% — Mastery target

The system avoids fake customer numbers. Instead it proves practicality with live prototype telemetry and a credible enterprise integration path.

### Live validation signals
- Interaction count.
- Answered vs safely escalated rate.
- Pattern-reuse count/rate.
- User helpfulness ratings.
- Negative feedback count.
- Median and p95 prototype latency.
- Open governance workload.
- Active human-approved memory count.

These values are generated from actual use of the demo.

### Adoption design
- Frontline user learns one action: ask.
- Governance effort is concentrated in the superadmin workspace.
- API-first application boundary.
- SQLite demo path minimizes hackathon failure risk.
- PostgreSQL driver and `DATABASE_URL` path reduce database migration cost.
- Offline-capable core lowers dependency risk.
- SSO/OIDC integration point is stated openly.
- Dockerized deployment path.

### Business-value tool
The Adoption & Impact page includes an **assumption-based ROI scenario calculator** for decisions/day, minutes saved/decision and staff hourly cost. It is visibly labelled as an illustrative planning model, not claimed customer validation.

### Demo sentence
“We separate what we have actually validated from what is an assumption. These operating metrics come from the live prototype; this ROI calculator is explicitly a scenario. We would rather show judges a truthful adoption model than invent a customer result.”

---

## 4. UX/UI Polish & Accessibility — 15% — Mastery target

### Regular user
- One page.
- No sidebar.
- One primary action.
- Answer + safe sources only.
- No contradictory evidence burden.
- Loading, answered, review-pending, feedback and failure states.
- Keyboard Enter-to-send behavior and visible character count.

### Superadmin
- Information architecture separates Workspace, Governance and Appendix.
- New knowledge-gap notification is placed directly under the chatbot.
- Safe to Publish is the center of the admin workflow.
- Technical details are expandable rather than permanently crowding the primary decision.
- Compare Evidence / Judge Proof are explicitly Appendix.

### Accessibility mechanisms
- Semantic labels.
- Skip-to-content link.
- Visible `:focus-visible` states.
- Keyboard-operable native controls.
- `aria-live` feedback/toasts.
- Responsive layout.
- Reduced-motion preference support.
- Increased-contrast preference support.
- No critical information encoded only by animation.

### Demo sentence
“The employee interface is intentionally simpler than the technology behind it. Our goal is not to make users operate an AI governance console; their only job is to ask a question.”

---

## 5. Defensibility & Q&A — 10% — Mastery target

### In-product Judge Proof screen
It exposes:
- architecture layers,
- not-hardcoded proof points,
- model card and development benchmark,
- explicit limitations.

### Q&A stance
- Never call the curated development benchmark production accuracy.
- Never claim the compliance mapping is certification.
- Never claim ROI calculator values are customer results.
- Explain why the system abstains as a design strength, not a model failure.
- Be able to distinguish TF-IDF retrieval, Logistic Regression routing, Policy Atom reasoning and human publication authority.
- Be able to explain how client evidence is prevented from silently becoming training data.

### Demo sentence
“The AI is allowed to recommend and explain; it is not allowed to silently create policy. That separation is the center of our architecture.”

---

# Recommended finals proof sequence

1. Regular known answer.
2. Regular unseen question → abstention.
3. Superadmin notification → Solve.
4. Safe-to-Publish evidence groups + disagreement explanation.
5. Optional live evidence ingestion to prove dynamic processing.
6. Human publish with uncertainty note.
7. Rephrased regular question → governed memory reuse.
8. Regular user marks answer Needs review → show quality loop if time permits.
9. Resilience Test → live pass + risk/compliance page.
10. Adoption & Impact → actual demo metrics.
11. Judge Proof only during Q&A.

The winning story is not “we built the most screens.” It is “we built one complete decision-governance loop and can prove its functionality, safety, adoption path, UX and technical defensibility live.”


## v11 live proof objects

### Technical Execution — 30%
- live question → abstention → resolution → semantic reuse;
- privacy-scoped dynamic evidence intake;
- 1,500-scenario Monte Carlo Decision Digital Twin;
- source/decision lineage and rollback.

### Security, Compliance & Risk Resilience — 25%
- PM/DM/1:1 ingestion blocked;
- group relevance gate;
- AES-256-GCM customer export;
- API-key + HMAC ciphertext transfer;
- HMAC audit-chain verification;
- live resilience and secure-transfer self-tests.

### Market Feasibility & Validation — 20%
- operational telemetry from real demo interactions;
- encrypted export and integration gateway show a credible enterprise handoff path;
- the employee workflow remains low-friction while governance is centralized.

### UX/UI Polish & Accessibility — 15%
- one-page Regular User experience;
- progressive disclosure for Superadmin;
- compact decision brief + evidence cards instead of long prose;
- JurisTech-aligned red/graphite/white visual system;
- keyboard, contrast, reduced-motion, responsive and projector-readability support.

### Defensibility & Q&A — 10%
- Audit Evidence appendix;
- Technical Trace;
- live privacy/transfer proof;
- explicit Monte Carlo assumptions and robustness certificate;
- implementation limitations stated rather than hidden.

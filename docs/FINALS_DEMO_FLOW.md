# Finals Demo Flow — JurisTwin Sentinel v11

Use this as one story, not a menu tour.

## Before demo
1. `preflight_finals.bat` → confirm **33 passed**.
2. `reset_demo.bat`.
3. `run_finals.bat`.
4. Open `/finals`.

## Act 1 — Regular User simplicity
Login as Regular User and ask:

**Can gig workers use bank statements as income evidence?**

Show one governed answer + safe source. Point out that contradictory material is withheld from the employee.

Then ask:

**Do QR merchant settlement records count as income proof for self-employed applicants?**

JurisTwin should abstain and create a governance item.

## Act 2 — Superadmin depth without clutter
Login as Superadmin. Click **Solve** on the new notification.

On Safe to Publish show, in this order:
1. Admin Decision Brief — coverage, source boundary, visibility, decision owner.
2. Supporting / Contradicting counts.
3. Why Sources Disagree.
4. One evidence card showing source scope + authority + relevance.
5. Expand Technical Trace only if the judge wants the ML/reasoning detail.

Say: **“The employee sees one governed answer; the Superadmin sees exactly enough evidence to defend why it is safe.”**

## Act 3 — privacy proof
Open **Privacy & Data Security**.

Show the source boundary:
**approved group channel → relevance gate ≥55% → PII/lifecycle gate → governed retrieval**.

Point to **PM / DM / 1:1 blocked**. Explain that JurisTwin does not indiscriminately scrape collaboration data; unrelated group chatter is rejected too.

## Act 4 — customer-data export + transfer
On the same page:
- generate an encrypted `.jtx` customer-data export with a demo passphrase;
- show AES-256-GCM + PBKDF2 manifest and audit transaction ID;
- run **Secure-transfer test** and show API-key gate + HMAC integrity + replay protection.

Say: **“Export data is encrypted at rest; system-to-system traffic is ciphertext-only and authenticated server-side. The browser never receives the API key.”**

## Act 5 — audit evidence (optional main demo; excellent Q&A appendix)
Open **Audit Evidence**.
Use the three slide-like panels:
- Accountability;
- Tamper Evidence;
- Data Lifecycle.

Show that the export and transfer events you just created are now part of the live ledger.

## Act 6 — Monte Carlo Digital Twin (appendix / innovation proof)
Open **Compare Evidence**.
Show the **1,500-scenario Decision Digital Twin** first. Explain:
- 500 simulations per remediation option;
- P10/P50/P90 uncertainty;
- sensitivity stability;
- Pareto frontier;
- robustness certificate.

Move a weighting slider and rerun to prove it is live. Do not present the twin as a trained forecast; it stress-tests explicit operational assumptions.

## Act 7 — publish + reuse
Return to Safe to Publish. Publish a human-governed response with an uncertainty note if no approved evidence explicitly covers the new case.

Return to Regular User and ask a paraphrase. JurisTwin should reuse the governed memory if semantic/domain similarity clears the threshold.

## Closing line
**“JurisTwin collects less, exposes less, guesses less—and gives authorized humans more evidence exactly when a decision needs governance.”**

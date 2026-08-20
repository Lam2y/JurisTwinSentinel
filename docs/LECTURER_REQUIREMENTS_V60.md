# JurisTwin Sentinel v6.0 — Lecturer Requirements: Original vs Complete System

This release turns the lecturer's recommendations into visible, executable product controls rather than presentation claims. The new **Management Controls** page is the in-system checklist: each requirement shows what the original prototype did, what v6.0 does now, live proof, and the page where a manager can test it.

## 1. Management gets one definite answer and the exact source

**Original prototype:** conflict discovery was the hero experience; management had to interpret technical evidence and graphs.

**v6.0:** Ask JurisTwin is answer-first. It returns the instruction staff should follow, a single primary governed source, supporting sources that actually won, resolution reason, privacy exclusions, and freshness. Hybrid keyword/BM25 + semantic retrieval finds relevant evidence, but retrieval rank never grants policy authority.

**Where to demonstrate:** `Ask JurisTwin` → ask `Can gig workers use bank statements as income evidence?`

## 2. Management controls which enterprise sources are eligible

**Original prototype:** connectors existed but source inclusion was mostly implicit.

**v6.0:** `Privacy & Security` exposes Source Scope Control. Managers/Compliance can narrow approved Teams groups/channels, approved official-email sender roles, and approved SharePoint libraries. Backend retrieval enforces these lists.

**Hard privacy boundaries:**
- Teams personal/1-to-1 DMs cannot be enabled.
- Teams group/channel evidence is reference/context only and cannot become the main official policy source.
- Outlook/Gmail remain official-only.
- Customer Core is impact/context only and cannot define policy.
- Client evidence never becomes model-training data.

**Where to demonstrate:** `Privacy & Security` → select a source → `Configure`.

## 3. Conflict resolution is authority-first, with safe majority fallback

**Original prototype:** conflict weighting was visible, but the management rule was not simple enough.

**v6.0 resolution order:**
1. Active human-approved Decision Contract.
2. Approved source inside the configured source scope, ranked by authority.
3. If no canonical source exists, majority only among evidence in the *same highest authority tier*.
4. Tie/uncertainty → human review; JurisTwin refuses to invent a winner.

This prevents ten casual chats from outvoting one Product Owner approval.

**Where to demonstrate:** `Ask JurisTwin` → `How sources were found`; `Management Controls` → conflict-resolution card.

## 4. Privacy and data minimisation are explicit

**Original prototype:** RBAC/redaction existed but privacy boundaries were not obvious to managers.

**v6.0:** personal DMs, casual/unapproved email and out-of-scope repositories are excluded before policy resolution. Customer communications can establish impact, not policy authority. Every source card shows what is allowed and what is blocked.

**Where to demonstrate:** `Privacy & Security` → source cards and security guarantees.

## 5. Customer-data export security is enforced server-side

**Original prototype:** data-security concepts were present but forbidden export actions were not a prominent manager workflow.

**v6.0:** customer data separates view permission, masked export and full export. Full export is restricted to authorised Compliance roles; Manager can use masked export; lower roles cannot export. The API enforces the rule even if the browser UI is bypassed. Export reason and outcome are audited.

**Where to demonstrate:** `Privacy & Security` → Customer Data Security → safe masked export → restricted full export.

## 6. Data transfer, encryption and API-key handling are visible

**Original prototype:** connector security was mostly technical architecture.

**v6.0:** a manager-facing protected-data path explains source → authenticated connector → scope/privacy filter → access check → governed index. Runtime secrets remain server-side. Real incoming evidence can use an HMAC-SHA256 signed webhook. Production deployment boundaries explicitly require TLS and encrypted persistence rather than falsely claiming localhost is bank production security.

**Where to demonstrate:** `Privacy & Security` → Protected Data Path → optional technical details.

## 7. Audit trail identifies who did what

**Original prototype:** decision ledger existed, but user-level query/export/source-change accountability was not a primary management view.

**v6.0:** questions, source-scope changes, approvals and customer-export attempts are attributed to actor, time, subject and outcome. Question audit uses a policy-safe excerpt/fingerprint to reduce unnecessary sensitive duplication.

**Where to demonstrate:** `Privacy & Security` → `Who did what?` Audit Log.

## 8. Real-time behavior is clear and testable

**Original prototype:** the polished demo could be mistaken for a static prepared story.

**v6.0:** every Ask JurisTwin request recomputes from the current governed state. The manager security view auto-refreshes. Source policy changes apply immediately to retrieval. Signed incoming evidence appears live, but is quarantined until governance makes it canonical. Freshness state and last-sync information are shown per source.

**Where to demonstrate:** `Privacy & Security` → Live Source Monitor; then `Test New Evidence` → analyse a new instruction → return to `Ask JurisTwin`.

## Head-to-toe manager UX changes

- Added **Management Controls** as a first-class navigation page.
- Larger presentation-safe typography throughout.
- Plain-language page names and controls.
- Persistent privacy/security trust messaging.
- Answer-first hierarchy; technical proof moved behind drill-downs.
- Conflict graph is optional evidence trail, not the first management task.
- Approval gate explains exactly why Publish is locked.
- Decision Proof is presented as manager-readable Audit Proof with technical fingerprints on demand.
- Source cards show approved scope, authority role, freshness and training boundary.
- Demo database self-check repairs stale case cohorts so the governance gate does not incorrectly show `0 operational cases` for the flagship conflict.

## Recommended lecturer demo path

1. **Management Controls** — prove every recommendation is now mapped to a working feature.
2. **Ask JurisTwin** — one definite answer + primary source + how sources were found.
3. **Privacy & Security** — show Teams DM block, official-email rule and configurable allowed scope.
4. **Customer Data Security** — masked export succeeds; forbidden full export is blocked server-side.
5. **Who did what?** — show the resulting audit trail.
6. **Test New Evidence** — add an unseen conflicting instruction.
7. **Why Sources Disagree** — show current official instruction and affected cases.
8. **Compare Solutions** — choose the complete-process option.
9. **Safe to Publish?** — all governance checks must pass.
10. **Approve & Publish → Audit Proof** — verify the governed decision record.

The management story is deliberately simple: **one trusted answer, only from approved sources, with protected customer data, controlled publication, live updates and a traceable record.**

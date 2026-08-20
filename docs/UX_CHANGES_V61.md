# v6.1 Executive UX pass

This build keeps the v6.0 lecturer-complete functionality but reduces reading load across the manager-facing UI.

## What changed
- Shorter page headings and subtitles.
- Ask JurisTwin now emphasizes: Answer, Source, Why, Privacy, Freshness.
- Source lists show the two most useful sources first; selection logic is collapsed behind “How was this answer chosen?”.
- Conflict page shows “Follow” vs “Conflicts” first; graph remains optional.
- Compare Solutions keeps the 3 options and key outcomes while moving “Why not A/B?” behind a compact disclosure.
- Safe to Publish removes verbose control explanations from the main view; details remain available as tooltips/technical disclosure.
- Privacy & Security now leads with four obvious manager states: Teams DMs blocked, casual email blocked, client AI training off, live refresh on.
- Source controls show only Used / Official-or-Reference / AI training off in the main card.
- Customer export access uses concise Allowed / Blocked verdicts.
- Data-transfer security is summarized as four one-line controls; TLS/HMAC details remain optional.
- Audit shows the latest eight events instead of a long wall of rows.
- Test New Evidence shows the new message, official message, what to follow, and affected cases; detailed reasoning is optional.

## Functionality retained
- Approved source scope controls.
- Teams group-only / no personal DM policy.
- Official email sender scoping.
- SharePoint library scoping.
- Authority-first conflict resolution with same-tier majority fallback.
- Role-based customer-data exports enforced server-side.
- Audit trail of questions, exports and source-policy changes.
- Real-time source freshness and per-question recomputation.
- Evidence challenge/quarantine workflow.
- Conflict graph and blast radius.
- Scenario simulation and recommendation.
- Governance Gate and human publication control.
- Proof Pack / ledger verification.

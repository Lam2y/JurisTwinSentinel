# JurisTwin Finals Frontend — v5.4

The frontend is a zero-build responsive SPA served by FastAPI. `frontend/src/` is the readable source mirror; deployed files live under `backend/app/static/`.

## Judge-facing information architecture

- Overview
- Conflict Map
- Digital Twin
- Assurance
- Evidence Lab

Everything else is progressive disclosure through Platform / Final Flow.

## v5.4 UX additions

- Secure Enterprise Memory includes a large **Verified Answer** interaction for plain-language Track 2 access.
- Answers expose status (`CONFLICT_PRESENT`, `VERIFIED`, `RESTRICTED`, `NEEDS_REVIEW`), authority, version and evidence lineage.
- Hybrid AI Policy Reasoner exposes learned prediction, symbolic collision, dual-control arbitration and Authority-Weighted Hybrid Consensus.
- All three conflicts are selectable and fully executable; flagship-only endpoint hardcoding has been removed.
- Proof Pack includes a live **Verify this proof** action.
- Presentation Mode remains available through `Alt+P`.

## Interaction rules

- Native document scrolling; sticky application chrome.
- One reusable side-sheet model; close via X, Escape or backdrop.
- Graph nodes remain clamped to visible SVG bounds.
- Non-stacking status capsule.
- View Transitions are progressive enhancement only.
- `prefers-reduced-motion` is respected.

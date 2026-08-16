# JurisTwin Sentinel v5.6.1 — Overview UI Hotfix

This frontend hotfix keeps the complete v5.6 Track-2 MaxScore backend and feature set unchanged while repairing two Overview components that could collapse visually.

## Fixed

- **Other Live Conflicts** is now a responsive conflict-card grid with explicit severity, conflict reference, wrapped title/cause, affected count and open-case affordance.
- **Decision Integrity** now uses a non-overlapping 0–100 gauge, four readable alignment bars and a clear assurance footer.
- Desktop, projector and mobile CSS breakpoints are explicit for both components.
- Presentation Mode has dedicated larger typography for both components.
- Source and FastAPI-served static assets are kept byte-for-byte in sync.
- Dedicated regression tests prevent the old unstyled inline layout from returning.

No pitch-deck feature, Track-2 function, v4 assurance feature, reasoning path, simulator, governance workflow, Bodyguard control, ledger, Proof Pack or evidence-ingress capability was removed or changed.

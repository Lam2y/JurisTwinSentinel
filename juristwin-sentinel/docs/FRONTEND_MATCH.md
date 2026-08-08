# Front-end Match

The v1.3 finals UI is generated from the ten original 1440×1024 prototype frames stored in `reference/Prototype-reference.txt`. It preserves the supplied layout, colors, spacing, typography sizes, labels, cards, graph positioning, and page structure. The UI is not a screenshot background: it is DOM markup with functional navigation/actions bound to the backend.

## Screen mapping

0 Login / System Access
1 Command Center
2 Customer Case Workspace
3 Evidence Network Graph / Conflict Intelligence
4 Decision Digital Twin
5 Approve Recommended Resolution
6 Decision Ledger
7 AI Bodyguard Security Center
8 Secure Enterprise Memory
9 Integrations & Administration

The renderer scales the 1440×1024 stage proportionally to the browser viewport. Font rasterization can differ slightly by browser/Windows display scaling, but the source geometry is the supplied prototype geometry.


## v1.3 finalist screen completion

- `screen5.html` — Approve Recommended Resolution, including authorisation process, affected assets, request changes/reject/publish controls and state-driven publication confirmation.
- `screen7.html` — AI Bodyguard Security Center, including clean incident metadata grid, version comparison, explainable flag reasons, activity review, explanation request, access revocation, compliance escalation, authorised override and approved-version restoration.
- Both screens remain live DOM interfaces and call backend APIs; they are not screenshot backgrounds.

# UI v11 — Finals Design Notes

## Design objective
Make the Regular User feel that JurisTwin is effortless, while letting the Superadmin see technical depth without turning the governance workspace into a research paper.

## Visual system
- JurisTech-aligned red (`#EC1C24`) as the decisive action/accent color.
- Graphite/near-black for governance and trust surfaces.
- White/light-grey operational surfaces for readability.
- Semantic green/amber/red reserved for actual state, not decoration.
- Consistent inline SVG icons so the finals UI works offline.

## Regular User
- one page, no sidebar;
- large question/answer hierarchy;
- safe-source treatment only;
- contradictions withheld by API contract;
- simple Helpful / Needs Review feedback;
- loading, empty, success, timeout and abstention states;
- no model confidence or evidence governance jargon.

## Superadmin information hierarchy
**Layer 1 — visible immediately**
- question under review;
- coverage and source boundary;
- support / contradiction / context counts;
- decision owner;
- concise Why Sources Disagree;
- publication controls.

**Layer 2 — evidence detail**
- source scope;
- approval/lifecycle status;
- authority;
- relevance;
- governance score;
- short reason for classification.

**Layer 3 — expandable/appendix**
- technical trace;
- context-only evidence;
- risk register/compliance mapping;
- complete audit ledger;
- Monte Carlo Digital Twin.

## Privacy UX
The Privacy & Data Security page visually shows:
`Approved group channel → relevance gate → PII/lifecycle gate → governed retrieval`
while PM/DM/1:1 content is visibly shown as blocked.

## Data-security UX
- Customer export has one clear primary action and a post-export integrity/audit manifest.
- System transfer shows TLS readiness, API-key/HMAC authentication, key fingerprint and a live self-test.
- Secrets are never displayed.

## Audit Evidence
Three slide-like proof sections make auditability presentation-friendly without placing the full ledger in the primary workflow.

## Accessibility / finals-room usability
- keyboard focus states;
- `aria-live` feedback;
- labelled controls;
- skip-to-content;
- responsive layouts;
- reduced-motion mode;
- high-contrast mode;
- projector-readable typography and touch/click targets.

No UI design can guarantee a score, but v11 is deliberately optimized around the rubric’s “production-grade / seamless / accessible” intent while protecting the simplicity of the lecturer-approved user flow.

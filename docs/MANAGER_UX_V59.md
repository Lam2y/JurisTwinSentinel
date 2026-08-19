# JurisTwin Sentinel v5.9 — Manager-First UX

This build keeps the v5.8 source-governance and security controls, but changes how they are presented to non-technical managers.

## Design rule

The main interface now answers four management questions first:

1. What should my team follow?
2. Where did that answer come from?
3. Is customer/private data protected?
4. Is it safe to approve and publish?

Engineering detail remains available through optional "Technical details" controls rather than dominating the primary workflow.

## Major UX changes

- Sidebar renamed to plain-language destinations: Why Sources Disagree, Compare Solutions, Safe to Publish?, Test New Evidence, Privacy & Security.
- A persistent trust strip is visible across the workspace: private DMs blocked, client data not used for AI training, role-based access, and live source checks.
- Ask JurisTwin now uses "Answer to follow", "Official source", "Privacy check" and "Up to date" instead of retrieval/authority jargon.
- Conflict view shows the official instruction, conflicting instruction, management action and customer impact before the evidence graph.
- Compare Solutions uses customer delay, complaint risk and process consistency as business-language priorities.
- Final approval explicitly explains why the publish button is locked and names the exact failed check.
- Assurance is presented as a management publication-readiness check; latency, runtime and other engineering metrics are hidden under technical details.
- Privacy & Security opens with four manager-facing guarantees before source controls, customer access, data transfer and audit history.
- Source configuration uses "Use for answers", "Can set official policy", "Always private" and "Never trains AI".
- Customer export controls explicitly state the current role and whether full export is blocked.
- Data-transfer controls are shown as a simple protected path, with TLS/HMAC/API-key implementation details collapsed underneath.
- Audit Log is reframed as "Who did what?" with person, action and outcome as the main columns.
- Evidence Lab is now "Test New Evidence" and presents a business conclusion before technical AI reasoning.
- Proof Pack is now "Audit proof for this decision" and leads with decision, customer impact, audit history and human authority; cryptographic fingerprints remain available on demand.

## Security controls retained

No security control was removed to simplify the UI. Server-side source scope, role-based customer exports, audit logging, signed live ingress, proof verification, governance gates and model publication restrictions remain enforced by the backend.

## Validation

- 57/57 automated tests pass.
- 32/32 industry preflight checks pass.
- JavaScript syntax check passes for both frontend source and served static copy.
- Frontend and backend static assets are synchronized.

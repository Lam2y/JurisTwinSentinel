# JurisTwin Sentinel Security Model

JurisTwin's finals build is designed to demonstrate **governed decision integrity**, not to claim bank-production certification.

Implemented controls include JWT authentication, role/capability checks, role-aware evidence redaction, HMAC-SHA256 connector authentication, replay-safe webhook handling, input bounds, write-safe frontend retry behavior, request IDs, rate containment, security headers, transaction rollback checks, an append-only SHA-256 ledger, and live adversarial self-tests. The JWT tamper control mutates a meaningful interior signature character so its result is independent of base64url padding and the machine-specific secret.

## Trust boundaries

1. Browser ↔ FastAPI: bearer token + input validation.
2. Machine connector ↔ webhook: HMAC-SHA256 signature + replay/idempotency handling.
3. New evidence ↔ canonical policy: quarantine by default; human governance required.
4. Decision publication ↔ operational cases: explicit approval + audit events.
5. Lower-privilege users ↔ restricted evidence: role-aware redaction and DLP policy.

## Demo versus production

The finals integration adapters and Digital Twin coefficients are explicitly labelled prototype-calibrated. A production deployment would add enterprise SSO/IdP, managed secrets/KMS, WAF/API gateway rate controls, centralized OpenTelemetry/SIEM, database migrations/HA/backups, signed build provenance, formal penetration testing, and vendor connector OAuth scopes.

See `docs/THREAT_MODEL.md` and `docs/CLAIMS_BOUNDARY.md`.


## Finals connector truthfulness

Vendor-branded integrations marked `deterministic_finals_adapter` are immutable fixtures and never fabricate new object counts. The `Signed Webhook Gateway` is the genuine HMAC-SHA256 live network ingress and increments only after an authenticated external POST.

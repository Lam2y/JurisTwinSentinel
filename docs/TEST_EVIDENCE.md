# Finals Test Evidence — v11

## Current automated result

**33 passed**

Run:

```bash
cd backend
python -m pytest -q
```

or use `preflight_finals.bat`.

## Coverage

### Core governed-answer workflow
- governed answer returns safe source lineage only;
- contradictory sources are excluded from the Regular User payload;
- unknown questions abstain and create a knowledge gap;
- semantic duplicate questions merge;
- Safe to Publish separates support, contradiction and context;
- publication creates reusable governed memory;
- paraphrases reuse governed memory;
- rollback disables reuse;
- source revalidation stops stale memory;
- canonical split-brain fails closed;
- misleading source attachment is rejected.

### Privacy and data security
- private/1:1 message ingestion is blocked and not persisted;
- irrelevant group-chat material is blocked;
- relevant group-channel evidence is accepted only as quarantined evidence with origin metadata;
- PII is masked before review persistence;
- encrypted customer export is Superadmin-only;
- AES-256-GCM export envelope decrypts correctly with the operator passphrase;
- plaintext customer payload does not appear in the encrypted file;
- API key is not exposed by the browser-facing security API;
- secure transfer rejects missing/wrong API keys and accepts valid API-key + HMAC + digest packets.

### Decision Digital Twin
- 1,500 scenarios execute across three options;
- robustness/Pareto/sensitivity output is generated;
- simulation is audit logged.

### Security / resilience / UX guards
- Regular User admin access is rejected;
- interaction ownership is checked;
- audit-chain tampering is detected;
- resilience self-test executes;
- retention enforcement executes;
- security headers/request limits remain active;
- accessibility hooks and required v11 UI controls are regression tested.

The suite is evidence that the implementation behaves as designed; it is not a guarantee of a competition score.

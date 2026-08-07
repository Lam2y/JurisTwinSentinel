# Prototype → Working Function Mapping

| Prototype screen/action | Working implementation |
|---|---|
| System Access | JWT login, PBKDF2 password verification, demo roles |
| Command Center | Live SQL aggregates over 128 cases and current conflict/security state |
| Investigate Income-Document Conflict | Opens case JT-2026-084 from database |
| Case Workspace timeline | SQL `case_events` + evidence records |
| Open Conflict Network Graph | Graph generated from conflict/evidence link table |
| Conflict Explanation | Persisted root cause + evidence-backed recommendation |
| Simulate Resolution Options | White-box intervention model with inspectable levers |
| Adjust Weights | Recomputes transparent weighted decision loss |
| Submit Scenario for Approval | Creates governed approval object |
| Approve & Publish Resolution | Resolves conflict, supersedes stale evidence, publishes Decision Contract, propagates to 27 cases, updates dashboard |
| Decision Ledger | Append-only SHA-256 hash chain with TXIDs |
| Registry integrity | `/api/ledger/verify` recalculates all links and hashes |
| AI Bodyguard | Safe simulated policy mutation with explainable reasons |
| Restore Approved Version | Resolves incident and appends restoration proof |
| Secure Enterprise Memory | Meaning search + RBAC + sensitivity redaction |
| Integrations | Persisted connector states + sync actions |
| Start Guided Demo | Server-defined finals storyline |
| Reset | Database wipe + deterministic reseed |

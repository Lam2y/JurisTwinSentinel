# Verification Report

Final verification performed on 7 August 2026.

```text
...                                                                      [100%]
3 passed in 0.92s
```

Validated flows:

- JWT login and deterministic reset.
- 128-case dashboard with 3 conflicts, 27 at-risk cases and 94 initially protected decisions.
- Flagship case timeline and seven-source evidence graph.
- White-box A/B/C simulation with Option C recommendation.
- Approval creates Decision Contract JT-084 and propagates to the affected cohort.
- Dashboard changes after approval (risk cleared, conflict count reduced, protected decisions increase).
- Complete SHA-256 ledger chain verifies after approval and after restoration.
- Bodyguard cannot be demonstrated before the governed decision exists.
- Intern restricted evidence is redacted at API/service level.


## v1.3 UI workflow validation
- Existing automated E2E suite: **3 passed**.
- New action smoke: `request-changes`, governed approve, Bodyguard `escalate`, `revoke-access`, `authorize-overwrite`, `restore`, and final ledger verification: **PASS**.
- JavaScript syntax (`node --check`): **PASS**.
- Python router compile check: **PASS**.

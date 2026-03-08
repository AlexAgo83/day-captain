## task_023_day_captain_weekend_window_and_reliability_orchestration - Orchestrate weekend digest horizon, weekday-only ops scheduling, and reliability hardening
> From version: 0.10.0
> Status: Ready
> Understanding: 99%
> Confidence: 99%
> Progress: 0%
> Complexity: High
> Theme: Reliability
> Reminder: Update status/understanding/confidence/progress and dependencies/references when you edit this doc.

# Context
- Derived from backlog items `item_015_day_captain_weekend_digest_window_from_friday`, `item_016_day_captain_isolation_and_delivery_reliability_hardening`, and `item_017_day_captain_ops_scheduler_weekday_only_delivery`.
- Source files:
  - `logics/backlog/item_015_day_captain_weekend_digest_window_from_friday.md`
  - `logics/backlog/item_016_day_captain_isolation_and_delivery_reliability_hardening.md`
  - `logics/backlog/item_017_day_captain_ops_scheduler_weekday_only_delivery.md`
- Related request(s): `req_015_day_captain_weekend_digest_window_from_friday`, `req_016_day_captain_isolation_and_delivery_reliability_hardening`, `req_017_day_captain_ops_scheduler_weekday_only_delivery`.
- Depends on: `task_022_day_captain_recall_and_delivery_evolution_orchestration`.
- Delivery target: close the newly reviewed reliability gaps first, then align weekend digest fallback behavior with the intended Friday-to-weekend recap, while keeping production ops scheduling explicitly weekday-only and without leaving README and operator docs behind the implementation.

```mermaid
flowchart LR
    Start[Current 0.10.0 state] --> Reliability[req 016 isolation and delivery reliability hardening]
    Reliability --> Weekend[req 015 weekend digest window from Friday]
    Weekend --> OpsPolicy[req 017 weekday-only ops scheduler]
    OpsPolicy --> Tests[Regression tests and hosted or operator validation]
    Tests --> Docs[README and operator docs updated]
    Docs --> Close[Close linked slices]
```

# Plan
- [ ] 1. Fix the isolation and retry-safety defects first so `run_id` actions and partial-failure behavior are trustworthy before expanding weekend digest semantics.
- [ ] 2. Implement the weekend first-run digest horizon so Saturday and Sunday fallback windows begin at Friday local midnight while repeated weekend runs stay incremental.
- [ ] 3. Freeze and validate the ops scheduler contract so scheduled delivery remains weekday-only even after weekend digest behavior is clarified.
- [ ] 4. Validate the combined behavior through automated regression tests and any needed ops-level scheduler semantics checks.
- [ ] 5. Update the README and the relevant operator/setup docs before closing the task; do not mark this task `Done` while the scheduler semantics and weekend digest horizon remain undocumented.
- [ ] FINAL: Update related Logics docs, statuses, and closure links across the linked requests and backlog items.

# AC Traceability
- Req016 AC1 -> Plan step 1. Proof: task explicitly fixes cross-user `run_id` recall before any product-behavior expansion.
- Req016 AC2 -> Plan step 1. Proof: task explicitly fixes cross-user `run_id` feedback in the same reliability tranche.
- Req016 AC3 -> Plan step 1. Proof: task explicitly hardens send/persist retry safety before closure.
- Req016 AC4 -> Plan step 1. Proof: task explicitly hardens email-command replay behavior under partial persistence failure.
- Req016 AC5 -> Plan steps 4 and 5. Proof: task explicitly validates and documents the chosen scheduler time semantics.
- Req016 AC6 -> Plan step 4. Proof: task explicitly requires regression validation for the reliability fixes.
- Req016 AC7 -> Plan step 5. Proof: task explicitly blocks closure until docs reflect the chosen production behavior.
- Req015 AC1 -> Plan step 2. Proof: task explicitly changes Saturday first-run fallback to Friday local midnight.
- Req015 AC2 -> Plan step 2. Proof: task explicitly changes Sunday first-run fallback to Friday local midnight.
- Req015 AC3 -> Plan step 2. Proof: task explicitly limits the behavior change to weekend fallback windows.
- Req015 AC4 -> Plan steps 1 and 2. Proof: task sequences continuity safety first, then weekend fallback changes without reopening old windows.
- Req015 AC5 -> Plan step 2. Proof: task explicitly leaves weekend Monday-meeting preview untouched.
- Req015 AC6 -> Plan step 4. Proof: task explicitly requires regression validation for weekend and repeated-run behavior.
- Req015 AC7 -> Plan step 5. Proof: task explicitly blocks completion until weekend horizon behavior is documented.
- Req017 AC1 -> Plan step 3. Proof: task explicitly freezes auto-send to weekdays only in the ops scheduler contract.
- Req017 AC2 -> Plan steps 2 and 3. Proof: task explicitly separates weekend digest content semantics from weekend auto-send policy.
- Req017 AC3 -> Plan step 5. Proof: task explicitly blocks closure until operator docs describe the weekday-only scheduling policy.
- Req017 AC4 -> Plan steps 3 and 4. Proof: task explicitly requires validation and operator-facing verification of the weekday-only policy.
- Documentation closure -> Plan step 5. Proof: task explicitly blocks `Done` until README and operator docs are updated.
- Workflow coherence -> Plan step 6. Proof: task explicitly requires linked Logics doc/status closure.

# Links
- Backlog item(s): `item_015_day_captain_weekend_digest_window_from_friday`, `item_016_day_captain_isolation_and_delivery_reliability_hardening`, `item_017_day_captain_ops_scheduler_weekday_only_delivery`
- Request(s): `req_015_day_captain_weekend_digest_window_from_friday`, `req_016_day_captain_isolation_and_delivery_reliability_hardening`, `req_017_day_captain_ops_scheduler_weekday_only_delivery`

# Validation
- python3 -m unittest discover -s tests
- python3 logics/skills/logics-doc-linter/scripts/logics_lint.py --require-status
- python3 logics/skills/logics-flow-manager/scripts/workflow_audit.py --group-by-doc

# Definition of Done (DoD)
- [ ] Reliability hardening for `run_id` isolation and partial-failure retry safety is implemented and validated.
- [ ] Weekend first-run digest fallback starts at Friday local midnight on Saturday and Sunday, while repeated runs remain incremental.
- [ ] Ops scheduler remains explicitly weekday-only for automatic sends.
- [ ] Scheduler time semantics and weekend digest behavior are documented before status moves to `Done`.
- [ ] Linked request/backlog/task docs are updated consistently.
- [ ] Status is `Done` and progress is `100%`.

# Report
- Created on Sunday, March 8, 2026 to group the next corrective slice after the latest review plus the newly requested weekend digest behavior.

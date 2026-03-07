## task_011_day_captain_meeting_horizon_fallbacks - Implement weekend and next-day meeting horizon fallbacks
> From version: 0.5.0
> Status: Done
> Understanding: 100%
> Confidence: 98%
> Progress: 100%
> Complexity: Medium
> Theme: Productivity
> Reminder: Update status/understanding/confidence/progress and dependencies/references when you edit this doc.

# Context
- Derived from backlog item `item_005_day_captain_meeting_horizon_fallbacks`.
- Source file: `logics/backlog/item_005_day_captain_meeting_horizon_fallbacks.md`.
- Related request(s): `req_005_day_captain_meeting_horizon_fallbacks`.
- Depends on: `task_002_day_captain_digest_scoring_recall_and_delivery`.
- Delivery target: make the `Upcoming meetings` section choose a more useful near-term day when the current digest day would otherwise provide poor calendar context.

```mermaid
flowchart LR
    Backlog[Backlog: `item_005_day_captain_meeting_horizon_fallbacks`] --> Step1[Define meeting-horizon fallback rules]
    Step1 --> Step2[Render explicit labels for fallback day selection]
    Step2 --> Step3[Validate json and graph_send outputs]
    Step3 --> Validation[Validation]
    Validation --> Report[Report and Done]
```

# Plan
- [x] 1. Implement weekend fallback so Saturday and Sunday digests display Monday meetings.
- [x] 2. Implement next-day fallback when the current digest day contains no meetings.
- [x] 3. Update rendered output so the section explicitly states when Monday or next-day fallback is being shown.
- [x] 4. Add focused tests for weekend fallback, empty-day fallback, and unchanged same-day behavior.
- [x] 5. Validate the updated digest contract for both `json` and `graph_send`.
- [x] FINAL: Update related Logics docs

# AC Traceability
- AC1 -> Plan step 1 implements weekend behavior. Proof: task explicitly requires Saturday/Sunday fallback to Monday.
- AC2 -> Plan step 3 implements explicit weekend labeling. Proof: task explicitly requires rendered wording for Monday fallback.
- AC3 -> Plan step 2 implements empty-day fallback. Proof: task explicitly requires choosing the next day when same-day meetings are absent.
- AC4 -> Plan step 3 implements explicit next-day labeling. Proof: task explicitly requires rendered wording for fallback day selection.
- AC5 -> Plan step 4 preserves unchanged same-day behavior. Proof: task explicitly requires coverage for the no-op case.
- AC6 -> Plan step 5 preserves delivery compatibility. Proof: task explicitly validates both supported delivery modes.
- AC7 -> Plan step 4 adds automated proof. Proof: task explicitly requires focused tests for each scenario.

# Links
- Backlog item: `item_005_day_captain_meeting_horizon_fallbacks`
- Request(s): `req_005_day_captain_meeting_horizon_fallbacks`

# Validation
- python3 -m unittest tests.test_scoring tests.test_digest_renderer tests.test_delivery_contract
- python3 -m unittest discover -s tests
- PYTHONPATH=src python3 -m day_captain morning-digest --now 2026-03-08T08:00:00+00:00 --force
- python3 logics/skills/logics-doc-linter/scripts/logics_lint.py --require-status
- python3 logics/skills/logics-flow-manager/scripts/workflow_audit.py --group-by-doc

# Definition of Done (DoD)
- [x] Scope implemented and acceptance criteria covered.
- [x] Validation commands executed and results captured.
- [x] Linked request/backlog/task docs updated.
- [x] Status is `Done` and progress is `100%`.

# Report
- Added meeting-horizon selection in `src/day_captain/app.py` so weekend runs preview Monday meetings and empty same-day windows fall back to the next day.
- Updated `src/day_captain/services.py` to render explicit fallback notes in the `Upcoming meetings` section and to keep the result compatible with both `json` and `graph_send`.
- Added focused coverage in `tests/test_app.py` and `tests/test_digest_renderer.py` for weekend fallback, empty-day fallback, and unchanged same-day behavior.
- Validation executed:
  - `python3 -m unittest tests.test_scoring tests.test_digest_renderer tests.test_delivery_contract`
  - `python3 -m unittest discover -s tests`
  - `PYTHONPATH=src python3 -m day_captain morning-digest --delivery-mode graph_send --force`
- Real delivered validation on Saturday, March 7, 2026 confirmed the digest explicitly said `Looking ahead to Monday.` and included Monday meetings instead of an empty section.

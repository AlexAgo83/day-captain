## task_042_day_captain_unread_mail_indicators_received_time_display_and_9am_daily_schedule - Day Captain unread mail indicators received time display and 9am daily schedule
> From version: 1.7.0
> Status: Done
> Understanding: 100%
> Confidence: 96%
> Progress: 100%
> Complexity: Medium
> Theme: UX
> Reminder: Update status/understanding/confidence/progress and dependencies/references when you edit this doc.

# Context
- Derived from backlog item `item_080_day_captain_unread_mail_indicators_received_time_display_and_9am_daily_schedule`.
- Source file: `logics/backlog/item_080_day_captain_unread_mail_indicators_received_time_display_and_9am_daily_schedule.md`.
- Related request(s): `req_037_day_captain_unread_mail_indicators_received_time_display_and_9am_daily_schedule`.
- Delivery target: expose mail read state and received-time metadata in the digest while shifting the supported default daily scheduler time to `09:00 Europe/Paris`.

```mermaid
flowchart LR
    Metadata[Mail metadata rendering] --> Scheduler[Scheduler default update]
    Scheduler --> Validation[Tests, docs, validation]
    Validation --> Report[Report and Done]
```

# Plan
- [x] 1. Confirm the mail metadata contract, including unread/read-state availability and received-time formatting in the effective display timezone.
- [x] 2. Add the digest rendering changes needed to show a compact unread/read-state cue and low-prominence received-time metadata without hiding already read but still relevant emails.
- [x] 3. Update the repository-defined default daily schedule to `09:00 Europe/Paris` wherever that contract is implemented or documented.
- [x] FINAL: Run regression checks, update the linked Logics docs, and capture validation results.

# AC Traceability
- Req037 AC1 -> Plan step 2. Proof: visible read-state metadata is part of the rendering step.
- Req037 AC2 -> Plan step 2. Proof: the same step explicitly preserves resurfacing eligibility for already read but relevant emails.
- Req037 AC3 -> Plan steps 1 and 2. Proof: received-time formatting is confirmed first and then exposed in rendering.
- Req037 AC4 -> Plan step 3. Proof: the scheduler default shift is isolated as its own implementation step.
- Req037 AC5 -> FINAL. Proof: tests and docs are explicit closure requirements.

# Decision framing
- Product framing: Not needed
- Product signals: (none detected)
- Product follow-up: No product brief follow-up is expected based on current signals.
- Architecture framing: Consider
- Architecture signals: contracts and integration
- Architecture follow-up: Review whether an architecture decision is needed before implementation becomes harder to reverse.

# Links
- Product brief(s): (none yet)
- Architecture decision(s): (none yet)
- Backlog item: `item_080_day_captain_unread_mail_indicators_received_time_display_and_9am_daily_schedule`
- Request(s): `req_037_day_captain_unread_mail_indicators_received_time_display_and_9am_daily_schedule`

# Validation
- python3 -m unittest discover -s tests
- python3 logics/skills/logics-doc-linter/scripts/logics_lint.py --require-status
- python3 logics/skills/logics-flow-manager/scripts/workflow_audit.py --group-by-doc

# Definition of Done (DoD)
- [x] Scope implemented and acceptance criteria covered.
- [x] Validation commands executed and results captured.
- [x] Linked request/backlog/task docs updated.
- [x] Status is `Done` and progress is `100%`.

# Report
- Created on Wednesday, March 18, 2026 from user feedback about unread visibility, mail received-time hints, and a later weekday digest run.
- Completed on Wednesday, March 18, 2026.
- Implemented:
  - added visible unread/read state plus received-time metadata to surfaced mail items in text and HTML digest rendering
  - preserved surfacing of already read but still relevant emails while making unread items easier to spot
  - shifted the supported weekday scheduler default to `09:00 Europe/Paris` through a timezone-aware morning gate shared by the repo and ops templates
  - updated scheduler and rendering docs to reflect the new metadata and scheduling contract
- Validation:
  - `python3 -m unittest tests.test_digest_renderer tests.test_scheduler tests.test_scheduler_templates`
  - `python3 -m unittest discover -s tests`
  - `python3 logics/skills/logics-doc-linter/scripts/logics_lint.py --require-status`
  - `python3 logics/skills/logics-flow-manager/scripts/workflow_audit.py --group-by-doc`

## task_013_day_captain_digest_header_and_subject_polish - Improve digest header copy and inbox subject wording
> From version: 0.5.0
> Status: Done
> Understanding: 100%
> Confidence: 98%
> Progress: 100%
> Complexity: Medium
> Theme: Quality
> Reminder: Update status/understanding/confidence/progress and dependencies/references when you edit this doc.

# Context
- Derived from backlog item `item_007_day_captain_mailbox_tone_and_copy_polish`.
- Source file: `logics/backlog/item_007_day_captain_mailbox_tone_and_copy_polish.md`.
- Related request(s): `req_007_day_captain_mailbox_tone_and_copy_polish`.
- Depends on: `task_008_day_captain_email_rendering_and_formatting_upgrade`, `task_006_day_captain_graph_send_delivery_execution`.
- Delivery target: make the first impression of the digest feel less like a report export and more like a user-facing morning brief.

```mermaid
flowchart LR
    Backlog[Backlog source 007 day captain mailbox tone and copy polish] --> Step1[Rewrite header and metadata copy]
    Step1 --> Step2[Improve inbox subject line wording]
    Step2 --> Step3[Validate delivered appearance in mailbox]
    Step3 --> Validation[Validation]
    Validation --> Report[Report and Done]
```

# Plan
- [x] 1. Replace technical header labels and metadata phrasing with more natural assistant-style copy.
- [x] 2. Improve the email subject line so it reads naturally in the inbox while remaining stable and clear.
- [x] 3. Ensure the updated subject and header behave consistently in both `json` and `graph_send`.
- [x] 4. Validate the updated output on a real delivered digest.
- [x] FINAL: Update related Logics docs

# AC Traceability
- AC1 -> Plan step 1 improves header and metadata tone. Proof: task explicitly rewrites technical phrasing.
- AC2 -> Plan step 2 improves inbox subject wording. Proof: task explicitly upgrades the delivered subject line.
- AC5 -> Plan step 4 validates mailbox quality. Proof: task explicitly requires real delivered review.
- AC6 -> Plan step 3 preserves delivery compatibility. Proof: task explicitly keeps both supported delivery modes aligned.
- AC8 -> This task is one part of the mailbox tone decomposition. Proof: the request explicitly splits the polish slice into header/subject and copy/empty-state tasks, including this one.

# Links
- Backlog item: `item_007_day_captain_mailbox_tone_and_copy_polish`
- Request(s): `req_007_day_captain_mailbox_tone_and_copy_polish`

# Validation
- python3 -m unittest tests.test_digest_renderer tests.test_delivery_contract
- python3 -m unittest discover -s tests
- PYTHONPATH=src python3 -m day_captain morning-digest --delivery-mode graph_send --force
- python3 logics/skills/logics-doc-linter/scripts/logics_lint.py --require-status
- python3 logics/skills/logics-flow-manager/scripts/workflow_audit.py --group-by-doc

# Definition of Done (DoD)
- [x] Scope implemented and acceptance criteria covered.
- [x] Validation commands executed and results captured.
- [x] Linked request/backlog/task docs updated.
- [x] Status is `Done` and progress is `100%`.

# Report
- Replaced system-like header copy with assistant-style wording in `src/day_captain/services.py`, including new title, preparation line, and coverage line.
- Updated the delivered inbox subject from the utilitarian digest subject to a more natural brief-style subject while preserving stable date context.
- Added coverage in `tests/test_digest_renderer.py` and `tests/test_app.py` for the updated header and subject behavior.
- Validation executed:
  - `python3 -m unittest tests.test_digest_renderer tests.test_delivery_contract`
  - `python3 -m unittest discover -s tests`
  - `PYTHONPATH=src python3 -m day_captain morning-digest --delivery-mode graph_send --force`
- Real delivered validation confirmed the subject and header now read as a user-facing brief instead of an internal report export.

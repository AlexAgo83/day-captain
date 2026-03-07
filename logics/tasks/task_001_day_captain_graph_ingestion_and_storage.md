## task_001_day_captain_graph_ingestion_and_storage - Implement Microsoft Graph ingestion and SQLite persistence
> From version: 0.1.0
> Status: In Progress
> Understanding: 99%
> Confidence: 97%
> Progress: 98%
> Complexity: High
> Theme: Productivity
> Reminder: Update status/understanding/confidence/progress and dependencies/references when you edit this doc.

# Context
- Derived from backlog item `item_000_day_captain_daily_assistant_for_microsoft_365`.
- Source file: `logics/backlog/item_000_day_captain_daily_assistant_for_microsoft_365.md`.
- Related request(s): `req_000_day_captain_daily_assistant_for_microsoft_365`.
- Supporting spec: `spec_000_day_captain_v1_digest_contract`.
- Depends on: `task_000_day_captain_daily_assistant_for_microsoft_365`.
- Delivery target: implement delegated Graph collection and idempotent `SQLite` persistence for normalized mail, meetings, digest runs, and feedback primitives.

```mermaid
flowchart LR
    Backlog[Backlog: `item_000_day_captain_daily_assistant_for_microsoft_365`] --> Step1[Implement delegated Graph auth and collectors]
    Step1 --> Step2[Normalize and persist mail, meetings, and run state in SQLite]
    Step2 --> Step3[Add fixtures, retry/error handling, and ingestion tests]
    Step3 --> Validation[Validation]
    Validation --> Report[Report and Done]
```

# Plan
- [x] 1. Implement delegated Graph auth/config plus mail and calendar collectors for the frozen V1 time window.
- [x] 2. Normalize Graph payloads and persist messages, meetings, digest runs, digest items, and preference/feedback primitives in `SQLite` with idempotent writes.
- [x] 3. Add fixtures, pagination/error handling, and tests for normalization, deduplication, repeated runs, and stored run metadata.
- [x] FINAL: Update related Logics docs

# AC Traceability
- AC1 -> This task implements the selected Graph auth mode. Proof: Plan step 1 adds delegated auth/config handling.
- AC2 -> This task implements morning collection and persisted run state. Proof: Plan steps 1 and 2 collect the fixed window and write normalized records to `SQLite`.
- AC6 -> This task establishes the system of record. Proof: Plan step 2 persists source entities, run metadata, and feedback primitives.
- AC7 -> This task respects the agreed architecture boundary. Proof: Plan step 1 keeps Graph access in Python and leaves orchestration external.

# Links
- Backlog item: `item_000_day_captain_daily_assistant_for_microsoft_365`
- Request(s): `req_000_day_captain_daily_assistant_for_microsoft_365`
- Spec: `spec_000_day_captain_v1_digest_contract`

# Validation
- python3 -m unittest tests.test_graph_client tests.test_storage tests.test_morning_run
- python3 -m unittest discover -s tests
- PYTHONPATH=src python3 -m day_captain morning-digest --now 2026-03-07T08:00:00+00:00 --force
- python3 logics/skills/logics-doc-linter/scripts/logics_lint.py --require-status
- python3 logics/skills/logics-flow-manager/scripts/workflow_audit.py --group-by-doc

# Definition of Done (DoD)
- [x] Scope implemented and acceptance criteria covered.
- [x] Validation commands executed and results captured.
- [x] Linked request/backlog/task docs updated.
- [ ] Status is `Done` and progress is `100%`.

# Report
- Added `SQLiteStorage` in `src/day_captain/adapters/storage.py` with schema bootstrap, idempotent upserts for messages and meetings, persisted digest runs/items, and feedback persistence.
- Added Microsoft Graph adapters in `src/day_captain/adapters/graph.py` for delegated bearer-token auth, `/me` profile resolution, `/me/messages` ingestion, `/me/calendar/calendarView` ingestion, pagination support, and HTTP error surfacing.
- Added Microsoft Entra ID device-code auth support in `src/day_captain/adapters/auth.py`, plus token-cache-backed delegated auth and refresh handling in the Graph provider and CLI.
- Updated `build_application()` so `SQLite` is the default storage backend and Graph adapters activate automatically when `DAY_CAPTAIN_GRAPH_ACCESS_TOKEN` is configured.
- Added coverage in `tests/test_graph_client.py`, `tests/test_storage.py`, `tests/test_morning_run.py`, and `tests/test_auth.py`.
- Workflow note: the implementation slice is complete, but the task remains `In Progress` until the parent backlog item can close under the repo's workflow audit rules.
- Validation results:
  - `python3 -m unittest discover -s tests` -> `OK` (`23` tests)
  - `PYTHONPATH=src python3 -m day_captain auth status` -> returned a valid unauthenticated cache status payload
  - `PYTHONPATH=src python3 -m day_captain morning-digest --now 2026-03-07T08:00:00+00:00 --force` -> returned a valid digest payload backed by default `SQLite` storage

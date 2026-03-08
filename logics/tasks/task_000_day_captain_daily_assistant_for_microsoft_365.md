## task_000_day_captain_daily_assistant_for_microsoft_365 - Freeze Day Captain V1 contract and bootstrap the service skeleton
> From version: 0.1.0
> Status: In Progress
> Understanding: 100%
> Confidence: 97%
> Progress: 96%
> Complexity: Medium
> Theme: Productivity
> Reminder: Update status/understanding/confidence/progress and dependencies/references when you edit this doc.

# Context
- Derived from backlog item `item_000_day_captain_daily_assistant_for_microsoft_365`.
- Source file: `logics/backlog/item_000_day_captain_daily_assistant_for_microsoft_365.md`.
- Related request(s): `req_000_day_captain_daily_assistant_for_microsoft_365`.
- Supporting spec: `spec_000_day_captain_v1_digest_contract`.
- Delivery target: remove ambiguity before implementation by freezing the auth model, data contracts, entrypoints, service module boundaries, and local-vs-hosted deployment assumptions, then bootstrap the minimal Python project skeleton those later tasks will extend.

```mermaid
flowchart LR
    Backlog[Backlog source 000 day captain daily assistant for microsoft 365] --> Step1[Freeze auth window digest and storage contracts]
    Step1 --> Step2[Bootstrap Python package config and service interfaces]
    Step2 --> Step3[Add local run entrypoints smoke tests and linked doc updates]
    Step3 --> Validation[Validation]
    Validation --> Report[Report and Done]
```

# Plan
- [x] 1. Freeze the V1 contract: delegated Graph auth, morning collection window, digest JSON/email schema, local `SQLite` tables plus hosted Postgres-compatible schema expectations, recall contract, and Render/GitHub Actions/Python responsibilities.
- [x] 2. Bootstrap the Python project skeleton with configuration loading, service interfaces, normalized DTOs, and placeholders for auth, collection, storage, scoring, digest, recall, and feedback modules.
- [x] 3. Add local run entrypoints, smoke-test scaffolding, and implementation notes that unblock `task_001_day_captain_graph_ingestion_and_storage` and `task_002_day_captain_digest_scoring_recall_and_delivery`.
- [x] FINAL: Update related Logics docs

# AC Traceability
- AC1 -> This task freezes the auth model. Proof: Plan step 1 defines delegated Graph auth and required scopes.
- AC2 -> This task freezes the collection and persistence contracts. Proof: Plan step 1 defines the morning window and `SQLite` tables; step 2 adds the corresponding interfaces.
- AC3 -> This task freezes the digest contract. Proof: Plan step 1 defines the digest schema and step 2 adds normalized DTOs.
- AC6 -> This task bootstraps persistence boundaries. Proof: Plan steps 1 and 2 define and scaffold `SQLite` repositories.
- AC7 -> This task makes the service boundary explicit. Proof: Plan step 1 defines the Render/GitHub Actions vs Python split and step 2 creates module placeholders.
- AC8 -> This task creates the first runnable integration surface. Proof: Plan step 3 adds local run entrypoints compatible with later hosted wiring.

# Links
- Backlog item: `item_000_day_captain_daily_assistant_for_microsoft_365`
- Request(s): `req_000_day_captain_daily_assistant_for_microsoft_365`
- Spec: `spec_000_day_captain_v1_digest_contract`

# Validation
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
- Added the initial Python project metadata in `pyproject.toml` and the `src/day_captain/` package skeleton.
- Added typed settings/config loading, domain models, and service interfaces for auth, collectors, storage, scoring, digest rendering, recall, and feedback.
- Added stub adapters plus application entrypoints for `run_morning_digest`, `recall_digest`, and `record_feedback`, with a CLI exposed through `python -m day_captain` / `day-captain`.
- Added smoke coverage in `tests/test_settings.py` and `tests/test_app.py`.
- Added GitHub Actions CI in `.github/workflows/ci.yml` to run install, unit tests, CLI smoke test, Logics lint, and workflow audit on push/PR across Python `3.9` and `3.11`.
- Workflow note: the implementation slice is complete, but the task remains `In Progress` until the parent backlog item can close under the repo's workflow audit rules.
- Validation results:
  - `python3 -m unittest discover -s tests` -> `OK` (`4` tests)
  - `PYTHONPATH=src python3 -m day_captain morning-digest --now 2026-03-07T08:00:00+00:00 --force` -> returned an empty but valid digest payload

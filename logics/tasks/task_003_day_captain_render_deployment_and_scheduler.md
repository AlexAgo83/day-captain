## task_003_day_captain_render_deployment_and_scheduler - Deploy Day Captain on Render with GitHub Actions scheduling
> From version: 0.1.0
> Status: Ready
> Understanding: 97%
> Confidence: 95%
> Progress: 0%
> Complexity: High
> Theme: Productivity
> Reminder: Update status/understanding/confidence/progress and dependencies/references when you edit this doc.

# Context
- Derived from backlog item `item_000_day_captain_daily_assistant_for_microsoft_365`.
- Source file: `logics/backlog/item_000_day_captain_daily_assistant_for_microsoft_365.md`.
- Related request(s): `req_000_day_captain_daily_assistant_for_microsoft_365`.
- Supporting spec: `spec_000_day_captain_v1_digest_contract`.
- Depends on: `task_000_day_captain_daily_assistant_for_microsoft_365`, `task_001_day_captain_graph_ingestion_and_storage`, `task_002_day_captain_digest_scoring_recall_and_delivery`.
- Delivery target: make the current single-user Day Captain implementation operable as a hosted V1 using Render for runtime, GitHub Actions for the morning trigger, Microsoft Graph for ingestion/send, and Postgres-backed persistence in hosted mode.

```mermaid
flowchart LR
    Backlog[Backlog: `item_000_day_captain_daily_assistant_for_microsoft_365`] --> Step1[Prepare hosted config, secrets, and Postgres-backed persistence]
    Step1 --> Step2[Add Render deployment assets and HTTP-triggered service entrypoint]
    Step2 --> Step3[Add GitHub Actions scheduler and hosted smoke checks]
    Step3 --> Validation[Validation]
    Validation --> Report[Report and Done]
```

# Plan
- [ ] 1. Add hosted configuration boundaries for Render deployment, including env-var contracts, secret expectations, and a Postgres-backed persistence path that preserves current run/digest/feedback behavior.
- [ ] 2. Add deployment assets and a hosted trigger surface for Render, such as a `render.yaml`, web-service entrypoint, and authenticated webhook/job endpoint for morning digest execution.
- [ ] 3. Add a GitHub Actions scheduled workflow that securely triggers the hosted service and records success/failure without exposing mailbox payloads.
- [ ] FINAL: Update related Logics docs

# AC Traceability
- AC2 -> This task makes the hosted morning run executable. Proof: Plan steps 1 and 2 wire the existing collection window and storage behavior into a hosted service.
- AC6 -> This task hardens hosted persistence. Proof: Plan step 1 adds a Postgres-backed persistence path compatible with local `SQLite` contracts.
- AC7 -> This task fixes the deployment boundary. Proof: Plan step 2 defines Render-owned runtime concerns while Python keeps business logic.
- AC8 -> This task implements the selected first deployment path. Proof: Plan steps 2 and 3 add Render hosting plus GitHub Actions scheduling.

# Links
- Backlog item: `item_000_day_captain_daily_assistant_for_microsoft_365`
- Request(s): `req_000_day_captain_daily_assistant_for_microsoft_365`
- Spec: `spec_000_day_captain_v1_digest_contract`

# Validation
- python3 -m unittest discover -s tests
- PYTHONPATH=src python3 -m day_captain morning-digest --now 2026-03-07T08:00:00+00:00 --force
- render blueprint validation or equivalent config check
- GitHub Actions workflow lint or dry-run validation
- python3 logics/skills/logics-doc-linter/scripts/logics_lint.py --require-status
- python3 logics/skills/logics-flow-manager/scripts/workflow_audit.py --group-by-doc

# Definition of Done (DoD)
- [ ] Scope implemented and acceptance criteria covered.
- [ ] Validation commands executed and results captured.
- [ ] Linked request/backlog/task docs updated.
- [ ] Status is `Done` and progress is `100%`.

# Report
- Pending implementation.

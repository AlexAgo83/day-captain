## task_048_day_captain_technical_debt_hardening_orchestration - Day Captain technical debt hardening orchestration
> From version: 1.9.3
> Schema version: 1.0
> Status: Draft
> Understanding: 95%
> Confidence: 90%
> Progress: 0%
> Complexity: Medium
> Theme: Engineering Quality
> Reminder: Update status/understanding/confidence/progress and dependencies/references when you edit this doc.

# Context
- Derived from backlog items `item_100` through `item_105`, all owned by `req_053_day_captain_technical_debt_and_runtime_hardening`.
- Six independent engineering quality improvements identified in the April 2026 codebase audit. They share no product-visible behavior change and can be delivered as a single hardening wave.
- Recommended delivery order (lowest risk first):
  1. SQL pattern cleanup (`item_103`) — mechanical, zero behavioral risk
  2. Python 3.11 migration (`item_100`) — CI-only, no application change
  3. Coverage reporting (`item_101`) — CI tooling addition
  4. Rate limiting (`item_104`) — new HTTP behavior, well-bounded scope
  5. Connection pooling (`item_105`) — storage lifecycle change, medium complexity
  6. services.py decomposition (`item_102`) — highest complexity, do last when CI is green and coverage is measured

```mermaid
%% logics-kind: task
%% logics-signature: task|day-captain-technical-debt-hardening-orc|item-100-day-captain-python-3-9-eol-migr|1-sql-format-cleanup-item-103|pythonpath-src-python3-m-unittest-discov
flowchart TD
    Inputs[item 100-105 technical debt audit] --> Step1[1. SQL .format cleanup item 103]
    Step1 --> Step2[2. Python 3.11 migration item 100]
    Step2 --> Step3[3. Coverage reporting in CI item 101]
    Step3 --> Step4[4. Rate limiting on job endpoints item 104]
    Step4 --> Step5[5. PostgreSQL connection pooling item 105]
    Step5 --> Step6[6. services.py decomposition item 102]
    Step6 --> Validation[Run full test suite and lint]
    Validation --> Close[Update linked Logics docs and close wave]
```

# Plan
- [ ] 1. SQL `.format()` cleanup (`item_103`): locate all `.format()` SQL calls in `storage.py`, replace with explicit constants or literal clause builders, verify all tests pass.
- [ ] CHECKPOINT: commit SQL cleanup wave.
- [ ] 2. Python 3.11 migration (`item_100`): raise `python_requires` in `pyproject.toml`, drop Python 3.9 from CI matrix, verify CI passes on 3.11 and 3.12.
- [ ] CHECKPOINT: commit Python version bump.
- [ ] 3. Coverage reporting (`item_101`): integrate `coverage.py` into CI test run, emit summary, define minimum threshold in `pyproject.toml`.
- [ ] CHECKPOINT: commit CI coverage integration.
- [ ] 4. Rate limiting (`item_104`): implement in-memory fixed-window limiter in `web.py`, add env var config and `.env.example` entries, add tests for 429 and window-reset paths.
- [ ] CHECKPOINT: commit rate limiting wave.
- [ ] 5. PostgreSQL connection pooling (`item_105`): implement connection reuse within a job run in `storage.py`, add lifecycle tests, verify SQLite is unaffected.
- [ ] CHECKPOINT: commit connection pooling wave.
- [ ] 6. services.py decomposition (`item_102`): identify functions exceeding 150 lines, extract focused helpers, verify all existing tests pass unchanged, add unit tests for three largest extracted helpers.
- [ ] CHECKPOINT: commit decomposition wave.
- [ ] FINAL: Run full validation suite, update all linked Logics docs, close backlog items and request.

# Delivery checkpoints
- Each wave should leave the repository in a coherent, commit-ready state.
- Update the linked Logics docs during the wave that changes the behavior, not only at final closure.
- Prefer a reviewed commit checkpoint at the end of each meaningful wave instead of accumulating several undocumented partial states.

# AC Traceability
- Req053 AC1 → Plan step 2. Proof: Python version gate and CI matrix are owned by item_100.
- Req053 AC2 → Plan step 3. Proof: coverage reporting is owned by item_101.
- Req053 AC3 → Plan step 6. Proof: services.py decomposition contract is owned by item_102.
- Req053 AC4 → Plan step 1. Proof: SQL pattern safety is owned by item_103.
- Req053 AC5 → Plan step 4. Proof: rate limiting contract is owned by item_104.
- Req053 AC6 → Plan step 5. Proof: connection lifecycle contract is owned by item_105.

# Decision framing
- Product framing: Not needed
- Architecture framing: Not needed — all six items are implementation-level improvements within existing module and deployment boundaries.

# Links
- Product brief(s): (none yet)
- Architecture decision(s): (none yet)
- Backlog item: `item_100_day_captain_python_3_9_eol_migration_to_3_11`, `item_101_day_captain_ci_coverage_reporting`, `item_102_day_captain_services_decomposition_large_functions`, `item_103_day_captain_replace_format_based_sql_construction_in_storage`, `item_104_day_captain_rate_limiting_on_job_endpoints`, `item_105_day_captain_postgresql_connection_pooling_in_storage_adapter`
- Request(s): `req_053_day_captain_technical_debt_and_runtime_hardening`

# AI Context
- Summary: Orchestrate the six technical debt and runtime hardening items from the April 2026 audit in a single wave: SQL cleanup, Python 3.11, coverage reporting, rate limiting, connection pooling, and services.py decomposition.
- Keywords: technical debt, python 3.11, coverage, SQL format, rate limiting, connection pooling, services decomposition, orchestration
- Use when: Use when executing any of the six engineering quality improvements from req_053.
- Skip when: Skip when the work targets product features, digest logic, or delivery behavior.

# Validation
- `PYTHONPATH=src python3 -m unittest discover -s tests`
- `python3 logics/skills/logics-doc-linter/scripts/logics_lint.py --require-status`

# Definition of Done (DoD)
- [ ] Scope implemented and acceptance criteria covered.
- [ ] Validation commands executed and results captured.
- [ ] Linked request/backlog/task docs updated during completed waves and at closure.
- [ ] Each completed wave left a commit-ready checkpoint or an explicit exception is documented.
- [ ] Status is `Done` and progress is `100%`.

# Report

## item_105_day_captain_postgresql_connection_pooling_in_storage_adapter - Day Captain PostgreSQL connection pooling in storage adapter
> From version: 1.9.3
> Schema version: 1.0
> Status: Draft
> Understanding: 90%
> Confidence: 88%
> Progress: 0%
> Complexity: Medium
> Theme: Engineering Quality
> Reminder: Update status/understanding/confidence/progress and linked task references when you edit this doc.

# Problem
- The storage adapter opens a new PostgreSQL connection for each operation within a job run, creating per-query TCP handshake overhead and risking connection limit exhaustion under concurrent multi-user load.
- On Render's starter PostgreSQL tier the default connection limit is low (typically 25); multiple simultaneous digest runs can approach this ceiling.
- SQLite is unaffected (file-based, no TCP overhead) and must not be changed by this item.

# Scope
- In:
  - introduce a connection reuse strategy for the PostgreSQL adapter within the lifetime of a single job run (e.g. pass a single connection through the call chain, or use `psycopg`'s connection pool for the process)
  - ensure connections are closed or returned to the pool on job completion and on all error paths
  - SQLite adapter behavior must remain unchanged
  - add tests for connection lifecycle: opened once per run, closed on completion, closed on exception
- Out:
  - connection pooling across concurrent HTTP requests (gunicorn worker isolation makes this complex; defer to a later item)
  - changing the storage protocol or adapter interface signature visible to `app.py`
  - upgrading the `psycopg` dependency version

```mermaid
%% logics-kind: backlog
%% logics-signature: backlog|day-captain-postgresql-connection-poolin|req-053-day-captain-technical-debt-and-r|the-storage-adapter-opens-a-new|ac1-the-postgresql-storage-adapter-opens
flowchart LR
    Request[Req 053 technical debt] --> Problem[New PG connection per operation]
    Problem --> Scope[Reuse connection within job run]
    Scope --> Acceptance[AC1 single connection per job run]
    Acceptance --> Tasks[Execution task]
```

# Acceptance criteria
- AC1: The PostgreSQL storage adapter opens at most one connection per job run and reuses it across all operations within that run.
- AC2: The connection is explicitly closed (or returned to pool) when the job run completes, including on error paths.
- AC3: SQLite adapter behavior is unchanged — no regression on local or test runs.
- AC4: Tests verify that the connection is opened once and closed on both happy path and exception path.
- AC5: The storage adapter interface (ports protocol) requires no changes; callers in `app.py` are unaffected.

# AC Traceability
- Req053 AC6 → AC1, AC2, AC3, AC5. Proof: this item owns the PostgreSQL connection lifecycle contract.

# Decision framing
- Product framing: Not needed
- Architecture framing: Low signal — connection reuse is a well-understood pattern in `psycopg3`; no new architectural decision required.

# Links
- Product brief(s): (none yet)
- Architecture decision(s): (none yet)
- Request: `req_053_day_captain_technical_debt_and_runtime_hardening`
- Primary task(s): (orchestration task to be linked)

# AI Context
- Summary: Reuse a single PostgreSQL connection per job run in the storage adapter instead of opening a new connection per operation; ensure clean close on completion and error.
- Keywords: connection pooling, PostgreSQL, psycopg, storage adapter, connection lifecycle, TCP overhead
- Use when: Work targets the PostgreSQL connection model in the storage adapter.
- Skip when: Work targets SQLite, query logic, schema, or delivery.

# References
- Storage adapter: [adapters/storage.py](src/day_captain/adapters/storage.py)
- Ports protocol: [ports.py](src/day_captain/ports.py)
- Application orchestration: [app.py](src/day_captain/app.py)

# Priority
- Impact: Medium — reduces DB connection overhead and prevents limit exhaustion under multi-user load.
- Urgency: Low — no immediate limit hit observed; risk grows as tenant count increases.

# Notes
- Derived from `req_053_day_captain_technical_debt_and_runtime_hardening`.
- Evaluate whether the existing `psycopg[binary]` dependency is sufficient or whether `psycopg-pool` needs to be added as an optional extra.

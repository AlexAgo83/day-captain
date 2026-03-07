# Day Captain

Day Captain is a Python service that builds a daily Microsoft 365 digest from Outlook mail and calendar data.

It currently supports:
- delegated Microsoft Graph auth through Microsoft Entra ID device code flow
- message and meeting ingestion from Graph
- deterministic scoring and anti-noise filtering
- optional bounded LLM wording on shortlisted digest items with deterministic fallback
- digest generation with `critical_topics`, `actions_to_take`, `watch_items`, and `upcoming_meetings`
- persisted runs, feedback, and preferences
- local CLI usage
- a minimal hosted HTTP surface for Render

## Project status

Current package version: `0.3.0`

This repository is in active development. The core digest flow works locally and against a real Microsoft 365 mailbox. The hosted Render path is scaffolded, and a dedicated hardening track exists in Logics before treating it as production-ready.

## Repository layout

- `src/day_captain/`: application code
- `tests/`: unit and integration-style tests
- `logics/`: request, backlog, specs, and task tracking
- `render.yaml`: Render deployment blueprint
- `.github/workflows/`: CI and scheduled trigger workflows

## Core components

- `config.py`: environment-driven settings
- `app.py`: application assembly and main digest flow
- `adapters/auth.py`: Microsoft Entra device code auth and token cache
- `adapters/graph.py`: Microsoft Graph mail/calendar adapters
- `adapters/storage.py`: `SQLite` and Postgres-backed persistence
- `services.py`: scoring, filtering, digest rendering, recall, and feedback logic
- `web.py`: hosted HTTP endpoints for health, morning digest, and recall
- `cli.py`: command-line entrypoints

## Requirements

- Python `3.9+`
- a Microsoft Entra app registration for Graph delegated auth
- Graph delegated permissions:
  - `User.Read`
  - `Mail.Read`
  - `Calendars.Read`
  - optionally `Mail.Send`

## Installation

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

## Configuration

Start from [`.env.example`](./.env.example).

Local development typically uses:

```env
DAY_CAPTAIN_ENV=development
DAY_CAPTAIN_SQLITE_PATH=day_captain.sqlite3
DAY_CAPTAIN_DELIVERY_MODE=json
DAY_CAPTAIN_GRAPH_TENANT_ID=common
DAY_CAPTAIN_GRAPH_CLIENT_ID=your-app-client-id
DAY_CAPTAIN_GRAPH_AUTH_CACHE_PATH=.day_captain_auth.json
DAY_CAPTAIN_GRAPH_SCOPES=User.Read,Mail.Read,Calendars.Read
DAY_CAPTAIN_LLM_PROVIDER=disabled
DAY_CAPTAIN_LLM_MODEL=
DAY_CAPTAIN_LLM_API_KEY=
```

Hosted deployment typically uses:

```env
DAY_CAPTAIN_ENV=production
DAY_CAPTAIN_DATABASE_URL=postgresql://...
DAY_CAPTAIN_JOB_SECRET=...
DAY_CAPTAIN_DELIVERY_MODE=graph_send
DAY_CAPTAIN_GRAPH_CLIENT_ID=...
DAY_CAPTAIN_GRAPH_TENANT_ID=...
DAY_CAPTAIN_LLM_PROVIDER=openai
DAY_CAPTAIN_LLM_MODEL=gpt-5-mini
DAY_CAPTAIN_LLM_API_KEY=...
```

Important:
- never commit `.env`
- never commit Graph access or refresh tokens
- never commit LLM API keys
- local token cache and local databases are already git-ignored

## AI wording layer

The digest still uses deterministic scoring and guardrails to decide what matters.

If `DAY_CAPTAIN_LLM_PROVIDER` is enabled, Day Captain sends only a bounded shortlist of already-prioritized digest items to an OpenAI-compatible chat-completions endpoint to improve summary wording. If the provider is disabled, misconfigured, or fails at runtime, the app falls back to the deterministic summaries already present in the scored items.

## Microsoft auth setup

1. Create an Entra app registration.
2. Enable public client flows.
3. Add delegated Microsoft Graph permissions.
4. Export your local env vars.
5. Run:

```bash
set -a
source .env
set +a
PYTHONPATH=src python3 -m day_captain auth login
```

Useful auth commands:

```bash
PYTHONPATH=src python3 -m day_captain auth status
PYTHONPATH=src python3 -m day_captain auth login
PYTHONPATH=src python3 -m day_captain auth logout
```

## Local usage

Run a digest directly:

```bash
set -a
source .env
set +a
PYTHONPATH=src python3 -m day_captain morning-digest --force
```

Recall the latest digest:

```bash
PYTHONPATH=src python3 -m day_captain recall-digest
```

Record feedback:

```bash
PYTHONPATH=src python3 -m day_captain record-feedback \
  --run-id RUN_ID \
  --source-kind message \
  --source-id MESSAGE_ID \
  --signal-type useful \
  --signal-value true
```

## Local HTTP service

Start the local web service:

```bash
set -a
source .env
set +a
PYTHONPATH=src python3 -m day_captain serve
```

Healthcheck:

```bash
curl http://127.0.0.1:8000/healthz
```

Trigger a digest through the HTTP endpoint:

```bash
curl -X POST http://127.0.0.1:8000/jobs/morning-digest \
  -H "Content-Type: application/json" \
  -H "X-Day-Captain-Secret: $DAY_CAPTAIN_JOB_SECRET" \
  -d '{"force": true}'
```

Recall through HTTP:

```bash
curl -X POST http://127.0.0.1:8000/jobs/recall-digest \
  -H "Content-Type: application/json" \
  -H "X-Day-Captain-Secret: $DAY_CAPTAIN_JOB_SECRET" \
  -d '{}'
```

## Testing

Run the full test suite:

```bash
python3 -m unittest discover -s tests
```

Run targeted tests:

```bash
python3 -m unittest tests.test_scoring
python3 -m unittest tests.test_web
python3 -m unittest tests.test_graph_client
```

## Storage model

Current persistence covers:
- `messages`
- `meetings`
- `digest_runs`
- `digest_items`
- `feedback`
- `preferences`

Local mode uses `SQLite`.

Hosted mode is wired for Postgres through `DAY_CAPTAIN_DATABASE_URL`.

## Render deployment

The repository includes [`render.yaml`](./render.yaml) for a first hosted deployment path:
- Render web service
- Render Postgres
- `python -m day_captain serve`
- `/healthz` healthcheck

Expected hosted secrets/config include:
- `DAY_CAPTAIN_DATABASE_URL`
- `DAY_CAPTAIN_JOB_SECRET`
- Graph / Entra settings

## GitHub Actions

Two workflow categories exist:
- CI checks
- scheduled hosted trigger for the morning digest

The scheduler workflow is in [`morning-digest-scheduler.yml`](./.github/workflows/morning-digest-scheduler.yml) and expects:
- `DAY_CAPTAIN_SERVICE_URL`
- `DAY_CAPTAIN_JOB_SECRET`

## Security note

The hosted path exists, but a separate hardening track is still open in Logics:
- [`req_001_day_captain_hosted_security_hardening.md`](./logics/request/req_001_day_captain_hosted_security_hardening.md)
- [`item_001_day_captain_hosted_security_hardening.md`](./logics/backlog/item_001_day_captain_hosted_security_hardening.md)
- [`task_004_day_captain_hosted_security_hardening.md`](./logics/tasks/task_004_day_captain_hosted_security_hardening.md)

Treat the current Render deployment path as staging-quality until that hardening task is implemented.

## Logics

Main product chain:
- [`req_000_day_captain_daily_assistant_for_microsoft_365.md`](./logics/request/req_000_day_captain_daily_assistant_for_microsoft_365.md)
- [`item_000_day_captain_daily_assistant_for_microsoft_365.md`](./logics/backlog/item_000_day_captain_daily_assistant_for_microsoft_365.md)
- [`task_003_day_captain_render_deployment_and_scheduler.md`](./logics/tasks/task_003_day_captain_render_deployment_and_scheduler.md)

## Next steps

- harden the hosted security path
- validate a real Render deployment end to end
- switch the hosted scheduler to a production-safe operating mode
- continue tuning scoring and feedback behavior on real mailbox data

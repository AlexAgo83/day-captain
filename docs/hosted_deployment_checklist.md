# Hosted Deployment Checklist

Use this checklist before treating the Render-hosted Day Captain service as ready for routine use.

## Secrets and auth
- Set `DAY_CAPTAIN_JOB_SECRET` in Render and in the GitHub Actions scheduler secrets.
- Do not deploy hosted environments with an empty `DAY_CAPTAIN_JOB_SECRET`.
- Set `DAY_CAPTAIN_GRAPH_CLIENT_ID` and `DAY_CAPTAIN_GRAPH_TENANT_ID`.
- Prefer `DAY_CAPTAIN_GRAPH_REFRESH_TOKEN` for hosted delegated auth bootstrap.
- Do not commit `.env`, token caches, database files, or mailbox-derived fixtures.

## Database and transport
- Use `DAY_CAPTAIN_DATABASE_URL` backed by managed Postgres in hosted mode.
- Set `DAY_CAPTAIN_DATABASE_SSL_MODE=require` for hosted Postgres connections.
- Keep `DAY_CAPTAIN_SQLITE_PATH` for local development only.
- Confirm the Render Postgres instance enforces TLS and the app resolves `sslmode=require`.

## Runtime and scheduling
- Serve the hosted app with `gunicorn`, not the standard-library WSGI server.
- Keep the scheduler workflow calling only `/jobs/morning-digest`.
- Ensure the scheduler checks the HTTP status code without printing the response body.
- Store `DAY_CAPTAIN_SERVICE_URL` and `DAY_CAPTAIN_JOB_SECRET` as GitHub Actions secrets.

## HTTP surface
- Expose only the minimal hosted endpoints:
  - `GET /healthz`
  - `POST /jobs/morning-digest`
  - `POST /jobs/recall-digest`
- Require `X-Day-Captain-Secret` on job endpoints.
- Verify successful job responses contain only acknowledgement metadata and section counts.
- Verify unhandled server errors return `{"error":"internal_error"}` without internal details.

## Operational checks
- Run `python3 -m unittest discover -s tests` before deployment.
- Run `python3 logics/skills/logics-doc-linter/scripts/logics_lint.py --require-status`.
- Run `python3 logics/skills/logics-flow-manager/scripts/workflow_audit.py --group-by-doc`.
- Perform one manual hosted trigger after deployment and verify:
  - scheduler logs do not contain digest content
  - the job returns HTTP `200`
  - a digest run is persisted successfully

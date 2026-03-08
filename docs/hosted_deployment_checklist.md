# Hosted Deployment Checklist

Use this checklist before treating the Render-hosted Day Captain service as ready for routine use.

## Secrets and auth
- Set `DAY_CAPTAIN_JOB_SECRET` in Render and in the GitHub Actions scheduler secrets.
- Do not deploy hosted environments with an empty `DAY_CAPTAIN_JOB_SECRET`.
- Set `DAY_CAPTAIN_GRAPH_AUTH_MODE=app_only` for the Render-hosted unattended path.
- Set `DAY_CAPTAIN_GRAPH_CLIENT_ID` and `DAY_CAPTAIN_GRAPH_TENANT_ID`.
- Set `DAY_CAPTAIN_GRAPH_CLIENT_SECRET`.
- Set `DAY_CAPTAIN_TARGET_USERS` to the explicit mailbox list served by this deployment.
- If delivery should come from a shared mailbox such as `daycaptain@...`, set `DAY_CAPTAIN_GRAPH_SENDER_USER_ID` to that mailbox identifier.
- If inbound email-command recall is enabled for a single-target helper flow, set `DAY_CAPTAIN_EMAIL_COMMAND_ALLOWED_SENDERS` to the bounded allowed sender list.
- Treat `DAY_CAPTAIN_GRAPH_USER_ID` only as the single-user fallback/default target, not the primary multi-user hosted model.
- Do not commit `.env`, token caches, database files, or mailbox-derived fixtures.

## Database and transport
- Use `DAY_CAPTAIN_DATABASE_URL` backed by managed Postgres in hosted mode.
- Set `DAY_CAPTAIN_DATABASE_SSL_MODE=require` for hosted Postgres connections.
- Keep `DAY_CAPTAIN_SQLITE_PATH` for local development only.
- Confirm the Render Postgres instance enforces TLS and the app resolves `sslmode=require`.

## Runtime and scheduling
- Serve the hosted app with `gunicorn`, not the standard-library WSGI server.
- Keep weekday `morning-digest` scheduling separate from the Sunday-evening `weekly-digest` workflow.
- Treat `.github/workflows/morning-digest-scheduler.yml` and `.github/workflows/weekly-digest-scheduler.yml` in this repo as example bootstraps, not the final production scheduler location.
- Prefer a non-sleeping paid web service for production scheduling. Treat sleeping-service operation as a fallback mode only.
- Include `target_user_id` in hosted job payloads when several target users are configured.
- If GitHub Actions drives several users, set repository variable `DAY_CAPTAIN_TARGET_USERS_JSON` to a JSON array.
- Ensure the scheduler checks the HTTP status code without printing the response body.
- Store `DAY_CAPTAIN_SERVICE_URL` and `DAY_CAPTAIN_JOB_SECRET` as GitHub Actions secrets.
- If the hosted service may sleep, use `--wake-service` plus bounded wake retries before the real job trigger and give the workflow a longer timeout budget.
- If the scheduler fans out across several users, prefer one standalone readiness/wake-up step before the fan-out instead of waking the service once per target.
- Keep the routine weekday cron path on `trigger-hosted-job --job morning-digest`, the Sunday recap path on `trigger-hosted-job --job weekly-digest`, and reserve `validate-hosted-service` for manual checks and rollout validation.

## HTTP surface
- Expose only the minimal hosted endpoints:
  - `GET /healthz`
  - `POST /jobs/morning-digest`
  - `POST /jobs/weekly-digest`
  - `POST /jobs/recall-digest`
  - `POST /jobs/email-command-recall`
- Require `X-Day-Captain-Secret` on job endpoints.
- Verify `GET /healthz` returns only `{"status":"ok"}` for unauthenticated probes and includes runtime summary metadata only when `X-Day-Captain-Secret` is supplied.
- Verify successful job responses contain only acknowledgement metadata and section counts.
- Verify unhandled server errors return `{"error":"internal_error"}` without internal details.

## Operational checks
- Run `python3 -m unittest discover -s tests` before deployment.
- Run `PYTHONPATH=src python3 -m day_captain validate-config` against the final hosted env contract.
- Run `python3 logics/skills/logics-doc-linter/scripts/logics_lint.py --require-status`.
- Run `python3 logics/skills/logics-flow-manager/scripts/workflow_audit.py --group-by-doc`.
- Perform one manual hosted trigger after deployment and verify:
  - scheduler logs do not contain digest content
  - the job returns HTTP `200`
  - a digest run is persisted successfully
  - only the requested `target_user_id` receives the digest and persistence stays isolated from other configured users
- If `DAY_CAPTAIN_GRAPH_SENDER_USER_ID` is set, confirm the target mailbox remains the read scope while the delivered message visibly comes from the dedicated sender mailbox.
- Run `PYTHONPATH=src python3 -m day_captain validate-hosted-service --target-user ... --wake-service --wake-timeout-seconds 45 --wake-max-attempts 6 --wake-delay-seconds 10 --timeout-seconds 90 --expect-graph-auth-mode app_only --expect-storage-backend postgres` from the private ops repo or equivalent environment.
- If inbound email-command recall is enabled, run `PYTHONPATH=src python3 -m day_captain validate-hosted-service --target-user ... --wake-service --wake-timeout-seconds 45 --wake-max-attempts 6 --wake-delay-seconds 10 --timeout-seconds 90 --expect-graph-auth-mode app_only --expect-storage-backend postgres --check-email-command --email-command-sender ... --email-command-text recall-week` and confirm only authorized senders succeed.
- For sleeping-service fallback, run `PYTHONPATH=src python3 -m day_captain check-hosted-health --wake-service ...` once before the per-user trigger fan-out when possible.
- If the service may sleep, document the warm-up interval, readiness check, and timeout policy directly in the private ops repo runbook.
- Follow [`tenant_scoped_multi_user_operator_guide.md`](/Users/alexandreagostini/Documents/day-captain/docs/tenant_scoped_multi_user_operator_guide.md) for the bounded operator workflow.

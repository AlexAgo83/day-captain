# Private Ops Repo Bootstrap

Use a separate private repository, for example `day-captain-ops`, for production scheduling and production secrets.

## Why

- production secrets should not live in the application repo
- production scheduling should be isolated from public CI or normal code-review churn
- the application repo keeps only reference automation and reusable trigger utilities

## Minimal layout

Your private ops repo should contain:

- the production GitHub Actions workflow
- repository secrets such as `DAY_CAPTAIN_SERVICE_URL` and `DAY_CAPTAIN_JOB_SECRET`
- optional repository variable `DAY_CAPTAIN_TARGET_USERS_JSON`
- optional secrets or variables for `DAY_CAPTAIN_GRAPH_SENDER_USER_ID` and `DAY_CAPTAIN_EMAIL_COMMAND_ALLOWED_SENDERS`
- deployment-specific notes or runbooks
- optional Power Automate runbook if inbound email-command recall is operated outside GitHub Actions

Use these copy-ready templates in the private ops repo:
- [`day_captain_ops_morning_digest_scheduler.yml`](/Users/alexandreagostini/Documents/day-captain/docs/day_captain_ops_morning_digest_scheduler.yml) -> `.github/workflows/morning-digest.yml`
- [`day_captain_ops_weekly_digest_scheduler.yml`](/Users/alexandreagostini/Documents/day-captain/docs/day_captain_ops_weekly_digest_scheduler.yml) -> `.github/workflows/weekly-digest.yml`

## Recommended workflow pattern

1. Check out the Day Captain repo, or vendor the trigger script into the ops repo.
2. Use `scripts/check_hosted_health.py` for readiness/wake-up, `scripts/validate_hosted_service.py` for manual validation runs, and `scripts/trigger_hosted_digest.py` for routine trigger-only workflows.
3. Fan out over explicit users from `DAY_CAPTAIN_TARGET_USERS_JSON`.
4. If the hosted service can sleep, run one standalone readiness step with `scripts/check_hosted_health.py --wake-service` before the real trigger fan-out.
5. Keep the workflow output free of digest content.

## Copy-ready workflows

Copy:
- [`day_captain_ops_morning_digest_scheduler.yml`](/Users/alexandreagostini/Documents/day-captain/docs/day_captain_ops_morning_digest_scheduler.yml) into the private ops repo as `.github/workflows/morning-digest.yml`
- [`day_captain_ops_weekly_digest_scheduler.yml`](/Users/alexandreagostini/Documents/day-captain/docs/day_captain_ops_weekly_digest_scheduler.yml) into the private ops repo as `.github/workflows/weekly-digest.yml`

Assumptions baked into that template:

- the application repo is `alexandreagostini/day-captain`
- Render deploys the `release` branch
- the ops workflow installs the package from that `release` branch before calling the hosted helper scripts
- the hosted service may sleep, so the workflow performs one readiness/wake-up pass before per-user fan-out
- `DAY_CAPTAIN_TARGET_USERS_JSON` is mandatory in the ops repo so the scheduler never silently falls back to an ambiguous single-user trigger
- the morning scheduler stays weekday-only and targets `09:00 Europe/Paris`, while the weekly scheduler is a separate Sunday-evening contract
- the weekly scheduler gate should tolerate normal GitHub Actions cron jitter within the intended Sunday `20:30 Europe/Paris` hour instead of depending on an exact process start minute
- the copy-ready weekly templates are expected to stay aligned with the shared `day_captain.scheduler.should_run_sunday_weekly_digest` helper

## Suggested repository variables

- `DAY_CAPTAIN_TARGET_USERS_JSON=["alice@example.com","bob@example.com"]`

## Suggested repository secrets

- `DAY_CAPTAIN_SERVICE_URL=https://your-render-service.example.com`
- `DAY_CAPTAIN_JOB_SECRET=...`
- `DAY_CAPTAIN_GRAPH_SENDER_USER_ID=daycaptain@example.com`
- `DAY_CAPTAIN_EMAIL_COMMAND_ALLOWED_SENDERS=assistant@example.com=alice@example.com`

If you set `DAY_CAPTAIN_EMAIL_COMMAND_ALLOWED_SENDERS`, also ensure:
- the hosted service uses `DAY_CAPTAIN_GRAPH_AUTH_MODE=app_only`
- `DAY_CAPTAIN_GRAPH_SEND_ENABLED=true`
- single-target deployments may use bare helper senders such as `assistant@example.com`
- multi-user deployments must use explicit `sender=target` mappings such as `assistant@example.com=alice@example.com`

## Validation before enabling cron

- run `PYTHONPATH=src python3 -m day_captain validate-config --target-user alice@example.com`
- run `DAY_CAPTAIN_SERVICE_URL=... DAY_CAPTAIN_JOB_SECRET=... PYTHONPATH=src python3 -m day_captain check-hosted-health --wake-service --wake-timeout-seconds 45 --wake-max-attempts 6 --wake-delay-seconds 10 --expect-graph-auth-mode app_only --expect-storage-backend postgres`
- run `DAY_CAPTAIN_SERVICE_URL=... DAY_CAPTAIN_JOB_SECRET=... PYTHONPATH=src python3 -m day_captain validate-hosted-service --target-user alice@example.com --wake-service --wake-timeout-seconds 45 --wake-max-attempts 6 --wake-delay-seconds 10 --timeout-seconds 90 --expect-graph-auth-mode app_only --expect-storage-backend postgres`
- if using a dedicated sender mailbox, confirm the hosted env also sets `DAY_CAPTAIN_GRAPH_SENDER_USER_ID=daycaptain@example.com` and verify delivery is sent from that mailbox while the selected target mailbox remains the data source
- if using inbound email-command recall, run `DAY_CAPTAIN_SERVICE_URL=... DAY_CAPTAIN_JOB_SECRET=... PYTHONPATH=src python3 -m day_captain validate-hosted-service --target-user alice@example.com --wake-service --wake-timeout-seconds 45 --wake-max-attempts 6 --wake-delay-seconds 10 --timeout-seconds 90 --expect-graph-auth-mode app_only --expect-storage-backend postgres --check-email-command --email-command-sender alice@example.com --email-command-text recall-week`
- if the release includes digest-readability changes, review [`digest_rendering_validation.md`](/Users/alexandreagostini/Documents/day-captain/docs/digest_rendering_validation.md) and explicitly perform the final live Outlook rendering check before calling the rollout complete
- trigger one hosted job manually for each target user with `day-captain trigger-hosted-job --job morning-digest`
- trigger one hosted weekly job manually with `day-captain trigger-hosted-job --job weekly-digest`
- trigger one hosted `email-command-recall` job manually if that surface is enabled and confirm duplicate suppression by replaying the same `command_message_id`
- confirm delivery and persistence before enabling the scheduled trigger
- if the hosted plan can sleep, document the warm-up path and timeout policy in the private ops workflow before enabling cron
- if inbound email-command recall is bridged through Power Automate, keep [`power_automate_shared_mailbox_recall_setup.md`](/Users/alexandreagostini/Documents/day-captain/docs/power_automate_shared_mailbox_recall_setup.md) alongside the private repo runbook and document the mailbox permission propagation caveat
- if a hosted run remains `delivery_pending`, treat it as possible post-send uncertainty and reconcile before retrying from ops
- if a hosted run is `delivery_failed`, treat it as a pre-send failure and retry only after fixing the underlying Graph or configuration issue

The hosted validation helper checks:

- `GET /healthz`
- protected runtime summary from `GET /healthz` using `X-Day-Captain-Secret`
- `POST /jobs/morning-digest`
- `POST /jobs/weekly-digest`
- optional `POST /jobs/recall-digest`
- optional `POST /jobs/email-command-recall`
- runtime expectations such as `graph_auth_mode=app_only` and `storage_backend=postgres`
- acknowledgement shape (`status`, `job`, `run_id`, `generated_at`, `delivery_mode`, `section_counts`)
- `run_id` consistency between morning-digest and recall-digest
- email-command routing and sender resolution when `--check-email-command` is enabled

Recommended sleeping-service fallback:

- warm the service with `check-hosted-health --wake-service`
- wait for readiness or retry within a bounded window
- only then trigger `POST /jobs/morning-digest` through `trigger-hosted-job --job morning-digest`
- use a separate Sunday workflow for `POST /jobs/weekly-digest` instead of broadening the weekday morning cron
- keep longer timeouts in the ops workflow than you would on an always-on service

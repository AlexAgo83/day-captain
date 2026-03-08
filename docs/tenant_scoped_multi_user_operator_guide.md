# Tenant-Scoped Multi-User Operator Guide

This guide covers the bounded operator-managed multi-user model shipped in Day Captain.

## Operating model

- One deployment serves one Microsoft 365 tenant.
- Users are explicit targets, not auto-discovered recipients.
- Each digest run executes for exactly one `target_user_id`.
- Persistence is partitioned by `tenant_id` and `user_id`.

## Required hosted settings

- `DAY_CAPTAIN_ENV=production`
- `DAY_CAPTAIN_DATABASE_URL=postgresql://...`
- `DAY_CAPTAIN_JOB_SECRET=...`
- `DAY_CAPTAIN_GRAPH_AUTH_MODE=app_only`
- `DAY_CAPTAIN_GRAPH_TENANT_ID=...`
- `DAY_CAPTAIN_GRAPH_CLIENT_ID=...`
- `DAY_CAPTAIN_GRAPH_CLIENT_SECRET=...`
- `DAY_CAPTAIN_TARGET_USERS=["alice@example.com","bob@example.com"]` is not used directly by the app. Keep the app env var as CSV:
  - `DAY_CAPTAIN_TARGET_USERS=alice@example.com,bob@example.com`
- optional `DAY_CAPTAIN_GRAPH_SENDER_USER_ID=daycaptain@example.com` when delivery should come from a dedicated shared mailbox
- optional `DAY_CAPTAIN_EMAIL_COMMAND_ALLOWED_SENDERS=alice@example.com` when inbound mail commands should be accepted from a bounded helper sender set in a single-target deployment
- `DAY_CAPTAIN_GRAPH_SEND_ENABLED=true`

## Add a target user

1. Confirm the user mailbox is inside the configured tenant.
2. Add the mailbox identifier to `DAY_CAPTAIN_TARGET_USERS`.
3. Ensure the Graph application permissions still cover the mailbox read and send operations.
4. Trigger a single-user validation run for the new target before adding it to automated schedules.

## Dedicated sender mailbox

- Use `DAY_CAPTAIN_GRAPH_SENDER_USER_ID=daycaptain@example.com` when the digest should be sent from a shared mailbox such as `daycaptain@...`.
- In that mode, Day Captain still reads Outlook mail and calendar data from the selected `target_user_id`.
- Delivery is routed through `/users/{sender}/sendMail`, so confirm the dedicated mailbox exists and the app-only Graph permissions cover it.
- Keep the target user explicit in hosted runs; otherwise the sender mailbox is not enough to infer which mailbox should be analyzed.

## Inbound email-command recall

- The shipped command surface is bounded to `recall`, `recall-today`, and `recall-week`.
- `recall` and `recall-today` generate a digest for the current day in `DAY_CAPTAIN_DISPLAY_TIMEZONE`.
- `recall-week` generates a digest from Monday `00:00` through now in `DAY_CAPTAIN_DISPLAY_TIMEZONE`.
- Sender resolution is strict:
  - multi-user deployments should use a sender address that matches one configured target user
  - single-user deployments may also authorize helper senders through `DAY_CAPTAIN_EMAIL_COMMAND_ALLOWED_SENDERS`
- Duplicate suppression is keyed by inbound `command_message_id`, so replaying the same inbound message should not regenerate a second digest.
- The first recommended transport bridge is Power Automate on top of the shared mailbox trigger. See [`power_automate_shared_mailbox_recall_setup.md`](/Users/alexandreagostini/Documents/day-captain/docs/power_automate_shared_mailbox_recall_setup.md).

## Manual validation

Validate the hosted env contract before triggering runs:

```bash
PYTHONPATH=src python3 -m day_captain validate-config
PYTHONPATH=src python3 -m day_captain validate-config --target-user alice@example.com
```

Run a single target through the CLI:

```bash
PYTHONPATH=src python3 -m day_captain morning-digest --force --target-user alice@example.com
```

Recall the latest digest for one target:

```bash
PYTHONPATH=src python3 -m day_captain recall-digest --target-user alice@example.com
```

Trigger the hosted job directly:

```bash
curl -X POST "$DAY_CAPTAIN_SERVICE_URL/jobs/morning-digest" \
  -H "Content-Type: application/json" \
  -H "X-Day-Captain-Secret: $DAY_CAPTAIN_JOB_SECRET" \
  -d '{"force":false,"target_user_id":"alice@example.com"}'
```

Run the hosted validation flow:

```bash
DAY_CAPTAIN_SERVICE_URL=... \
DAY_CAPTAIN_JOB_SECRET=... \
PYTHONPATH=src python3 -m day_captain validate-hosted-service \
  --target-user alice@example.com \
  --wake-service \
  --wake-timeout-seconds 45 \
  --wake-max-attempts 6 \
  --wake-delay-seconds 10 \
  --timeout-seconds 90 \
  --expect-graph-auth-mode app_only \
  --expect-storage-backend postgres
```

Run the hosted validation flow including inbound email-command recall:

```bash
DAY_CAPTAIN_SERVICE_URL=... \
DAY_CAPTAIN_JOB_SECRET=... \
PYTHONPATH=src python3 -m day_captain validate-hosted-service \
  --target-user alice@example.com \
  --wake-service \
  --wake-timeout-seconds 45 \
  --wake-max-attempts 6 \
  --wake-delay-seconds 10 \
  --timeout-seconds 90 \
  --expect-graph-auth-mode app_only \
  --expect-storage-backend postgres \
  --check-email-command \
  --email-command-sender alice@example.com \
  --email-command-text recall-week
```

If the hosted service can sleep between runs, use `--wake-service` instead of assuming the first scheduler call will execute immediately.

For several target users, prefer a separate readiness pass before fan-out:

```bash
DAY_CAPTAIN_SERVICE_URL=... \
DAY_CAPTAIN_JOB_SECRET=... \
PYTHONPATH=src python3 -m day_captain check-hosted-health \
  --wake-service \
  --wake-timeout-seconds 45 \
  --wake-max-attempts 6 \
  --wake-delay-seconds 10 \
  --expect-graph-auth-mode app_only \
  --expect-storage-backend postgres
```

Then use trigger-only calls for the routine schedule:

```bash
DAY_CAPTAIN_SERVICE_URL=... \
DAY_CAPTAIN_JOB_SECRET=... \
PYTHONPATH=src python3 -m day_captain trigger-hosted-job \
  --job morning-digest \
  --target-user alice@example.com \
  --timeout-seconds 90
```

Trigger a bounded email-command recall manually:

```bash
DAY_CAPTAIN_SERVICE_URL=... \
DAY_CAPTAIN_JOB_SECRET=... \
PYTHONPATH=src python3 -m day_captain trigger-hosted-job \
  --job email-command-recall \
  --message-id inbound-001 \
  --sender-address alice@example.com \
  --command-text recall-week \
  --timeout-seconds 90
```

## Scheduling model

The GitHub Actions scheduler supports two modes:

- Manual one-off override with `workflow_dispatch` input `target_user_id`
- Scheduled fan-out from repository variable `DAY_CAPTAIN_TARGET_USERS_JSON`

In production, run that scheduler from a private ops repository rather than from the application repository.

Use the ready-to-copy template in [`day_captain_ops_morning_digest_scheduler.yml`](/Users/alexandreagostini/Documents/day-captain/docs/day_captain_ops_morning_digest_scheduler.yml) as the base workflow for that private repo.
Use [`day_captain_ops_weekly_digest_scheduler.yml`](/Users/alexandreagostini/Documents/day-captain/docs/day_captain_ops_weekly_digest_scheduler.yml) as the separate Sunday-evening weekly recap workflow.

Example repository variable:

```json
["alice@example.com", "bob@example.com"]
```

The weekday scheduler issues one hosted `/jobs/morning-digest` call per listed target user. The Sunday scheduler issues one hosted `/jobs/weekly-digest` call per listed target user. If `DAY_CAPTAIN_TARGET_USERS_JSON` is unset, the example workflow falls back to a single request without `target_user_id`, which is compatible with single-user deployments.
- The Sunday scheduler should tolerate normal GitHub Actions cron jitter. Prefer the shared helper-backed gate from the copy-ready weekly workflow template instead of requiring an exact `20:30 Europe/Paris` process start.

## Sleeping-service fallback

If the hosted web service is on a plan that can sleep:

- use the private ops workflow to call `GET /healthz` as a warm-up step before the real trigger
- for multi-user schedules, do that warm-up once before the per-user fan-out rather than once per user
- use trigger-only job calls for the weekday and Sunday schedules, and keep full `validate-hosted-service` runs for manual validation or rollout checks
- allow bounded retries before `POST /jobs/morning-digest`
- allow bounded retries before `POST /jobs/weekly-digest`
- use longer timeout settings than for an always-on deployment
- keep this as a fallback mode only; prefer a paid always-on service for routine production delivery

Use [`private_ops_repo_bootstrap.md`](/Users/alexandreagostini/Documents/day-captain/docs/private_ops_repo_bootstrap.md) as the starting point for that private repo.

## Isolation checks

After adding or changing users, validate:

- each scheduled or manual run returns `200`
- each user receives only their own digest
- recall for `alice@example.com` never returns `bob@example.com`'s latest run
- if a dedicated sender mailbox is configured, delivery still arrives for the target user while the visible sender is `daycaptain@...`
- if inbound email-command recall is enabled, only authorized senders can trigger it and replaying the same inbound `command_message_id` is deduplicated
- a run left in `delivery_pending` still means delivery may already have happened and requires reconciliation before another send
- a run marked `delivery_failed` means Graph prerequisites or delivery failed before acceptance was likely, so a later retry is expected to be safe
- feedback recorded against one user changes only that user's preferences
- persisted rows for messages, meetings, runs, feedback, and preferences stay partitioned by `tenant_id` and `user_id`

## Rollout note

Use this model for bounded operator-managed deployments. It is not a self-service tenant administration system.

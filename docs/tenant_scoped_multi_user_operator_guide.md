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
- `DAY_CAPTAIN_GRAPH_SEND_ENABLED=true`

## Add a target user

1. Confirm the user mailbox is inside the configured tenant.
2. Add the mailbox identifier to `DAY_CAPTAIN_TARGET_USERS`.
3. Ensure the Graph application permissions still cover the mailbox read and send operations.
4. Trigger a single-user validation run for the new target before adding it to automated schedules.

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
  --expect-graph-auth-mode app_only \
  --expect-storage-backend postgres
```

## Scheduling model

The GitHub Actions scheduler supports two modes:

- Manual one-off override with `workflow_dispatch` input `target_user_id`
- Scheduled fan-out from repository variable `DAY_CAPTAIN_TARGET_USERS_JSON`

In production, run that scheduler from a private ops repository rather than from the application repository.

Example repository variable:

```json
["alice@example.com", "bob@example.com"]
```

The scheduler will issue one hosted `/jobs/morning-digest` call per listed target user. If `DAY_CAPTAIN_TARGET_USERS_JSON` is unset, the workflow falls back to a single request without `target_user_id`, which is compatible with single-user deployments.

Use [`private_ops_repo_bootstrap.md`](/Users/alexandreagostini/Documents/day-captain/docs/private_ops_repo_bootstrap.md) as the starting point for that private repo.

## Isolation checks

After adding or changing users, validate:

- each scheduled or manual run returns `200`
- each user receives only their own digest
- recall for `alice@example.com` never returns `bob@example.com`'s latest run
- feedback recorded against one user changes only that user's preferences
- persisted rows for messages, meetings, runs, feedback, and preferences stay partitioned by `tenant_id` and `user_id`

## Rollout note

Use this model for bounded operator-managed deployments. It is not a self-service tenant administration system.

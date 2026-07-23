# Power Automate Scheduler Setup

This runbook replaces routine GitHub Actions cron scheduling with tenant-owned Power Automate recurrence. Power Automate only triggers Day Captain's hosted HTTP jobs; Day Captain still owns digest generation, Graph access, storage, and delivery.

## Required Connections

- Power Automate Schedule trigger.
- HTTP connector.
- Optional Office 365 Outlook or Teams connector only if custom failure notifications are required beyond native owner failure alerts.

The HTTP connector may require a Power Automate Premium or trial entitlement. If it is not available, keep the GitHub Actions schedules enabled until the entitlement is resolved.

## Required Values

Store these in Power Platform environment variables or another tenant-managed secret/config store:

- `DAY_CAPTAIN_SERVICE_URL`, for example `https://your-day-captain-service.example.com`
- `DAY_CAPTAIN_JOB_SECRET`
- `DAY_CAPTAIN_TARGET_USERS_JSON`, a JSON array of target user IDs

Do not put these values in flow names, tracked docs, email bodies, GitHub logs, or screenshots.

## Flow 1: Morning Digest

- Name: `Day Captain - Morning Digest`
- Trigger: Recurrence
- Time zone: `Europe/Paris`
- Frequency: Week
- On these days: Monday, Tuesday, Wednesday, Thursday, Friday
- At these hours/minutes: `08:45`
- Concurrency: 1 run

Actions:

1. Parse `DAY_CAPTAIN_TARGET_USERS_JSON`.
2. Warm the hosted service with retry policy `fixed`, interval `PT10S`, count `6`:

```text
GET @{variables('DAY_CAPTAIN_SERVICE_URL')}/healthz
X-Day-Captain-Secret: @{variables('DAY_CAPTAIN_JOB_SECRET')}
```

3. Apply to each target user and call with the same retry policy:

```text
POST @{variables('DAY_CAPTAIN_SERVICE_URL')}/jobs/morning-digest
Content-Type: application/json
X-Day-Captain-Secret: @{variables('DAY_CAPTAIN_JOB_SECRET')}
```

Body:

```json
{
  "force": false,
  "target_user_id": "<target user from loop>"
}
```

## Flow 2: Weekly Digest

- Name: `Day Captain - Weekly Digest`
- Trigger: Recurrence
- Time zone: `Europe/Paris`
- Frequency: Week
- On these days: Sunday
- At these hours/minutes: `20:30`
- Concurrency: 1 run

Actions:

1. Parse `DAY_CAPTAIN_TARGET_USERS_JSON`.
2. Warm the hosted service with the same authenticated `GET /healthz` action and retry policy `fixed`, interval `PT10S`, count `6`.
3. Apply to each target user and call with the same retry policy:

```text
POST @{variables('DAY_CAPTAIN_SERVICE_URL')}/jobs/weekly-digest
Content-Type: application/json
X-Day-Captain-Secret: @{variables('DAY_CAPTAIN_JOB_SECRET')}
```

Body:

```json
{
  "target_user_id": "<target user from loop>"
}
```

## Logging And Failure Handling

- Enable secure inputs and secure outputs on HTTP actions that include `X-Day-Captain-Secret`.
- Keep secure outputs off only if a downstream action must parse the response, and document the reason before doing so.
- Do not log response bodies outside Power Automate run history.
- Keep the Power Automate owner failure alert subscription enabled. If a custom failure notification is added, include only:
  - flow name,
  - run timestamp,
  - failed action name,
  - target user ID if available,
  - Power Automate run link.
- Do not include digest content, mailbox snippets, Graph responses, or secrets in failure emails.

## Validation

Before disabling GitHub Actions schedules:

1. Manually run `Day Captain - Morning Digest` for one target user.
2. Confirm the hosted response is HTTP 200.
3. Confirm the digest was delivered to that target only.
4. Record the Power Automate run ID and delivery timestamp in the Logics task notes.
5. Manually run `Day Captain - Weekly Digest` or wait for the first Sunday run.
6. Record that run ID and delivery timestamp too.

Only after both jobs have evidence should the private ops repo remove the `schedule:` blocks from the GitHub workflows. Keep `workflow_dispatch` available.

## Rollback

If Power Automate recurrence, entitlement, connection, or HTTP execution fails:

1. Stop the affected Power Automate flow.
2. Restore the corresponding GitHub Actions `schedule:` block in the private ops repo.
3. Run the workflow manually with `workflow_dispatch` for one target user.
4. Confirm delivery.
5. Fix the Power Automate issue before trying the cutover again.

The rollback must not change Day Captain app code; both schedulers call the same hosted job endpoints.

## Deployment Evidence

Keep tenant-specific flow names, run IDs, next-run timestamps, service URLs, target-user lists, and secret-rotation notes in the private ops repository. Public docs should record only the reusable setup pattern and the content-free validation checklist above.

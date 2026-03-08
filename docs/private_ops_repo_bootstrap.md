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
- deployment-specific notes or runbooks

## Recommended workflow pattern

1. Check out the Day Captain repo, or vendor the trigger script into the ops repo.
2. Use `scripts/validate_hosted_service.py` for validation runs and `scripts/trigger_hosted_digest.py` for simpler trigger-only workflows.
3. Fan out over explicit users from `DAY_CAPTAIN_TARGET_USERS_JSON`.
4. Keep the workflow output free of digest content.

## Suggested repository variables

- `DAY_CAPTAIN_TARGET_USERS_JSON=["alice@example.com","bob@example.com"]`

## Suggested repository secrets

- `DAY_CAPTAIN_SERVICE_URL=https://your-render-service.example.com`
- `DAY_CAPTAIN_JOB_SECRET=...`

## Validation before enabling cron

- run `PYTHONPATH=src python3 -m day_captain validate-config --target-user alice@example.com`
- run `DAY_CAPTAIN_SERVICE_URL=... DAY_CAPTAIN_JOB_SECRET=... PYTHONPATH=src python3 -m day_captain validate-hosted-service --target-user alice@example.com --expect-graph-auth-mode app_only --expect-storage-backend postgres`
- trigger one hosted job manually for each target user
- confirm delivery and persistence before enabling the scheduled trigger

The hosted validation helper checks:

- `GET /healthz`
- protected runtime summary from `GET /healthz` using `X-Day-Captain-Secret`
- `POST /jobs/morning-digest`
- optional `POST /jobs/recall-digest`
- runtime expectations such as `graph_auth_mode=app_only` and `storage_backend=postgres`
- acknowledgement shape (`status`, `job`, `run_id`, `generated_at`, `delivery_mode`, `section_counts`)
- `run_id` consistency between morning-digest and recall-digest

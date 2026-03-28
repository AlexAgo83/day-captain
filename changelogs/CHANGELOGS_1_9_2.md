# Changelog (`1.9.1 -> 1.9.2`)

## Major Highlights

- Hardened the hosted Render runtime so health checks can stay responsive while a digest job is running on a single-instance deployment.
- Documented the exact manual Render start command needed for operators who do not deploy from `render.yaml`.

## Version 1.9.2

### Delivered

- Updated the recommended hosted start command to `gunicorn --worker-class gthread --threads 4 --timeout 90 --bind 0.0.0.0:$PORT "day_captain.web:create_web_app()"`.
- Kept the hosted `/healthz` path unchanged while improving the odds that Render health checks succeed during long-running morning digest execution.
- Added explicit operator guidance in the hosted deployment checklist for single-instance Render services that run digest work inside the web process.
- Aligned the Render deployment section in the repository README with the hardened Gunicorn runtime command.

### Validation

- Manual runtime diagnosis against the live Render service confirmed repeated `server_failed` events with `HTTP health check failed (timed out after 5 seconds)` during the morning digest window on the free single-instance plan.
- `python3 logics/skills/logics-version-release-manager/scripts/publish_version_release.py --dry-run`

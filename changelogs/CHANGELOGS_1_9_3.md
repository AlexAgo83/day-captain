# Changelog (`1.9.2 -> 1.9.3`)

## Major Highlights

- Hardened the weekday morning scheduler so GitHub Actions jitter after the intended `08:45 Europe/Paris` slot no longer skips the digest entirely.
- Updated the ops workflow contract to pass the triggering cron expression into the shared scheduler gate.

## Version 1.9.3

### Delivered

- Added cron-aware scheduler gate resolution so the weekday helper can evaluate the intended scheduled slot instead of the runner's delayed wall-clock start time.
- Kept the duplicate DST-safe morning cron entries while ensuring only the matching `08:45 Europe/Paris` trigger proceeds to hosted wake-up and digest fan-out.
- Aligned the shipped ops scheduler template with the private ops workflow contract by forwarding `github.event.schedule` into the shared helper.
- Added regression coverage for the exact `30 March 2026` jitter scenario that skipped the morning digest despite a successful workflow run.

### Validation

- `python3 -m unittest tests/test_scheduler.py tests/test_scheduler_templates.py`
- `python3 logics/skills/logics-version-release-manager/scripts/publish_version_release.py --dry-run`

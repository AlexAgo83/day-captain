# Changelog (`1.9.4 -> 1.9.5`)

## Major Highlights

- Moved routine Day Captain scheduling from GitHub Actions cron to tenant-owned Power Automate recurrence.
- Preserved manual GitHub Actions fallback while documenting the Power Automate runbook, migration corpus, and release contract.
- Hardened the scheduler model for Render cold starts, secure HTTP run history, and future tenant reuse.

## Version 1.9.5

### Delivered

- Added the Power Automate scheduler runbook and Logics migration corpus.
- Updated app and private ops documentation so Power Automate is primary and GitHub Actions remains manual fallback only.
- Recorded the scheduler hardening review: explicit HTTP retries, secure HTTP inputs and outputs, native owner failure alerts, and remaining secret-store hardening before cloning the pattern into another tenant.
- Added a Logics release contract and moved CI Logics validation to the packaged `logics-manager` CLI.

### Validation

- `python3 -m pytest`
- `logics-manager flow validate req_054_day_captain_power_automate_scheduler_migration --fixable --explain`
- `logics-manager lint --require-status`
- `logics-manager audit --group-by-doc`

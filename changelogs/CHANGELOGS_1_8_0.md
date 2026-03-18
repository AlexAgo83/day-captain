# Changelog (`1.7.0 -> 1.8.0`)

## Major Highlights

- Added clearer digest mail triage metadata with unread visibility and low-prominence received timestamps on surfaced message cards.
- Moved the supported weekday morning scheduler default to `09:00 Europe/Paris` with a shared timezone-aware gate in both repository and ops templates.
- Hardened hosted Graph timeout handling and aligned the imported Logics kit to the newer `v1.0.3` submodule state.

## Version 1.8.0

### Delivered

- Added visible unread/read state rendering for surfaced mail items while preserving the current behavior that still allows already read but relevant messages to resurface.
- Added low-prominence received-time metadata on surfaced mail cards using the digest display timezone.
- Added a shared `should_run_weekday_morning_digest` scheduler helper and updated the weekday scheduler templates to target `09:00 Europe/Paris` safely across DST.
- Updated scheduler, rendering, and operator docs to reflect the new unread/read metadata and weekday scheduling contract.
- Added regression coverage for unread/read renderer behavior, weekday scheduler gating, and morning scheduler template expectations.
- Converted hosted Microsoft Graph read timeouts into bounded Graph errors so hosted health and job calls fail more safely instead of leaking raw timeout behavior.
- Bumped the imported `logics/skills` kit from the older pinned commit to `v1.0.3`.
- Closed the related Logics request, backlog item, and task for the unread metadata and `09:00 Europe/Paris` delivery slice.

### Validation

- `python3 -m unittest tests.test_digest_renderer tests.test_scheduler tests.test_scheduler_templates`
- `python3 -m unittest discover -s tests`
- `python3 logics/skills/logics-doc-linter/scripts/logics_lint.py --require-status`
- `python3 logics/skills/logics-flow-manager/scripts/workflow_audit.py --group-by-doc`

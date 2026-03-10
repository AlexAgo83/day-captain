# Changelog (`1.4.3 -> 1.5.1`)

## Major Highlights

- Replaced the old mechanical digest-summary behavior with structured assistant briefings for surfaced mail threads and meetings, including handling guidance, confidence signals, and a regenerated `En bref`.
- Added product-aware treatment for all-day presence events so location-style calendar entries are rendered separately from ordinary meetings.
- Hardened hosted/runtime behavior with fail-fast validation, durable-storage requirements, explicit delegated-auth expiry failures, mailbox normalization, and shared datetime parsing across CLI and web.

## Version 1.5.1

### Delivered

- Shipped structured digest briefings per email thread and per meeting, with `recommended_action`, `handling_bucket`, `confidence_score`, `confidence_label`, and `confidence_reason`.
- Rebuilt `En bref` from important structured briefings instead of the older excerpt-oriented summary path.
- Added related-context support for meeting briefings and isolated qualifying all-day agenda entries as `daily_presence`.
- Improved recipient-aware wording, sender visibility on mail cards, and lighter-meeting-day behavior that can extend the meeting section into the next day.
- Added versioned changelog workflow support for release artifacts under `changelogs/`.
- Hardened hosted execution so production/staging requires durable database-backed runtime configuration and fails explicitly on invalid Graph auth setup.
- Prevented delegated Graph auth from reusing expired cached access tokens without a valid refresh path.
- Normalized mailbox target-user handling across config/runtime flows and aligned CLI plus hosted web datetime parsing with the shared model parser for `Z`-suffixed ISO timestamps.

### Validation

- `python3 -m unittest discover -s tests`
- `python3 logics/skills/logics-doc-linter/scripts/logics_lint.py --require-status`
- `python3 logics/skills/logics-flow-manager/scripts/workflow_audit.py --group-by-doc`

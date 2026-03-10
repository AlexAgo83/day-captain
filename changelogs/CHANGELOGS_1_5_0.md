# Changelog (`1.4.2 -> 1.5.0`)

## Major Highlights

- Replaced mechanical digest excerpts with structured assistant briefings for mail threads and meetings.
- Added confidence signals, recommended follow-up guidance, and a dedicated daily-presence section for all-day location events.
- Improved recipient-aware and bilingual digest wording so French digests stay readable when the source thread is in English.
- Formalized versioned changelog generation under `changelogs/` for closure-time release artifacts.

## Version 1.5.0

### Delivered

- Added structured per-thread and per-meeting digest entries with `recommended_action`, `handling_bucket`, confidence metadata, and persisted context payloads.
- Regenerated `En bref` from structured briefings instead of falling back to raw titles, and surfaced related mail context in meeting briefings.
- Split all-day calendar presence markers such as office or remote-work signals into a dedicated `daily_presence` section instead of treating them as normal meetings.
- Improved recipient-aware wording for directly addressed mail and introduced bounded bilingual fallback rules for English-source content inside French digests.
- Closed the synchronized Logics delivery slices for structured briefings, recipient-aware wording, bilingual coherence, meeting chronology, and changelog workflow alignment.

### Validation

- `python3 -m unittest discover -s tests`
- `python3 logics/skills/logics-doc-linter/scripts/logics_lint.py --require-status`
- `python3 logics/skills/logics-flow-manager/scripts/workflow_audit.py --group-by-doc`

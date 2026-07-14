# Changelog (`1.9.5 -> 1.10.0`)

## Major Highlights

- Made delivered digests more actionable by suppressing low-value authentication, tracking-preference, recap, and automated informational messages before they reach the final brief.
- Added privacy-safe digest usefulness telemetry, replay artifacts, and a local debug viewer for inspecting rendered daily and weekly digest scenarios.
- Improved email readability and Outlook dark-mode stability with stronger light-theme rendering guards and cleaner action-card presentation.
- Hardened runtime and release operations with Python 3.11+, CI coverage reporting, job endpoint rate limiting, safer SQL construction, PostgreSQL pooling, and explicit `main` plus `release` branch release handling.

## Version 1.10.0

### Delivered

- Added deterministic digest replay outputs, production-baseline metrics, debug JSON export, and `npm run digest:view` for local rendered email review.
- Expanded the digest intelligence path with richer bounded context, operational candidate balancing, decision-oriented summaries, continuity signals, owner-aware actions, and compact meeting conflict cues.
- Filtered noisy one-time-code, authentication, email-preference, and meeting-assistant recap messages so the digest spends less space on non-actions.
- Stabilized HTML email rendering across Outlook light and dark appearances.
- Documented the visual QA workflow, scheduler/deployment handoff, and Logics corpus for the actionability and usefulness improvement tracks.
- Clarified that production release publication updates both `main` and the deployed `release` branch.

### Validation

- `python3 -m pytest`
- `logics-manager lint --require-status`
- `logics-manager audit --group-by-doc`
- `logics-manager release validate 1.10.0`

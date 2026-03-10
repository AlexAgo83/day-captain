## item_071_day_captain_target_user_normalization_and_entrypoint_datetime_alignment - Normalize target-user identity and align datetime parsing across entrypoints
> From version: 1.5.0
> Status: Ready
> Understanding: 97%
> Confidence: 95%
> Progress: 0%
> Complexity: Medium
> Theme: Reliability
> Reminder: Update status/understanding/confidence/progress and linked task references when you edit this doc.

# Problem
- Target-user validation and resolution remain case-sensitive in places even though email-command routing already normalizes mailbox identifiers.
- CLI and hosted web entrypoints still parse datetimes differently from the shared model layer, so common `Z`-suffixed UTC timestamps can behave inconsistently across surfaces.

# Scope
- In:
  - consistent normalization of target-user identifiers across config, runtime, and email-command routing
  - alignment of CLI and hosted web datetime parsing with the shared model behavior
  - tests for case-only identity differences and `Z`-suffixed ISO datetimes
- Out:
  - broader identity resolution from external directories
  - redesign of email-command product behavior
  - timezone-policy changes beyond parser consistency

# Acceptance criteria
- AC1: Mailbox identifiers differing only by case do not cause false target-user rejection in supported multi-user flows.
- AC2: Email-command routing and target-user validation follow the same normalization policy.
- AC3: CLI and hosted web entrypoints accept the same standard ISO datetime forms as the shared model layer, including `Z`-suffixed UTC timestamps.
- AC4: Tests cover representative case-normalized identity resolution and entrypoint datetime parsing scenarios.

# AC Traceability
- Req034 AC4 -> This item is the dedicated target-user normalization slice. Proof: mailbox identifiers are normalized consistently across config and runtime here.
- Req034 AC5 -> This item explicitly covers parser alignment across model, CLI, and web entrypoints. Proof: shared ISO parsing behavior is aligned in this implementation slice.
- Req034 AC6 -> This item requires the relevant regression coverage. Proof: normalization and parser-alignment regressions need dedicated tests here.

# Links
- Request: `req_034_day_captain_hosted_runtime_fail_fast_and_identity_normalization`

# Priority
- Impact: Medium - these are avoidable correctness failures in multi-user and automation paths.
- Urgency: Medium - they are edge-case heavy but very visible when they trigger.

# Notes
- Derived from the project review of multi-user resolution and cross-entrypoint parsing consistency.

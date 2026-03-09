## item_050_day_captain_web_runtime_error_logging_and_docs_alignment - Add bounded web runtime error logging and align operator docs with the new preview/runtime contract
> From version: 1.4.0
> Status: Ready
> Understanding: 98%
> Confidence: 96%
> Progress: 0%
> Complexity: Medium
> Theme: Reliability
> Reminder: Update status/understanding/confidence/progress and linked task references when you edit this doc.

# Problem
- The web surface currently returns a bounded `internal_error` response for unexpected exceptions, but does not emit actionable runtime logs.
- That makes production diagnosis harder than necessary when the service fails outside the explicitly handled error classes.
- The operator docs also need to match the final preview-safe and hosted input contracts once they are corrected.

# Scope
- In:
  - emit bounded but actionable logs for unexpected web runtime failures
  - avoid leaking secrets or full inbound payloads
  - align docs and validation notes with the corrected preview and hosted-runtime behavior
- Out:
  - adding a full centralized observability platform
  - changing normal 4xx error semantics
  - redesigning the hosted endpoints

```mermaid
flowchart LR
    Runtime[Unexpected web exception] --> Log[Bounded error logging]
    Log --> Diagnose[Faster diagnosis]
    Diagnose --> Docs[Docs match real runtime behavior]
```

# Acceptance criteria
- AC1: Unexpected web 500s emit actionable server-side logs.
- AC2: The bounded HTTP error response is preserved.
- AC3: Docs and validation notes match the final preview/runtime contract.

# AC Traceability
- Req028 AC4 -> Scope explicitly adds web runtime observability while preserving the bounded HTTP response. Proof: item is the 500-logging slice.
- Req028 AC5 -> Scope explicitly updates docs/validation. Proof: operator-facing runtime contracts must stay synchronized.

# Links
- Request: `req_028_day_captain_preview_safety_and_web_runtime_observability`
- Primary task(s): `task_033_day_captain_preview_safety_and_web_runtime_observability_orchestration` (`Ready`)

# Priority
- Impact: Medium - poor observability slows recovery and diagnosis during production incidents.
- Urgency: Medium - not a feature blocker, but a meaningful operational gap.

# Notes
- Derived from `req_028_day_captain_preview_safety_and_web_runtime_observability`.
- The goal is better diagnosis, not verbose or unsafe logging.

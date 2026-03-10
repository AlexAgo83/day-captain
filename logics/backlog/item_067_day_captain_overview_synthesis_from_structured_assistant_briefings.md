## item_067_day_captain_overview_synthesis_from_structured_assistant_briefings - Day Captain overview synthesis from structured assistant briefings
> From version: 1.4.2
> Status: Done
> Understanding: 100%
> Confidence: 98%
> Progress: 100%
> Complexity: Medium
> Theme: Product Quality
> Reminder: Update status/understanding/confidence/progress and linked task references when you edit this doc.

# Problem
- `En bref` currently sits on top of older summary inputs, but the new product direction is for the overview to be built from structured assistant briefings for surfaced mail threads and meetings.
- If `En bref` is not re-based on the new structured outputs, the digest will mix two summary systems: richer per-object briefings below and an older mechanical overview above.
- The overview also needs to stay selective, surfacing only the important briefings rather than flattening every object into an equally weighted recap.

# Scope
- In:
  - rebuild `En bref` from structured mail-thread and meeting briefings
  - make the overview focus on the important surfaced briefings rather than all surfaced objects equally
  - preserve bounded overview behavior and deterministic fallback when structured assistant inputs are unavailable
- Out:
  - turning `En bref` into a full second digest
  - summarizing low-value surfaced noise in the overview by default
  - reopening unrelated visual layout work

```mermaid
flowchart LR
    Briefings[Structured assistant briefings] --> Important[Important surfaced briefings]
    Important --> Overview[En bref synthesis]
    Overview --> Digest[More coherent top summary]
```

# Acceptance criteria
- AC1: `En bref` is generated from the structured per-thread and per-meeting briefings rather than primarily from older excerpt-oriented summary inputs.
- AC2: The overview remains selective and focuses on important surfaced briefings instead of recapping every surfaced object equally.
- AC3: Deterministic fallback remains available when the structured overview path cannot be used.
- AC4: Tests cover representative overview synthesis and fallback behavior.

# AC Traceability
- Req033 AC6 -> Item scope explicitly regenerates `En bref` from important structured briefings. Proof: this item is the overview-synthesis slice.
- Req033 AC7 -> Acceptance criteria preserve bounded overview behavior and deterministic fallback. Proof: this item keeps the top-summary path practical and safe.
- Req033 AC8 -> Acceptance criteria require representative overview regression coverage. Proof: closure includes structured-input and fallback test cases.

# Links
- Request: `req_033_day_captain_per_thread_and_per_meeting_assistant_briefings_with_confidence_scoring`
- Primary task(s): `task_038_day_captain_assistant_briefings_confidence_and_overview_orchestration` (`Done`)

# Priority
- Impact: High - the overview is the first summary surface the user sees and must stay aligned with the new briefing system.
- Urgency: Medium - it depends conceptually on the underlying briefing layers but should be planned from the start.

# Notes
- Created on Tuesday, March 10, 2026 from product direction to rebuild `En bref` on top of structured assistant briefings instead of the older mechanical path.
- Closed on Tuesday, March 10, 2026 after rebuilding `En bref` on the structured briefing outputs with deterministic fallback retained.

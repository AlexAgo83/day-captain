## req_024_day_captain_digest_daily_weather_capsule - Day Captain digest daily weather capsule
> From version: 1.3.0
> Status: Done
> Understanding: 100%
> Confidence: 99%
> Complexity: Medium
> Theme: UX
> Reminder: Update status/understanding/confidence and references when you edit this doc.

# Needs
- Add a small daily weather capsule near the top of the digest so the brief feels more useful as a real morning companion.
- Place that weather signal before `En bref`, not lower in the digest where it would compete with action-oriented content.
- Keep the weather wording short and scannable, including a quick indication of whether the day is warmer or cooler than the previous day.

# Context
- The digest top area is now materially cleaner after the readability, visual-weight, and wording-polish passes.
- That leaves room for one bounded contextual signal above `En bref` without reintroducing a heavy header block.
- The requested user experience is specific:
  - show the weather for the current day
  - keep it brief
  - indicate whether it is warmer or colder than the previous day
  - render it before `En bref`
- This should remain a compact utility layer, not a new large forecast section.
- The main open design constraints are:
  - where the weather location comes from for a given digest target
  - what weather source/provider is used
  - how the capsule behaves when weather data is unavailable

# In scope
- add one lightweight weather capsule above `En bref`
- summarize the day with short weather copy
- include a simple warmer/cooler comparison versus the previous local day
- keep the capsule visually subordinate to the digest title and main action summary
- preserve Outlook-compatible rendering
- document any required config if a weather location or provider setting is introduced

# Out of scope
- adding a full hourly forecast
- adding a multi-day forecast section
- turning the digest into a travel or commute planner
- introducing rich weather graphics that are likely to render poorly in Outlook
- blocking digest delivery when weather data is unavailable

```mermaid
flowchart LR
    DigestTop[Digest top block] --> Weather[Weather capsule]
    Weather --> Summary[En bref]
    Weather --> Context[Useful morning context]
    Summary --> Priorities[Main priorities stay central]
```

# Acceptance criteria
- AC1: The delivered digest can render a small weather capsule before `En bref`.
- AC2: The weather capsule states the day’s weather in brief assistant-style wording rather than a dense raw weather report.
- AC3: The weather capsule includes a short warmer/cooler signal relative to the previous local day when both days are available.
- AC4: If weather data is unavailable, the digest still renders cleanly without breaking the top layout.
- AC5: The capsule remains visually light and does not reintroduce the heavy header feel removed in earlier digest-polish slices.
- AC6: Any new weather dependency or location-setting contract is documented before closure.

# Backlog traceability
- AC1 -> `item_037_day_captain_digest_weather_capsule_rendering_and_copy`. Proof: this item explicitly places the weather capsule before `En bref` in the delivered digest.
- AC2 -> `item_037_day_captain_digest_weather_capsule_rendering_and_copy`. Proof: this item explicitly keeps the weather wording short and assistant-like.
- AC3 -> `item_037_day_captain_digest_weather_capsule_rendering_and_copy`. Proof: this item explicitly adds a bounded warmer/cooler comparison versus the previous day.
- AC4 -> `item_038_day_captain_digest_weather_fallback_and_docs_validation`. Proof: this item explicitly keeps the digest layout clean when weather data is missing.
- AC5 -> `item_037_day_captain_digest_weather_capsule_rendering_and_copy`. Proof: this item explicitly keeps the capsule visually light in the top block.
- AC6 -> `item_036_day_captain_digest_weather_source_and_location_contract`. Proof: this item explicitly defines the source/location contract and `item_038` closes the docs path.

# Task traceability
- AC1 -> `task_029_day_captain_digest_weather_capsule_orchestration`. Proof: task `029` explicitly adds the weather capsule ahead of `En bref`.
- AC2 -> `task_029_day_captain_digest_weather_capsule_orchestration`. Proof: task `029` explicitly keeps the weather wording brief and product-like.
- AC3 -> `task_029_day_captain_digest_weather_capsule_orchestration`. Proof: task `029` explicitly adds the bounded warmer/cooler comparison.
- AC4 -> `task_029_day_captain_digest_weather_capsule_orchestration`. Proof: task `029` explicitly requires fallback-safe rendering when weather data is missing.
- AC5 -> `task_029_day_captain_digest_weather_capsule_orchestration`. Proof: task `029` explicitly preserves the lighter top-of-mail presentation.
- AC6 -> `task_029_day_captain_digest_weather_capsule_orchestration`. Proof: task `029` explicitly blocks closure until config/docs are updated.

# Delivery notes
- Preferred placement: between the as-of/perimeter metadata and `En bref`.
- Preferred tone:
  - short
  - useful
  - non-technical
- Example shape in French:
  - `Météo du jour: ciel couvert, 14°C. Un peu plus frais qu'hier.`
- Example shape in English:
  - `Today's weather: overcast, 57F. Slightly cooler than yesterday.`

# Risks and dependencies
- Weather is a time-sensitive external dependency, so provider behavior and response shape must be treated as unstable.
- A location contract may be needed if the digest user base is not tied to one fixed city.
- The comparison logic should remain bounded; a simple warmer/cooler delta is enough and avoids false precision.

# Definition of Ready (DoR)
- [x] Problem statement is explicit and user impact is clear.
- [x] Scope boundaries (in/out) are explicit.
- [x] Acceptance criteria are testable.
- [x] Known risks and dependency questions are listed.

# Backlog
- `item_036_day_captain_digest_weather_source_and_location_contract` - Define the weather provider/location contract for digest runs. Status: `Done`.
- `item_037_day_captain_digest_weather_capsule_rendering_and_copy` - Render the weather capsule before `En bref` with short copy and warmer/cooler delta. Status: `Done`.
- `item_038_day_captain_digest_weather_fallback_and_docs_validation` - Keep the digest clean when weather data is missing and close docs/validation. Status: `Done`.
- `task_029_day_captain_digest_weather_capsule_orchestration` - Orchestrate the weather capsule slice end to end. Status: `Done`.

# Notes
- Created on Monday, March 9, 2026 from direct product feedback after the digest top block reached an acceptable polish level.
- This request intentionally treats weather as a bounded contextual enhancement, not as a new core decision section.
- Decomposed on Monday, March 9, 2026 into provider/location contract, capsule rendering/copy, and fallback/docs closure slices.
- Closed on Monday, March 9, 2026 after live Render deployment and Outlook validation of the weather capsule before `En bref`.

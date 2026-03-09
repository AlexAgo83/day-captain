## item_044_day_captain_llm_source_open_control_preservation - Preserve source-open controls through LLM rewriting
> From version: 1.3.1
> Status: Ready
> Understanding: 97%
> Confidence: 95%
> Progress: 0%
> Complexity: Low
> Theme: Reliability
> Reminder: Update status/understanding/confidence/progress and linked task references when you edit this doc.

# Problem
- Digest cards can render Outlook source-open controls from `DigestEntry.source_url`.
- The LLM wording path currently rebuilds entries without carrying that field forward.
- As soon as an item is rewritten, the open control can silently disappear even though the underlying source link still exists.

# Scope
- In:
  - preserve `source_url` and equivalent source-open metadata through wording and overview rewrite paths
  - confirm rewritten items still render the expected Outlook open controls
  - add regression coverage for this behavior
- Out:
  - redesigning the open-control UX
  - adding new kinds of source links
  - broad LLM feature changes unrelated to metadata preservation

```mermaid
flowchart LR
    ScoredItem[Scored digest item with source_url] --> Rewrite[LLM wording or overview rewrite]
    Rewrite --> Preserved[Preserve source metadata]
    Preserved --> Render[Render Outlook open control]
```

# Acceptance criteria
- AC1: LLM-rewritten digest items preserve `source_url`.
- AC2: Outlook source-open controls remain available after rewriting.
- AC3: Regression tests cover the preserved metadata path.

# AC Traceability
- Req026 AC4 -> Scope explicitly preserves source-open metadata through rewrite paths. Proof: item prevents open-control regression.
- Req026 AC5 -> Scope explicitly requires regression tests. Proof: item closes only with coverage.

# Links
- Request: `req_026_day_captain_runtime_contract_and_digest_cursor_reliability`
- Primary task(s): `task_031_day_captain_runtime_contract_and_digest_cursor_reliability_orchestration` (`Ready`)

# Priority
- Impact: Medium - the feature remains present in the renderer but becomes unreliable in LLM-enabled runs.
- Urgency: Medium - this is a regression on a user-visible control rather than a startup blocker.

# Notes
- Derived from `req_026_day_captain_runtime_contract_and_digest_cursor_reliability`.
- This slice should stay narrowly focused on metadata preservation, not wording quality.

## item_119_make_the_top_summary_decision_oriented - Make the top summary decision-oriented
> From version: 1.0.0
> Schema version: 1.0
> Status: Done
> Understanding: 90%
> Confidence: 85%
> Progress: 100%
> Complexity: Medium
> Theme: UX
> Reminder: Update status/understanding/confidence/progress and linked request/task references when you edit this doc.

# Problem
- The current deterministic overview summarizes one or two section fragments, and the LLM overview receives at most one compact item per section.
- Users need to know what changed, what they personally need to do, what is blocked elsewhere, and whether the rest can be ignored.
- A shallow but polished summary can make the whole digest feel useless even when individual cards are correct.

# Scope
- In:
  - Define a stable summary contract with four optional slots: changed since last digest, required user action, waiting/blocked elsewhere, and safe-to-ignore/no-meaningful-work.
  - Pass structured counts and representative evidence to deterministic and LLM overview engines.
  - Use no-meaningful-work wording when the evidence gate renders no operational cards.
  - Keep summary content short enough for email preview but specific enough to name the operational category, not raw private content.
  - Add French and English copy tests for the summary contract.
- Out:
  - Generating long executive narratives.
  - Listing every card in the top summary.
  - Exposing raw mailbox text in summary telemetry or docs.

# Acceptance criteria
- AC1: Summary tests cover changed work, user action, waiting elsewhere, and no-meaningful-work outputs.
- AC2: Deterministic fallback follows the same summary slots as the LLM path.
- AC3: The summary does not claim there is action when only unsupported watch content exists.
- AC4: Existing daily/weekly subject and renderer tests pass.

# Delivery notes
- Deterministic overview now reserves space for continuity and waiting signals after the primary operational sentence.
- No-meaningful-work output remains concise and does not pad weak cards into the digest.
- Existing LLM overview behavior remains compatible while deterministic fallback carries the same decision slots when LLM is disabled or fails.
- Validation: summary, replay, renderer, and full discovery tests pass.

# AC Traceability
- request-AC8 -> This backlog slice. Proof: AC1: Summary tests cover changed work, user action, waiting elsewhere, and no-meaningful-work outputs.
- request-AC9 -> This backlog slice. Proof: AC2: Deterministic fallback follows the same summary slots as the LLM path.
- request-AC10 -> This backlog slice. Proof: AC3: The summary does not claim there is action when only unsupported watch content exists.

# Decision framing
- Product framing: Not needed
- Architecture framing: Not needed

# Links
- Product brief(s): `prod_003_day_captain_useful_decision_brief`
- Architecture decision(s): (none yet)
- Request: `req_056_day_captain_digest_usefulness_intelligence`
- Primary task(s): `task_053_orchestrate_digest_usefulness_intelligence_improvements`

# AI Context
- Summary: Make the top summary decision-oriented
- Keywords: scaffolded-backlog, make the top summary decision-oriented, implementation-ready
- Use when: Implementing the scaffolded slice for Make the top summary decision-oriented.
- Skip when: The change belongs to another backlog slice.

# Priority
- Priority: Medium
- Rationale: Set by scaffold input or defaulted for grooming.

# Notes
- Task `task_053_orchestrate_digest_usefulness_intelligence_improvements` was finished via `logics-manager flow finish task` on 2026-07-14.

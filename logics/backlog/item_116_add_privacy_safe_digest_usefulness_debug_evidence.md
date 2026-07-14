## item_116_add_privacy_safe_digest_usefulness_debug_evidence - Add privacy-safe digest usefulness debug evidence
> From version: 1.0.0
> Schema version: 1.0
> Status: Done
> Understanding: 90%
> Confidence: 85%
> Progress: 100%
> Complexity: Medium
> Theme: Observability
> Reminder: Update status/understanding/confidence/progress and linked request/task references when you edit this doc.

# Problem
- When a delivered digest feels useless, the current preview gives rendered HTML/text but not a clear explanation of why each card was included.
- Without per-card and suppression evidence, developers tune scoring from vibes or real mailbox inspection.
- Existing metrics prove shorter output and fewer generic actions, but they do not prove usefulness.

# Scope
- In:
  - Extend digest replay or preview export with a content-free debug JSON artifact.
  - For rendered cards, include section, score bucket, reason codes, owner category, confidence label, continuity state, source kind, action-present flag, due-present flag, and source-open availability.
  - For suppressed candidates, report aggregate counters by suppression reason only.
  - Add usefulness metrics for concrete next step, owner clarity, due signal, changed/overdue state, critical failure, meeting conflict, unsupported watch, and no-meaningful-work days.
  - Extend synthetic replay with cases that intentionally produce useless-looking output before the intelligence fixes.
  - Document how to run the debug viewer and inspect the debug JSON without touching real mailbox content.
- Out:
  - Exporting raw subjects, bodies, previews, names, addresses, or client identifiers from production mail.
  - Adding tracking pixels or covert read/open tracking.
  - Changing scoring behavior in this observability slice except where needed to expose existing evidence.

# Acceptance criteria
- AC1: `digest-replay` can write a debug JSON artifact next to HTML/text output using only synthetic content.
- AC2: Debug output explains every rendered synthetic card without raw mailbox fields.
- AC3: Usefulness metrics distinguish useful cards from unsupported watch cards and generic actions.
- AC4: Tests prove no real mailbox-derived text is required for the debug artifact.
- AC5: Existing replay metrics still pass and full unit discovery remains green.

# Delivery notes
- Implemented `digest_debug_report` and usefulness metrics version `1.1`.
- `digest-replay --output-dir` writes `debug.json` next to HTML/text artifacts.
- Debug evidence reports section, source kind, score bucket, reason codes, owner, confidence, continuity, action/due/source-open booleans, guardrail state, unsupported-watch state, and suppression counters without raw mailbox content.
- Validation: focused metrics/replay tests pass; full unit discovery passes with 278 tests.

# AC Traceability
- request-AC1 -> This backlog slice. Proof: AC1: `digest-replay` can write a debug JSON artifact next to HTML/text output using only synthetic content.
- request-AC2 -> This backlog slice. Proof: AC2: Debug output explains every rendered synthetic card without raw mailbox fields.
- request-AC3 -> This backlog slice. Proof: AC3: Usefulness metrics distinguish useful cards from unsupported watch cards and generic actions.
- request-AC5 -> This backlog slice. Proof: AC4: Tests prove no real mailbox-derived text is required for the debug artifact.
- request-AC10 -> This backlog slice. Proof: AC5: Existing replay metrics still pass and full unit discovery remains green.

# Decision framing
- Product framing: Not needed
- Architecture framing: Not needed

# Links
- Product brief(s): `prod_003_day_captain_useful_decision_brief`
- Architecture decision(s): (none yet)
- Request: `req_056_day_captain_digest_usefulness_intelligence`
- Primary task(s): `task_053_orchestrate_digest_usefulness_intelligence_improvements`

# AI Context
- Summary: Add privacy-safe digest usefulness debug evidence
- Keywords: scaffolded-backlog, add privacy-safe digest usefulness debug evidence, implementation-ready
- Use when: Implementing the scaffolded slice for Add privacy-safe digest usefulness debug evidence.
- Skip when: The change belongs to another backlog slice.

# Priority
- Priority: High
- Rationale: Set by scaffold input or defaulted for grooming.

# Notes
- Task `task_053_orchestrate_digest_usefulness_intelligence_improvements` was finished via `logics-manager flow finish task` on 2026-07-14.

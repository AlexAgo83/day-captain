## item_117_add_bounded_rich_context_for_high_potential_candidates - Add bounded rich context for high-potential candidates
> From version: 1.0.0
> Schema version: 1.0
> Status: Ready
> Understanding: 90%
> Confidence: 85%
> Progress: 0%
> Complexity: High
> Theme: Intelligence
> Reminder: Update status/understanding/confidence/progress and linked request/task references when you edit this doc.

# Problem
- The current scorer and LLM wording mostly see subject and body_preview, so useful details hidden in the email body or recent thread can be missed.
- Fetching full context for every message would increase cost, latency, privacy exposure, and Graph complexity.
- A useful assistant needs enough evidence for the few candidates that matter without turning storage or telemetry into a mailbox archive.

# Scope
- In:
  - Introduce a bounded enrichment step after initial scoring and before LLM wording/final selection.
  - Select enrichment candidates by cheap signals: critical/transactional guardrail, user-owned action candidate, flagged mail, explicit due hint, changed continuity, and meeting conflict context.
  - Fetch or assemble at most a configured small number of richer contexts per digest and cap characters per candidate.
  - Prefer existing stored thread metadata and Graph fields before adding new storage columns.
  - Redact or omit secrets and authentication content before LLM input.
  - Keep enriched raw context in memory only unless the data is synthetic test content.
  - Expose content-free enrichment counters in debug output.
- Out:
  - Persisting full message bodies for production mail.
  - Embedding or indexing mailbox content.
  - Fetching attachments or document contents.
  - Making LLM use mandatory for digest generation.

# Acceptance criteria
- AC1: Tests prove only bounded high-potential candidates are enriched.
- AC2: Enrichment improves a synthetic fixture where the preview is vague but the bounded body/thread context contains the actionable detail.
- AC3: Authentication or one-time-code content is suppressed before enrichment output can reach LLM input or debug evidence.
- AC4: Config defaults keep enrichment bounded and disabled or minimal where Graph support is unavailable.
- AC5: No production raw body content is written to storage, telemetry, docs, or replay artifacts.

# AC Traceability
- request-AC4 -> This backlog slice. Proof: AC1: Tests prove only bounded high-potential candidates are enriched.
- request-AC5 -> This backlog slice. Proof: AC2: Enrichment improves a synthetic fixture where the preview is vague but the bounded body/thread context contains the actionable detail.
- request-AC6 -> This backlog slice. Proof: AC3: Authentication or one-time-code content is suppressed before enrichment output can reach LLM input or debug evidence.
- request-AC10 -> This backlog slice. Proof: AC4: Config defaults keep enrichment bounded and disabled or minimal where Graph support is unavailable.

# Decision framing
- Product framing: Not needed
- Architecture framing: Not needed

# Links
- Product brief(s): `prod_003_day_captain_useful_decision_brief`
- Architecture decision(s): (none yet)
- Request: `req_056_day_captain_digest_usefulness_intelligence`
- Primary task(s): `task_053_orchestrate_digest_usefulness_intelligence_improvements`

# AI Context
- Summary: Add bounded rich context for high-potential candidates
- Keywords: scaffolded-backlog, add bounded rich context for high-potential candidates, implementation-ready
- Use when: Implementing the scaffolded slice for Add bounded rich context for high-potential candidates.
- Skip when: The change belongs to another backlog slice.

# Priority
- Priority: High
- Rationale: Set by scaffold input or defaulted for grooming.

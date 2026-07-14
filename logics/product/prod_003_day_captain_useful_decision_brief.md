## prod_003_day_captain_useful_decision_brief - Day Captain useful decision brief
> Date: 2026-07-14
> Status: Settled
> Related request: `req_056_day_captain_digest_usefulness_intelligence`
> Related backlog: `item_116_add_privacy_safe_digest_usefulness_debug_evidence`, `item_117_add_bounded_rich_context_for_high_potential_candidates`, `item_118_select_llm_and_final_digest_inputs_by_operational_value`, `item_119_make_the_top_summary_decision_oriented`
> Related task: `task_053_orchestrate_digest_usefulness_intelligence_improvements`
> Related architecture: (none yet)
> Reminder: Update status, linked refs, scope, decisions, success signals, and open questions when you edit this doc.

# Overview
Upgrade Day Captain from a concise mailbox digest into a decision brief that explains why each item matters, uses enough context for the few candidates that deserve it, and admits when there is nothing worth the user's attention.

# Goals
- Increase perceived usefulness by surfacing fewer unsupported watch items and more evidence-backed decisions, actions, failures, deadlines, and conflicts.
- Create a privacy-safe debugging loop for every rendered card and every suppressed candidate.
- Use richer context surgically after the cheap candidate pass instead of broad mailbox ingestion.
- Improve LLM input selection without adding a new ranking service.
- Make empty or low-signal days honest and concise.

# Non-goals
- Building a general task manager or autonomous email agent.
- Reading or storing every full email body by default.
- Persisting raw mailbox content in debug artifacts, telemetry, tests, docs, or Logics evidence.
- Replacing Microsoft Graph, current storage adapters, current rendering, or existing delivery contracts.
- Adding a new external analytics or ranking service.

# Scope and guardrails
- In: scaffolded request, product, backlog, orchestration task, validation, and handoff context.
- Out: unrelated workflow docs and implementation of generated tasks.

# Key product decisions
- Use structured input as the source of truth for generated docs.
- Keep generated write paths local and repo-bounded.

# Success signals
- Generated docs pass lint and audit without broad manual rewrites.
- Context-pack output can be handed to an implementation agent directly.

# References
- Product back-reference: `req_056_day_captain_digest_usefulness_intelligence`
- Task back-reference: `task_053_orchestrate_digest_usefulness_intelligence_improvements`

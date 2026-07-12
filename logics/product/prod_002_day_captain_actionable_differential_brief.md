## prod_002_day_captain_actionable_differential_brief - Day Captain actionable differential brief
> Date: 2026-07-12
> Status: Proposed
> Related request: `req_055_day_captain_production_digest_actionability_improvement`
> Related backlog: `item_109_reduce_digest_noise_and_enforce_concise_section_budgets`, `item_110_generate_concrete_owner_aware_actions_and_deadlines`, `item_111_turn_recent_run_memory_into_a_differential_commitment_view`, `item_112_make_upcoming_meetings_preparation_and_conflict_aware`, `item_113_improve_digest_presentation_personalization_and_usefulness_telemetry`
> Related task: `task_050_orchestrate_production_digest_actionability_improvements`
> Related architecture: (none yet)
> Reminder: Update status, linked refs, scope, decisions, success signals, and open questions when you edit this doc.

# Overview
Make each digest answer what changed, what the recipient personally needs to do, when it is due, and what can safely be ignored.

# Goals
- Cut routine digest reading effort by reducing repeated and generic content.
- Prioritize concrete user-owned commitments, deadlines, delivery failures, and meeting preparation.
- Use stable thread continuity to explain changes across runs instead of repeating complete mailbox snapshots.
- Keep ambient context such as weather and external news subordinate to operational work.
- Measure whether surfaced cards lead to useful opens, recalls, feedback, or completed follow-up.

# Non-goals
- Building a general-purpose task-management platform.
- Automatically sending replies, accepting meetings, or completing commitments on behalf of a user.
- Replacing Microsoft Graph, the existing delivery adapter, or the current storage abstraction.
- Adding a new machine-learning service solely for ranking or confidence calibration.
- Persisting raw mailbox content in analytics or exposing production identities in fixtures and documentation.

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
- Product back-reference: `req_055_day_captain_production_digest_actionability_improvement`
- Task back-reference: `task_050_orchestrate_production_digest_actionability_improvements`

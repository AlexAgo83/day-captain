## task_050_orchestrate_production_digest_actionability_improvements - Orchestrate production digest actionability improvements
> From version: 1.0.0
> Schema version: 1.0
> Status: Ready
> Understanding: 90%
> Confidence: 85%
> Progress: 0%
> Complexity: Medium
> Theme: Implementation delivery
> Reminder: Update status/understanding/confidence/progress and linked request/backlog references when you edit this doc.

# Context
- Orchestrate the scaffolded request chain and keep sibling implementation slices linked.

# Plan
- [ ] 1. Capture anonymized baseline fixtures and metrics that reproduce the production audit findings without copying real mailbox content or identities.
- [ ] 2. Deliver the concise section budgets, unread-score removal, noise filters, transactional failure priority, empty-section omission, and ambient-content ordering as the first low-risk slice.
- [ ] 3. Implement owner-aware concrete actions, automatic-reply handling, deadline extraction, confidence categories, and stricter suspicious-mail evidence rules.
- [ ] 4. Change recent memory to use stable thread identity, suppress unchanged cards, render delta counts, and expose cleared items as compact resolved signals.
- [ ] 5. Add evidence-based meeting preparation and conflict detection without creating actions for context-free meetings or presence events.
- [ ] 6. Differentiate daily and weekly presentation, validate weather, constrain relevant external news, and add content-free usefulness feedback and metrics.
- [ ] 7. Run focused tests after each slice, then the full test suite, Logics flow validation, lint, and audit before closeout; record before/after brief-size and repetition metrics.
- [ ] GATE: do not close until lint, audit, and scaffold validation pass.

# Backlog
- `item_109_reduce_digest_noise_and_enforce_concise_section_budgets`
- `item_110_generate_concrete_owner_aware_actions_and_deadlines`
- `item_111_turn_recent_run_memory_into_a_differential_commitment_view`
- `item_112_make_upcoming_meetings_preparation_and_conflict_aware`
- `item_113_improve_digest_presentation_personalization_and_usefulness_telemetry`

# Definition of Done (DoD)
- [ ] Generated request, product, backlog, and task docs are present.
- [ ] Context-pack handoff is available when requested.
- [ ] Validation passes.

# AC Traceability
- request-AC1 -> This task. Proof: scaffold command generated the request-chain corpus.
- request-AC4 -> This task. Proof: optional context-pack handoff is supported.
- request-AC6 -> This task. Proof: dry-run and collision checks bound file changes.
- request-AC8 -> This task. Proof: CLI help documents the one-pass scaffold workflow.

# Validation
- Run `python3 -m logics_manager lint --require-status`.
- Run scaffold command tests.

# Report
- Implementation complete.

# AI Context
- Summary: Orchestrate production digest actionability improvements
- Keywords: scaffolded-task, request-chain-scaffold, orchestration
- Use when: Coordinating implementation of a scaffolded request chain.
- Skip when: Working on one isolated sibling slice.

# Links
- Request: `req_055_day_captain_production_digest_actionability_improvement`
- Product brief(s): `prod_002_day_captain_actionable_differential_brief`
- Architecture decision(s): (none yet)

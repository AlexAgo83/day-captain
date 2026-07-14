## task_053_orchestrate_digest_usefulness_intelligence_improvements - Orchestrate digest usefulness intelligence improvements
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
- [ ] 1. Add content-free debug evidence and usefulness metrics to replay/preview so bad digests can be diagnosed without real mailbox content.
- [ ] 2. Expand synthetic replay with useless, useful, no-work, wrong-shortlist, and rich-context cases.
- [ ] 3. Implement bounded rich-context enrichment for high-potential candidates before optional LLM wording.
- [ ] 4. Replace raw-order LLM shortlist selection with a balanced operational selector and add final evidence gates.
- [ ] 5. Update deterministic and LLM top summary behavior to follow the decision-oriented summary contract.
- [ ] 6. Run focused tests, full unit discovery, replay metrics, visual preview, Logics validation, lint, and audit before closeout.
- [ ] ADR 009 checkpoint: update affected Logics docs during each meaningful wave and leave the repo commit-ready.
- [ ] Keep commit creation under operator control; do not force one commit per micro-step.
- [ ] GATE: do not close until lint, audit, and scaffold validation pass.

# Backlog
- `item_116_add_privacy_safe_digest_usefulness_debug_evidence`
- `item_117_add_bounded_rich_context_for_high_potential_candidates`
- `item_118_select_llm_and_final_digest_inputs_by_operational_value`
- `item_119_make_the_top_summary_decision_oriented`

# Definition of Done (DoD)
- [ ] Generated request, product, backlog, and task docs are present.
- [ ] Context-pack handoff is available when requested.
- [ ] Validation passes.
- [ ] Meaningful waves followed ADR 009: affected docs updated and the repo left commit-ready without automatic commits.

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
- Summary: Orchestrate digest usefulness intelligence improvements
- Keywords: scaffolded-task, request-chain-scaffold, orchestration
- Use when: Coordinating implementation of a scaffolded request chain.
- Skip when: Working on one isolated sibling slice.

# Links
- Request: `req_056_day_captain_digest_usefulness_intelligence`
- Product brief(s): `prod_003_day_captain_useful_decision_brief`
- Architecture decision(s): (none yet)

## task_053_orchestrate_digest_usefulness_intelligence_improvements - Orchestrate digest usefulness intelligence improvements
> From version: 1.0.0
> Schema version: 1.0
> Status: Done
> Understanding: 90%
> Confidence: 85%
> Progress: 100%
> Complexity: Medium
> Theme: Implementation delivery
> Reminder: Update status/understanding/confidence/progress and linked request/backlog references when you edit this doc.

# Context
- Orchestrate the scaffolded request chain and keep sibling implementation slices linked.

# Plan
- [x] 1. Add content-free debug evidence and usefulness metrics to replay/preview so bad digests can be diagnosed without real mailbox content.
- [x] 2. Expand synthetic replay with useless, useful, no-work, wrong-shortlist, and rich-context cases.
- [x] 3. Implement bounded rich-context enrichment for high-potential candidates before optional LLM wording.
- [x] 4. Replace raw-order LLM shortlist selection with a balanced operational selector and add final evidence gates.
- [x] 5. Update deterministic and LLM top summary behavior to follow the decision-oriented summary contract.
- [x] 6. Run focused tests, full unit discovery, replay metrics, visual preview, Logics validation, lint, and audit before closeout.
- [x] ADR 009 checkpoint: update affected Logics docs during each meaningful wave and leave the repo commit-ready.
- [x] Keep commit creation under operator control; do not force one commit per micro-step.
- [x] GATE: do not close until lint, audit, and scaffold validation pass.

# Backlog
- `item_116_add_privacy_safe_digest_usefulness_debug_evidence`
- `item_117_add_bounded_rich_context_for_high_potential_candidates`
- `item_118_select_llm_and_final_digest_inputs_by_operational_value`
- `item_119_make_the_top_summary_decision_oriented`

# Definition of Done (DoD)
- [x] Generated request, product, backlog, and task docs are present.
- [x] Context-pack handoff is available when requested.
- [x] Validation passes.
- [x] Meaningful waves followed ADR 009: affected docs updated and the repo left commit-ready without automatic commits.

# AC Traceability
- request-AC1 -> This task. Proof: `digest-replay --output-dir` writes `debug.json` with content-free per-card reasons, score buckets, owner category, confidence, continuity, source kind, action/due/source-open booleans, and suppression counters.
- request-AC2 -> This task. Proof: synthetic replay now covers sensitive suppression, noise, owned deadline, transactional failure, continuity, meeting conflict, no-meaningful-work, rich-context, and balanced-shortlist cases.
- request-AC3 -> This task. Proof: digest metrics version `1.1` reports concrete next steps, owner clarity, due signals, change signals, critical failures, meeting conflicts, unsupported watch, and no-meaningful-work briefs.
- request-AC4 -> This task. Proof: `enrich_digest_candidates` enriches only bounded high-potential message candidates from explicit synthetic rich context before optional LLM wording.
- request-AC5 -> This task. Proof: debug metrics omit raw titles, summaries, previews, addresses, and bodies; rich context is synthetic-only and is not persisted as raw debug output.
- request-AC6 -> This task. Proof: `LlmDigestWordingEngine` now uses a balanced shortlist for transactional failures, user/shared actions, continuity, meeting conflicts, and high-confidence watch items before raw-score leftovers.
- request-AC7 -> This task. Proof: `filter_digest_items_for_usefulness` downgrades generic/empty action cards and suppresses unsupported watch cards while preserving guardrails.
- request-AC8 -> This task. Proof: deterministic overview adds changed/open and waiting-on-someone-else slots while preserving no-meaningful-work fallback.
- request-AC9 -> This task. Proof: replay includes a no-work digest with no padded operational cards and a concise top summary.
- request-AC10 -> This task. Proof: focused suites and full unit discovery pass; Logics validation/lint/audit are the remaining closeout gate.

# Validation
- PASS: `python3 -m unittest tests.test_digest_metrics tests.test_replay tests.test_llm tests.test_app`.
- PASS: `python3 -m unittest tests.test_llm tests.test_replay tests.test_digest_renderer tests.test_digest_metrics`.
- PASS: `PYTHONPATH=src python3 -m day_captain digest-replay --output-dir tmp/usefulness-check`; metrics version `1.1`, 5 synthetic briefs, zero generic actions, one no-meaningful-work brief, and passing production baseline gate.
- PASS: `python3 -m unittest discover -s tests` ran 278 tests successfully.
- PASS: `logics-manager flow validate req_056_day_captain_digest_usefulness_intelligence --apply-fixes`.
- PASS: `logics-manager lint --require-status`.
- PASS: `logics-manager audit --group-by-doc` with one non-blocking product Mermaid warning.
- Finish workflow executed on 2026-07-14.
- Linked backlog/request close verification passed.

# Report
- 2026-07-14: Wave 1 added content-free debug evidence and usefulness metrics. `digest-replay --output-dir` now writes `debug.json`, and `digest_metrics` version `1.1` reports actionable quality counters in addition to the existing production gate metrics.
- 2026-07-14: Wave 2 expanded identity-free replay from 3 to 5 briefs, adding no-meaningful-work and synthetic rich-context cases while preserving authentication suppression, noise filtering, owned deadline, transactional failure, continuity, and meeting conflict coverage.
- 2026-07-14: Wave 3 added bounded synthetic rich-context enrichment before optional LLM wording and a conservative evidence gate that downgrades generic/empty action cards and suppresses unsupported watch cards without weakening critical guardrails.
- 2026-07-14: Wave 4 changed LLM wording shortlist selection from raw-order only to an operational mix and added deterministic summary slots for changed/open work and waiting-on-someone-else, while keeping no-work output concise.
- 2026-07-14: Focused tests, full unit discovery, replay metrics, Logics validation, lint, and audit passed; commit remains.
- Finished on 2026-07-14.
- Linked backlog item(s): `item_116_add_privacy_safe_digest_usefulness_debug_evidence`, `item_117_add_bounded_rich_context_for_high_potential_candidates`, `item_118_select_llm_and_final_digest_inputs_by_operational_value`, `item_119_make_the_top_summary_decision_oriented`
- Related request(s): `req_056_day_captain_digest_usefulness_intelligence`

# AI Context
- Summary: Orchestrate digest usefulness intelligence improvements
- Keywords: scaffolded-task, request-chain-scaffold, orchestration
- Use when: Coordinating implementation of a scaffolded request chain.
- Skip when: Working on one isolated sibling slice.

# Links
- Request: `req_056_day_captain_digest_usefulness_intelligence`
- Product brief(s): `prod_003_day_captain_useful_decision_brief`
- Architecture decision(s): (none yet)

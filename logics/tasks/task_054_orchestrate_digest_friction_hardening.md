## task_054_orchestrate_digest_friction_hardening - Orchestrate digest friction hardening
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
- [ ] 1. Start with the authentication suppression gap because it is the only security-sensitive defect and should be fixed at the earliest shared boundary.
- [ ] 2. Add synthetic replay and focused regression fixtures before changing renderer behavior so sensitive and UX gates are measurable.
- [ ] 3. Tighten daily selection, external-news inclusion, confidence rendering, and top-summary wording using existing scoring and rendering primitives before adding fields.
- [ ] 4. Polish HTML and text rendering spacing/control grouping with small renderer assertions instead of broad visual infrastructure.
- [ ] 5. Add content-free sender delivery-count diagnostics for duplicate/missing send investigation without mailbox content.
- [ ] 6. Run focused tests for sensitive suppression, renderer output, replay, metrics, scheduler/audit diagnostics, then run the full suite.
- [ ] 7. Run Logics flow validation, lint, audit, index/context-pack refresh, and record only public-safe aggregate validation evidence.
- [ ] ADR 009 checkpoint: update affected Logics docs during each meaningful wave and leave the repo commit-ready.
- [ ] Keep commit creation under operator control; do not force one commit per micro-step.
- [ ] GATE: do not close until lint, audit, and scaffold validation pass.

# Backlog
- `item_120_close_authentication_message_suppression_gaps`
- `item_121_make_daily_output_a_strict_command_brief`
- `item_122_polish_outlook_and_text_rendering_ergonomics`
- `item_123_diagnose_sender_delivery_count_anomalies_without_mailbox_content`

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
- Summary: Orchestrate digest friction hardening
- Keywords: scaffolded-task, request-chain-scaffold, orchestration
- Use when: Coordinating implementation of a scaffolded request chain.
- Skip when: Working on one isolated sibling slice.

# Links
- Request: `req_057_day_captain_digest_friction_hardening`
- Product brief(s): `prod_004_day_captain_strict_decision_brief`
- Architecture decision(s): (none yet)

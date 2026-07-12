## task_050_orchestrate_production_digest_actionability_improvements - Orchestrate production digest actionability improvements
> From version: 1.0.0
> Schema version: 1.0
> Status: In progress
> Understanding: 100
> Confidence: 98
> Progress: 99
> Complexity: High
> Theme: Implementation delivery
> Reminder: Update status/understanding/confidence/progress and linked request/backlog references when you edit this doc.
> Owner: codex-work6

# Context
- Orchestrate the production-audit-driven request chain, coordinate the security and rollout sibling tasks, and preserve a single measurable baseline across all implementation slices.

# Plan
- [ ] 1. Capture anonymized baseline fixtures and metrics for the baseline stable production audit without copying real mailbox content or identities.
- [ ] 2. Deliver the concise section budgets, unread-score removal, noise filters, transactional failure priority, empty-section omission, and ambient-content ordering as the first low-risk slice.
- [ ] 3. Implement owner-aware concrete actions, automatic-reply handling, deadline extraction, confidence categories, and stricter suspicious-mail evidence rules.
- [ ] 4. Change recent memory to use stable thread identity, suppress unchanged cards, render delta counts, and expose cleared items as compact resolved signals.
- [ ] 5. Add evidence-based meeting preparation and conflict detection without creating actions for context-free meetings or presence events.
- [ ] 6. Differentiate daily and weekly presentation, validate weather, constrain/deduplicate relevant external news, and add reversible content-free usefulness feedback and metrics.
- [ ] 7. Coordinate the sensitive-content/application-access task and the replay/visual-QA/safe-rollout task before enabling production delivery.
- [ ] 8. Run focused tests after each slice, the full test suite, rendered visual QA, and an optional live send only to the explicitly authorized test mailbox; then run Logics validation and record before/after metrics.
- [ ] GATE: do not close until lint, audit, and scaffold validation pass.

# Backlog
- `item_109_reduce_digest_noise_and_enforce_concise_section_budgets`
- `item_110_generate_concrete_owner_aware_actions_and_deadlines`
- `item_111_turn_recent_run_memory_into_a_differential_commitment_view`
- `item_112_make_upcoming_meetings_preparation_and_conflict_aware`
- `item_113_improve_digest_presentation_personalization_and_usefulness_telemetry`

# Definition of Done (DoD)
- [ ] Anonymized regression fixtures reproduce the audited noise, ownership, repetition, meeting, and presentation failures.
- [ ] Backlog items 109 through 115 meet their acceptance criteria without weakening multi-user isolation or security guardrails.
- [ ] Before-and-after metrics demonstrate at least 40% shorter median visible briefs, 80% fewer generic actions, zero surfaced authentication secrets, and fewer unchanged repeated cards.
- [ ] Focused tests, the full test suite, rendered visual QA, and the single-recipient live test when needed all pass without contacting other recipients.
- [ ] Flow validation, lint, audit, and context-pack refresh pass at closeout.

# AC Traceability
- request-AC1 -> Plan step 7. Proof deferred to the sensitive-content boundary task and regression fixtures.
- request-AC2 -> Plan steps 2 and 4. Proof deferred to section-budget, noise-filter, and unchanged-item suppression tests.
- request-AC3 -> Plan step 3. Proof deferred to owner/action/deadline fixtures.
- request-AC4 -> Plan steps 2 and 3. Proof deferred to transactional failure and overdue ordering tests.
- request-AC5 -> Plan step 4. Proof deferred to stable-thread continuity and state-transition tests.
- request-AC6 -> Plan step 5. Proof deferred to meeting preparation, conflict, and placeholder tests.
- request-AC7 -> Plan steps 3 and 7. Proof deferred to confidence-category and suspicious-mail evidence tests.
- request-AC8 -> Plan steps 2 and 6. Proof deferred to daily/weekly renderer, weather/news, and empty-section tests.
- request-AC9 -> Plan step 6. Proof deferred to reversible preference and feedback tests.
- request-AC10 -> Plan steps 6 and 8. Proof deferred to content-free telemetry tests and audit metrics.
- request-AC11 -> Plan step 7. Proof deferred to application-access, retention, and content-free diagnostic evidence.
- request-AC12 -> Plan steps 1 through 8. Proof deferred to anonymized replay and full-suite results.
- request-AC13 -> Plan step 8. Proof deferred to rendered artifacts and the authorized-recipient-only delivery log.
- request-AC14 -> Plan steps 1, 7, and 8. Proof deferred to shadow comparison and post-release aggregate audit.
- request-AC1 -> This task. Proof: synthetic secret tests prove authentication content is absent from storage, LLM input, payloads, and persisted runs; task 051 is Done.
- request-AC2 -> This task. Proof: renderer budget and noise-filter tests enforce 3/3/2/4 limits, informational unread state, and unchanged low-signal suppression.
- request-AC3 -> This task. Proof: owner/action tests cover concrete verbs, objects, counterparties, evidence metadata, explicit due hints, and other-owned demotion.
- request-AC4 -> This task. Proof: transactional failure and deadline fixtures verify deterministic guardrail priority and specific recovery/follow-up actions.
- request-AC5 -> This task. Proof: stable-thread memory tests cover changed, still-open, waiting, overdue, cleared/resolved, and suppressed-unchanged states without using read state as completion.
- request-AC6 -> This task. Proof: meeting tests cover conflicts, tight transitions, related preparation evidence, placeholders, presence, and compact context-free meetings.
- request-AC7 -> This task. Proof: confidence-label and risk-threshold tests cover Reliable/Confirm/Insufficient context plus one-strong-or-multiple-weak warning behavior.
- request-AC8 -> This task. Proof: renderer/news tests cover distinct daily/weekly subjects, empty-section omission, operational-first ordering, news deduplication, and compact weather.
- request-AC9 -> This task. Proof: scoped feedback tests cover trusted preferences, reversible Useful/Hide similar, critical guardrails, and multi-user isolation.
- request-AC10 -> This task. Proof: versioned metrics report content-free cards, generic actions, risk/news volume, sensitive suppression, repeated suppression, and persisted explicit feedback.
- request-AC11 -> This task. Proof: target validation, Graph scope, retention guidance, secret suppression, and content-free runtime diagnostics are covered by focused and full tests.
- request-AC12 -> This task. Proof: identity-free replay covers sensitive auth, noise, ownership, deadline, delivery failure, continuity, meeting conflict, rendering, and localization; 279 tests pass.
- request-AC13 -> This task. Proof: daily/weekly HTML artifacts passed native visual inspection; UTF-8/background defects were fixed, and live delivery is fail-closed to one configured recipient with no CC/BCC.
- request-AC14 -> This task. Proof: deterministic shadow replay passes the versioned gates with 74.78% shorter median output, 100% fewer generic actions, and zero surfaced synthetic secrets; release is deployed and the first-new-run sender audit remains explicitly pending.

# Validation
- Run focused tests for each backlog slice.
- Run `python3 -m pytest`.
- Render representative daily and weekly HTML outputs and inspect them visually at desktop and narrow viewport widths.
- If a live Graph delivery test is necessary, send only to the explicitly authorized test mailbox and verify the final Outlook rendering there.
- Run `logics-manager flow validate req_055_day_captain_production_digest_actionability_improvement --explain`.
- Run `logics-manager lint --require-status`.
- Run `logics-manager audit --group-by-doc`.

# Report
- 2026-07-12: development-ready corpus expanded from an anonymized aggregate audit of stable production briefs across four recipient profiles. Implementation has not started; progress remains 0%.
- 2026-07-12: orchestration and security sibling task started. First checkpoint suppresses deterministic authentication messages at the earliest shared application boundary; 121 focused tests pass. Remaining implementation is tracked in tasks 050 through 052.
- 2026-07-12: security sibling task 051 completed with 265 passing tests. The first actionability slice now enforces renderer budgets of 3 critical, 3 user-action, 2 watch, 1 presence, and 4 meeting cards, and unread state no longer adds ranking score. Focused scoring/renderer suite: 67 passed.
- 2026-07-12: daily and weekly runs now pass their explicit run type into rendering and use distinct localized subjects. Full suite: 267 passed.
- 2026-07-12: recent-memory matching now follows stable mail thread identity even when Graph message IDs change. Unchanged watch, routine meeting, and presence cards are suppressed before rendering, while critical and user-action items remain visible as still open. Focused continuity/app/scoring suite: 100 passed.
- 2026-07-12: meeting scoring now detects overlaps and transitions of 15 minutes or less, raises their priority, and emits a specific conflict or transition action. Context-free meetings retain compact watch wording instead of invented preparation. Full suite: 270 passed.
- 2026-07-12: user-owned mail actions now name a concrete reply/resolve verb, normalized object, counterparty, and any explicitly stated due hint. Other-owned and shared actions retain separate wording. Full suite: 271 passed.
- 2026-07-12: text and HTML rendering omit empty operational sections and place optional weather/news after the overview and populated operational sections. Full suite remains 271 passed.
- 2026-07-12: confidence labels are now decision-oriented (`Reliable`/`Confirm`/`Insufficient context`, localized in French) while retaining the existing item-specific confidence reasons. Full suite remains 271 passed.
- 2026-07-12: external news deduplicates repeated URLs/headlines before applying its configured limit. Digest payloads now expose aggregate repeated-unchanged suppression counts alongside sensitive suppressions. Full suite: 274 passed.
- 2026-07-12: `hide_similar` feedback now creates a strong scoped negative preference that suppresses similar non-critical mail; sending the inverse value reverses it. Critical and transactional guardrails cannot be hidden this way. Full suite: 275 passed.
- 2026-07-12: the identity-free replay now exercises the core task-050 ranking, action, continuity, security, and meeting-conflict paths without Graph delivery. Full suite: 276 passed.
- 2026-07-12: continuity now emits explicit `waiting` for other-owned work and `overdue` when a supported explicit noon deadline has elapsed; cleared items already provide resolved signals and unchanged low-signal items are suppressed. Full suite: 278 passed.
- 2026-07-12: local implementation is complete and full suite passes at 279 tests. Task remains open only because its DoD depends on sibling task 052 post-release audit evidence; no production deployment or mailbox delivery was performed in this session.
- 2026-07-12: production rollout is live on Render with green CI and content-free health diagnostics. The deployment sent zero messages; completion remains gated only on auditing the first scheduled new-release digest after Monday 08:45.

# AI Context
- Summary: Orchestrate production digest actionability improvements
- Keywords: scaffolded-task, request-chain-scaffold, orchestration
- Use when: Coordinating implementation of a scaffolded request chain.
- Skip when: Working on one isolated sibling slice.

# Links
- Request: `req_055_day_captain_production_digest_actionability_improvement`
- Product brief(s): `prod_002_day_captain_actionable_differential_brief`
- Architecture decision(s): (none yet)

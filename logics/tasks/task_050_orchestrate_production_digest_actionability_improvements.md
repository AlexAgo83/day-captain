## task_050_orchestrate_production_digest_actionability_improvements - Orchestrate production digest actionability improvements
> From version: 1.0.0
> Schema version: 1.0
> Status: In progress
> Understanding: 98
> Confidence: 95
> Progress: 50
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
- request-AC1 -> This task. Evidence needed: Authentication codes, password-reset messages, magic links, and equivalent sensitive authentication content are suppressed before persistence, LLM processing, telemetry, and rendering, with no raw secret material retained.
- request-AC2 -> This task. Evidence needed: A daily digest renders no more than 3 critical items, 3 user-owned actions, 2 watch items, and 4 upcoming meetings; unread state remains informational and low-signal newsletters, entertainment recaps, routine automatic replies, passive presence, and unchanged items do not consume those budgets without a stronger signal.
- request-AC3 -> This task. Evidence needed: Every rendered action identifies a concrete verb, object, owner, and evidence source; due dates and counterparties are included when supported, while other-owned and unclear work is not presented as the recipient's action.
- request-AC4 -> This task. Evidence needed: Delivery failures, explicit deadlines, overdue commitments, and actionable transactional alerts deterministically outrank low-signal content and generate specific recovery or follow-up actions.
- request-AC5 -> This task. Evidence needed: Cross-run continuity follows stable mail threads and distinguishes new, changed, still open, waiting, overdue, resolved, and suppressed unchanged states without treating read state as completion.
- request-AC6 -> This task. Evidence needed: Meeting cards surface conflicts, tight transitions, and preparation evidence only when supported by a document, open decision, prior commitment, relevant thread, or explicit preparation request; routine and placeholder meetings remain compact.
- request-AC7 -> This task. Evidence needed: Confidence is displayed as Reliable, Confirm, or Insufficient context with a specific reason; suspicious-mail warnings require multiple independent weak signals or one strong trust-boundary violation and do not penalize language alone.
- request-AC8 -> This task. Evidence needed: Daily and weekly subjects are distinct, empty operational sections are omitted, operational deltas precede ambient content, external news is optional/relevant/deduplicated, and weather is compact and validated.
- request-AC9 -> This task. Evidence needed: Recipient preferences can prioritize trusted senders and themes, suppress low-value topics or recurring items, and accept reversible Useful or Hide similar feedback without sharing state across users.
- request-AC10 -> This task. Evidence needed: Digest payloads expose content-free usefulness instrumentation for impressions, voluntary opens, recalls, suppressions, repeated unchanged items, resolutions, and explicit feedback without covert tracking or raw mailbox content.
- request-AC11 -> This task. Evidence needed: Application access is restricted to required mailboxes, sender-side copies have an explicit retention policy, and diagnostics contain no raw subjects, previews, bodies, names, addresses, tokens, or secrets.
- request-AC12 -> This task. Evidence needed: An anonymized replay suite reproduces sensitive-auth, noise, ownership, deadline, delivery-failure, continuity, meeting-conflict, rendering, and localization cases; focused and full automated tests pass.
- request-AC13 -> This task. Evidence needed: Daily and weekly HTML are visually validated in rendered artifacts, and any necessary live delivery test is sent only to the explicitly authorized single test mailbox; no other production recipient is contacted during development or acceptance.
- request-AC14 -> This task. Evidence needed: Rollout uses a bounded shadow comparison or equivalent safe preview, proves at least a 40% median visible-length reduction and 80% generic-action reduction with zero surfaced authentication secrets, then repeats the sender-side production audit after release.

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

# AI Context
- Summary: Orchestrate production digest actionability improvements
- Keywords: scaffolded-task, request-chain-scaffold, orchestration
- Use when: Coordinating implementation of a scaffolded request chain.
- Skip when: Working on one isolated sibling slice.

# Links
- Request: `req_055_day_captain_production_digest_actionability_improvement`
- Product brief(s): `prod_002_day_captain_actionable_differential_brief`
- Architecture decision(s): (none yet)

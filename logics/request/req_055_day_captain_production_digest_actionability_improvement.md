## req_055_day_captain_production_digest_actionability_improvement - Day Captain production digest actionability improvement
> From version: 1.0.0
> Schema version: 1.0
> Status: Ready
> Understanding: 98
> Confidence: 95
> Complexity: High
> Theme: UX
> Reminder: Update status/understanding/confidence and linked backlog/task references when you edit this doc.

# Needs
- Turn production digests from long mailbox summaries into concise, differential, user-owned action briefs.
- Reduce repeated, generic, and low-signal cards while preserving delivery failures, explicit requests, deadlines, and meeting preparation needs.
- Use the existing scoring, ownership, continuity, rendering, feedback, and storage primitives before introducing new architecture.
- Make digest usefulness measurable so future tuning is based on user behavior rather than fixed heuristic scores.

# Context
- A read-only aggregate audit found historical briefs and selected stable production briefs sent to four anonymized recipients between baseline-start and 2026-07-12.
- The stable baseline averaged about 5,455 visible characters and 9 rendered cards per brief, with 869 generic recommended actions, 46 sender-verification warnings, 354 external-news articles, and no material June-to-July improvement.
- The audit found authentication-code messages eligible for surfacing, repeated entertainment recaps, recurring meetings and presence events repeated across runs, false suspicious-mail warnings on established conversations, and delivery failures that did not always dominate low-signal content.
- Every recipient received both daily and weekly briefs with the same subject on the same Sunday, a few seconds apart, while optional news was repeated in both editions.
- The codebase already stores action ownership, confidence metadata, continuity state, recent completed runs, cleared items, user preferences, and related meeting context, but the final selection and rendering do not fully exploit them.
- All production evidence in this corpus is anonymized. No mailbox addresses, personal names, client names, suppliers, or message contents are included.

# Acceptance criteria
- AC1: Authentication codes, password-reset messages, magic links, and equivalent sensitive authentication content are suppressed before persistence, LLM processing, telemetry, and rendering, with no raw secret material retained.
- AC2: A daily digest renders no more than 3 critical items, 3 user-owned actions, 2 watch items, and 4 upcoming meetings; unread state remains informational and low-signal newsletters, entertainment recaps, routine automatic replies, passive presence, and unchanged items do not consume those budgets without a stronger signal.
- AC3: Every rendered action identifies a concrete verb, object, owner, and evidence source; due dates and counterparties are included when supported, while other-owned and unclear work is not presented as the recipient's action.
- AC4: Delivery failures, explicit deadlines, overdue commitments, and actionable transactional alerts deterministically outrank low-signal content and generate specific recovery or follow-up actions.
- AC5: Cross-run continuity follows stable mail threads and distinguishes new, changed, still open, waiting, overdue, resolved, and suppressed unchanged states without treating read state as completion.
- AC6: Meeting cards surface conflicts, tight transitions, and preparation evidence only when supported by a document, open decision, prior commitment, relevant thread, or explicit preparation request; routine and placeholder meetings remain compact.
- AC7: Confidence is displayed as Reliable, Confirm, or Insufficient context with a specific reason; suspicious-mail warnings require multiple independent weak signals or one strong trust-boundary violation and do not penalize language alone.
- AC8: Daily and weekly subjects are distinct, empty operational sections are omitted, operational deltas precede ambient content, external news is optional/relevant/deduplicated, and weather is compact and validated.
- AC9: Recipient preferences can prioritize trusted senders and themes, suppress low-value topics or recurring items, and accept reversible Useful or Hide similar feedback without sharing state across users.
- AC10: Digest payloads expose content-free usefulness instrumentation for impressions, voluntary opens, recalls, suppressions, repeated unchanged items, resolutions, and explicit feedback without covert tracking or raw mailbox content.
- AC11: Application access is restricted to required mailboxes, sender-side copies have an explicit retention policy, and diagnostics contain no raw subjects, previews, bodies, names, addresses, tokens, or secrets.
- AC12: An anonymized replay suite reproduces sensitive-auth, noise, ownership, deadline, delivery-failure, continuity, meeting-conflict, rendering, and localization cases; focused and full automated tests pass.
- AC13: Daily and weekly HTML are visually validated in rendered artifacts, and any necessary live delivery test is sent only to the explicitly authorized single test mailbox; no other production recipient is contacted during development or acceptance.
- AC14: Rollout uses a bounded shadow comparison or equivalent safe preview, proves at least a 40% median visible-length reduction and 80% generic-action reduction with zero surfaced authentication secrets, then repeats the sender-side production audit after release.

# Definition of Ready (DoR)
- [x] Problem statement is explicit and user impact is clear.
- [x] Scope boundaries (in/out) are explicit.
- [x] Acceptance criteria are testable.
- [x] Dependencies and known risks are listed.

# Companion docs
- Product brief(s): `prod_002_day_captain_actionable_differential_brief`
- Architecture decision(s): (none yet)

# References
- src/day_captain/services.py
- src/day_captain/digest_parsing.py
- src/day_captain/digest_memory.py
- src/day_captain/models.py
- src/day_captain/app.py
- src/day_captain/config.py
- tests/test_digest_renderer.py
- tests/test_digest_parsing.py
- tests/test_digest_memory.py
- tests/test_app.py
- tests/test_graph_client.py
- tests/test_storage.py
- tests/test_recall.py
- tests/test_news.py

# AI Context
- Summary: Day Captain production digest actionability improvement
- Keywords: request-chain-scaffold, day captain production digest actionability improvement, development-ready
- Use when: You need to implement or review the scaffolded workflow for Day Captain production digest actionability improvement.
- Skip when: The change is unrelated to this scaffolded request chain.

# Backlog
- `item_109_reduce_digest_noise_and_enforce_concise_section_budgets`
- `item_110_generate_concrete_owner_aware_actions_and_deadlines`
- `item_111_turn_recent_run_memory_into_a_differential_commitment_view`
- `item_112_make_upcoming_meetings_preparation_and_conflict_aware`
- `item_113_improve_digest_presentation_personalization_and_usefulness_telemetry`
- `item_114_protect_sensitive_mailbox_content_and_govern_application_access`
- `item_115_validate_digest_usefulness_with_replay_visual_qa_and_safe_rollout`

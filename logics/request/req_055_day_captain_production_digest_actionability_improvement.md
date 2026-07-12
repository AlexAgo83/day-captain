## req_055_day_captain_production_digest_actionability_improvement - Day Captain production digest actionability improvement
> From version: 1.0.0
> Schema version: 1.0
> Status: Draft
> Understanding: 90%
> Confidence: 85%
> Complexity: High
> Theme: UX
> Reminder: Update status/understanding/confidence and linked backlog/task references when you edit this doc.

# Needs
- Turn production digests from long mailbox summaries into concise, differential, user-owned action briefs.
- Reduce repeated, generic, and low-signal cards while preserving delivery failures, explicit requests, deadlines, and meeting preparation needs.
- Use the existing scoring, ownership, continuity, rendering, feedback, and storage primitives before introducing new architecture.
- Make digest usefulness measurable so future tuning is based on user behavior rather than fixed heuristic scores.

# Context
- A read-only audit of 22 production briefs spanning roughly one month found bodies between about 7,200 and 12,400 characters, with up to 12 mail cards and 6 meetings in one brief.
- The audit found 106 cards using the same confidence score, 33 instances of a generic reply-or-confirm action, 19 generic meeting-preparation prompts, and one recurring entertainment newsletter surfaced in 19 briefs.
- Daily and weekly briefs can currently share the same subject, empty sections consume space, external news can dominate the brief, and operational delivery failures do not always outrank low-signal content.
- The codebase already stores action ownership, confidence metadata, continuity state, recent completed runs, cleared items, user preferences, and related meeting context, but the final selection and rendering do not fully exploit them.
- All production evidence in this corpus is anonymized. No mailbox addresses, personal names, client names, suppliers, or message contents are included.

# Acceptance criteria
- AC1: A daily digest renders no more than 3 critical items, 3 user-owned actions, 2 watch items, and 4 upcoming meetings, with deterministic ordering and focused regression coverage.
- AC2: Unread state is informational only; newsletters, entertainment recaps, routine automatic replies, and already-surfaced unchanged items do not gain action priority without a stronger signal.
- AC3: Every rendered action identifies a concrete next step and owner; user-owned actions are separated from shared work and work owned by another participant.
- AC4: Delivery failures, explicit deadlines, overdue commitments, and actionable transactional alerts outrank low-signal messages and produce specific recommended actions.
- AC5: Cross-run continuity follows stable mail threads where available and distinguishes new, changed, still open, waiting, overdue, resolved, and suppressed unchanged states.
- AC6: Meeting cards surface conflicts and preparation evidence only when the system has a document, open decision, prior commitment, relevant thread, or explicit preparation request.
- AC7: Confidence is displayed as a small evidence-based category rather than a pseudo-precise number, and suspicious-mail warnings require multiple independent risk signals or a strong trust-boundary violation.
- AC8: Daily and weekly subjects are distinct, empty operational sections are omitted, external news is optional and bounded, weather values are validated, and operational work appears before ambient information.
- AC9: Digest payloads expose anonymized usefulness instrumentation for card impressions, opens, recalls, suppressions, repeated unchanged items, and user feedback without storing message bodies in telemetry.
- AC10: Existing multi-user isolation, Graph delivery, recall, feedback, storage compatibility, and security guardrails remain covered by the full test suite.

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

## task_051_implement_sensitive_content_and_application_access_safeguards - Implement sensitive-content and application-access safeguards
> From version: 1.0.0
> Schema version: 1.0
> Status: Done
> Understanding: 100
> Confidence: 98
> Progress: 100%
> Complexity: High
> Theme: Implementation delivery
> Reminder: Update status/understanding/confidence/progress and linked request/backlog references when you edit this doc.
> Owner: codex-work6

# Context
The production audit found that authentication content can enter the digest pipeline and that mailbox-access boundaries are not sufficiently explicit. This task establishes a fail-closed boundary before persistence, model processing, telemetry, and rendering. All implementation fixtures and evidence must remain synthetic and identity-free.

# Implementation plan
1. Inventory every ingestion, persistence, model, telemetry, rendering, and diagnostic boundary traversed by a message.
2. Add deterministic sensitive-authentication detection and suppression at the earliest shared ingestion boundary.
3. Keep sensitivity classification independent from suspicious-mail risk classification.
4. Replace content-bearing suppression diagnostics with an allow-listed, content-free event schema.
5. Require multiple independent weak signals, or one strong violation, before raising a suspicious-mail warning.
6. Enforce explicit authorized mailbox scope and fail closed before Graph reads or sends outside it.
7. Document retention and operator-access expectations for sender-side mailbox evidence.
8. Add synthetic unit, integration, storage, rendering, and multi-user-isolation tests.

# Definition of Done (DoD)
- [x] Sensitive authentication content is removed before every downstream boundary, including errors and debug artifacts.
- [x] Sensitivity and suspicious-mail risk are separate typed outcomes with regression fixtures.
- [x] Suspicious-mail warnings require the documented signal threshold.
- [x] Mailbox reads and sends are bounded by explicit authorization and fail closed outside it.
- [x] Suppression telemetry and test evidence contain no mailbox content, identity, secret, token, or URL.
- [x] Retention and operator-access expectations are documented next to the implementation.
- [x] Focused and full automated validation passes.

# Backlog
- `item_114_protect_sensitive_mailbox_content_and_govern_application_access`

# Acceptance criteria
- AC1: Synthetic authentication-code, password-reset, and magic-link messages are suppressed before storage, LLM, telemetry, and rendering; tests prove raw secret text is absent from every downstream artifact.
- AC2: A content-free suppression event can be counted without recording subject, preview, body, sender, recipient, code, token, or URL.
- AC3: Internal collaboration links and foreign-language reply prefixes alone do not trigger verification, while fixtures with multiple independent weak signals or one strong violation do.
- AC4: Sensitivity and suspicious-mail risk are represented independently so a trusted sensitive message is suppressed rather than mislabeled suspicious.
- AC5: Application-access verification documents the bounded sender/target mailbox scope and fails closed when a mailbox falls outside the authorized scope.
- AC6: Sender-mailbox retention and operator-access expectations are documented and test evidence contains no production content or identity.
- AC7: Full auth, Graph, storage, multi-user isolation, and digest tests pass without exposing credentials in command output.

# Validation
- Run focused detector, ingestion, storage, rendering, Graph-scope, and multi-user-isolation tests with synthetic fixtures.
- Search generated artifacts and captured logs for fixture secrets and assert zero matches.
- Run the complete project test suite.
- Run `logics-manager flow validate task_051_implement_sensitive_content_and_application_access_safeguards --strict`.
- Run `logics-manager lint --require-status` and `logics-manager audit`.
- Run `logics-manager flow finish task task_051_implement_sensitive_content_and_application_access_safeguards.md` only after implementation evidence is attached.
- Finish workflow executed on 2026-07-12.
- Linked backlog/request close verification passed.

# Report
- 2026-07-12: implementation started. A deterministic authentication-message filter now runs immediately after collection and before tenant scoping, persistence, scoring, LLM rewriting, memory, rendering, and run storage.
- 2026-07-12: synthetic regression proof confirms a one-time-code secret is absent from message storage, wording-engine input, rendered payload, and persisted run. Focused app, scoring, and renderer suite: 121 passed.
- 2026-07-12: suspicious-mail classification now ignores a single weak urgency cue while retaining warnings for one strong or multiple independent signals. Existing target-user authorization fails closed outside `DAY_CAPTAIN_TARGET_USERS`; operator documentation now records mailbox-evidence access and retention boundaries. Expanded focused suite: 152 passed.
- 2026-07-12: added the allow-listed aggregate `sensitive_suppressions` metric; it contains only an integer count. Full suite: 265 passed. Task implementation is ready for closeout.
- Finished on 2026-07-12.
- Linked backlog item(s): `item_114_protect_sensitive_mailbox_content_and_govern_application_access`
- Related request(s): `req_055_day_captain_production_digest_actionability_improvement`

# AI Context
- Summary: Implement implement sensitive-content and application-access safeguards.
- Keywords: task, implementation, backlog, runtime, python
- Use when: You need a bounded implementation task for a backlog item.
- Skip when: The work is still at the request or backlog shaping stage.

# Links
- Request: `req_055_day_captain_production_digest_actionability_improvement`
- Product brief(s): (none yet)
- Architecture decision(s): (none yet)

# AC Traceability
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

## task_052_run_digest_replay_visual_qa_and_safe_rollout - Run digest replay visual QA and safe rollout
> From version: 1.0.0
> Schema version: 1.0
> Status: In progress
> Understanding: 98
> Confidence: 95
> Progress: 80
> Complexity: High
> Theme: Implementation delivery
> Reminder: Update status/understanding/confidence/progress and linked request/backlog references when you edit this doc.
> Owner: codex-work6

# Context
The stable production baseline contains 118 anonymized briefs. This task turns that baseline into repeatable usefulness, rendering, and delivery gates. Production recipients must never be used for testing: any live delivery is optional and must be restricted to one explicitly authorized test mailbox.

# Implementation plan
1. Build an identity-free synthetic replay corpus covering every request acceptance area and critical delivery-failure cases.
2. Implement one repeatable metrics command using versioned definitions for baseline and candidate output.
3. Generate representative daily and weekly HTML artifacts, including empty, dense, multilingual, conflict, delivery-failure, and sensitive-suppression cases.
4. Visually inspect desktop and narrow-width renders and retain content-free evidence of the checked artifact, viewport, and result.
5. Run a shadow comparison that cannot invoke the production delivery path.
6. Add a fail-closed live-test guard that accepts exactly one explicitly authorized recipient and rejects aliases, CC/BCC, lists, and fan-out payloads.
7. If a live test is necessary, send only to that authorized mailbox and verify the received Outlook rendering; otherwise record why synthetic rendering was sufficient.
8. Re-run the identical sender-side metric definitions after release and record bounded anonymized deltas.

# Definition of Done (DoD)
- [ ] Synthetic replay covers every request acceptance area without real identity or mailbox content.
- [ ] Baseline and candidate reports use identical versioned metric definitions.
- [ ] Candidate daily output meets the agreed size and generic-action targets without losing critical delivery failures.
- [ ] Daily and weekly HTML pass documented desktop and narrow-width visual review.
- [ ] Shadow comparison cannot deliver to production recipients.
- [ ] Optional live delivery is technically constrained to exactly one explicitly authorized test mailbox and verified in Outlook.
- [ ] Post-release audit can reproduce the baseline comparison without persisting mailbox content.
- [ ] Focused, full, Logics, and context-pack validation passes.

# Backlog
- `item_115_validate_digest_usefulness_with_replay_visual_qa_and_safe_rollout`

# Acceptance criteria
- AC1: Synthetic replay covers every request acceptance area and contains no real name, address, subject, preview, body, client, supplier, token, or secret.
- AC2: A repeatable report compares visible length, rendered cards, generic actions, unchanged repetitions, risk warnings, news volume, ownership, deadlines, conflicts, and sensitive suppressions.
- AC3: Candidate daily output achieves at least 40% lower median visible length and 80% fewer generic actions than baseline, with zero surfaced authentication secrets and no loss of critical delivery-failure fixtures.
- AC4: Representative daily and weekly HTML passes documented visual inspection at desktop and narrow widths, with operational hierarchy, readable cards, distinct subjects, valid links, and no redundant empty sections.
- AC5: Shadow comparison or equivalent preview runs without delivering to production recipients and produces bounded anonymized differences.
- AC6: Any live delivery test asserts exactly one authorized recipient before send, reaches only that mailbox, and is verified in Outlook; tests fail closed for every other address or fan-out payload.
- AC7: Focused tests, full pytest, flow validation, lint, audit, and context-pack refresh pass before rollout.
- AC8: A post-release aggregate audit uses the same metric definitions and records regressions or improvements without persisting mailbox content.

# Validation
- Run the synthetic replay and metrics command twice and confirm deterministic metric output.
- Render representative daily and weekly HTML at desktop and narrow widths; inspect hierarchy, wrapping, links, empty states, and card subjects.
- Exercise recipient-guard tests for the authorized singleton and rejected alternate, CC/BCC, list, and multi-recipient payloads.
- If live delivery is used, capture content-free proof that exactly one authorized mailbox received and rendered the message.
- Run focused tests and the complete project test suite.
- Run `logics-manager flow validate task_052_run_digest_replay_visual_qa_and_safe_rollout --strict`.
- Run `logics-manager lint --require-status`, `logics-manager audit`, and refresh the request context pack.
- Run `logics-manager flow finish task task_052_run_digest_replay_visual_qa_and_safe_rollout.md` only after implementation evidence is attached.

# Report
- 2026-07-12: implementation started. Added `day-captain digest-metrics` for one or more exported preview payloads. Metric definitions are versioned (`1.0`) and report only aggregate visible length, card count, generic actions, risk warnings, news volume, and sensitive suppressions.
- 2026-07-12: synthetic unit/CLI validation passes (16 tests). No Graph collection or delivery path is reachable from the metrics command.
- 2026-07-12: Graph delivery now has an optional fail-closed live-test marker. The marker must match `DAY_CAPTAIN_GRAPH_LIVE_TEST_RECIPIENT`, contain exactly one To recipient, and contain no CC/BCC; invalid fan-out fails before any Graph call. Focused Graph/settings/app suite: 87 passed.
- 2026-07-12: rendering validation documentation now defines desktop (~720px) and narrow (~360px) checks, operational ordering, section budgets, empty-section omission, and the optional single-recipient Outlook path. No local browser automation is installed, so screenshot evidence remains pending rather than adding a new dependency.
- 2026-07-12: versioned metrics now include repeated-unchanged suppression counts, and RSS news is deterministically deduplicated before reporting. Full suite: 274 passed.
- 2026-07-12: added the built-in `day-captain digest-replay` command. It uses only `.test` identities, forces JSON delivery, covers authentication suppression, noise, owned deadline, transactional failure, continuity, and meeting conflict, and emits byte-identical aggregate output across repeated runs. Full suite: 276 passed.
- 2026-07-12: replay now evaluates a versioned `public-safe-baseline-v1` gate against the baseline aggregate baseline. Candidate replay reports 1,804 median visible characters (66.93% reduction) and zero generic actions (100% reduction), passing the 40%/80% gates; synthetic secret absence remains asserted by the replay test.

# AI Context
- Summary: Implement run digest replay visual qa and safe rollout.
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

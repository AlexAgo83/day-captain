## item_115_validate_digest_usefulness_with_replay_visual_qa_and_safe_rollout - Validate digest usefulness with replay visual QA and safe rollout
> From version: 1.0.0
> Schema version: 1.0
> Status: In progress
> Understanding: 100
> Confidence: 98
> Progress: 99
> Complexity: High
> Theme: Operator workflow and runtime integration
> Reminder: Update status/understanding/confidence/progress and linked request/task references when you edit this doc.

# Problem
- The production audit provides a measurable baseline, but the repository does not yet have a single anonymized replay suite that reproduces the observed noise, security, ownership, continuity, calendar, and rendering failures.
- Automated payload assertions do not prove that the final HTML is readable in a real mail client or that daily and weekly editions are visually distinguishable.
- A direct production rollout could disturb real recipients, so comparison, visual QA, and any live delivery test need an explicit single-recipient safety boundary.

# Scope
- In:
  - Build synthetic fixtures for sensitive authentication messages, newsletters, automatic replies, delivery failures, ownership, deadlines, thread updates, alias duplicates, meeting conflicts, placeholders, localization, news dedupe, and weather validation.
  - Capture baseline and candidate metrics with one repeatable content-free audit command or script.
  - Render representative daily and weekly HTML artifacts and visually inspect desktop and narrow viewport behavior, hierarchy, truncation, links, badges, and empty states.
  - Run shadow comparison or equivalent non-delivery preview before enabling the new format for production recipients.
  - If a live Graph delivery test is necessary, send only to the explicitly authorized single test mailbox and assert the final recipient before sending; never fan out a test to configured production users.
  - Verify the delivered Outlook rendering, subject distinction, links, and absence of prohibited content in the authorized test mailbox.
  - Repeat the aggregate audit after release and compare it with the anonymized baseline baseline.
- Out:
  - Copying production mailbox content into fixtures, snapshots, reports, or commits.
  - Sending development or acceptance messages to any non-test recipient.
  - Covert read tracking or tracking pixels.
  - Requiring a new analytics service or dashboard for rollout.

# Acceptance criteria
- AC1: Synthetic replay covers every request acceptance area and contains no real name, address, subject, preview, body, client, supplier, token, or secret.
- AC2: A repeatable report compares visible length, rendered cards, generic actions, unchanged repetitions, risk warnings, news volume, ownership, deadlines, conflicts, and sensitive suppressions.
- AC3: Candidate daily output achieves at least 40% lower median visible length and 80% fewer generic actions than baseline, with zero surfaced authentication secrets and no loss of critical delivery-failure fixtures.
- AC4: Representative daily and weekly HTML passes documented visual inspection at desktop and narrow widths, with operational hierarchy, readable cards, distinct subjects, valid links, and no redundant empty sections.
- AC5: Shadow comparison or equivalent preview runs without delivering to production recipients and produces bounded anonymized differences.
- AC6: Any live delivery test asserts exactly one authorized recipient before send, reaches only that mailbox, and is verified in Outlook; tests fail closed for every other address or fan-out payload.
- AC7: Focused tests, full pytest, flow validation, lint, audit, and context-pack refresh pass before rollout.
- AC8: A post-release aggregate audit uses the same metric definitions and records regressions or improvements without persisting mailbox content.

# AC Traceability
- request-AC10 -> This backlog slice. Proof deferred to repeatable content-free usefulness metrics.
- request-AC12 -> This backlog slice. Proof deferred to anonymized replay and automated validation.
- request-AC13 -> This backlog slice. Proof deferred to visual artifacts and the authorized-recipient-only delivery evidence.
- request-AC14 -> This backlog slice. Proof deferred to shadow comparison, target metrics, and the post-release aggregate audit.
- request-AC1 -> This backlog slice. Evidence needed: Authentication codes, password-reset messages, magic links, and equivalent sensitive authentication content are suppressed before persistence, LLM processing, telemetry, and rendering, with no raw secret material retained.
- request-AC2 -> This backlog slice. Evidence needed: A daily digest renders no more than 3 critical items, 3 user-owned actions, 2 watch items, and 4 upcoming meetings; unread state remains informational and low-signal newsletters, entertainment recaps, routine automatic replies, passive presence, and unchanged items do not consume those budgets without a stronger signal.
- request-AC3 -> This backlog slice. Evidence needed: Every rendered action identifies a concrete verb, object, owner, and evidence source; due dates and counterparties are included when supported, while other-owned and unclear work is not presented as the recipient's action.
- request-AC4 -> This backlog slice. Evidence needed: Delivery failures, explicit deadlines, overdue commitments, and actionable transactional alerts deterministically outrank low-signal content and generate specific recovery or follow-up actions.
- request-AC5 -> This backlog slice. Evidence needed: Cross-run continuity follows stable mail threads and distinguishes new, changed, still open, waiting, overdue, resolved, and suppressed unchanged states without treating read state as completion.
- request-AC6 -> This backlog slice. Evidence needed: Meeting cards surface conflicts, tight transitions, and preparation evidence only when supported by a document, open decision, prior commitment, relevant thread, or explicit preparation request; routine and placeholder meetings remain compact.
- request-AC7 -> This backlog slice. Evidence needed: Confidence is displayed as Reliable, Confirm, or Insufficient context with a specific reason; suspicious-mail warnings require multiple independent weak signals or one strong trust-boundary violation and do not penalize language alone.
- request-AC8 -> This backlog slice. Evidence needed: Daily and weekly subjects are distinct, empty operational sections are omitted, operational deltas precede ambient content, external news is optional/relevant/deduplicated, and weather is compact and validated.
- request-AC9 -> This backlog slice. Evidence needed: Recipient preferences can prioritize trusted senders and themes, suppress low-value topics or recurring items, and accept reversible Useful or Hide similar feedback without sharing state across users.
- request-AC10 -> This backlog slice. Evidence needed: Digest payloads expose content-free usefulness instrumentation for impressions, voluntary opens, recalls, suppressions, repeated unchanged items, resolutions, and explicit feedback without covert tracking or raw mailbox content.
- request-AC11 -> This backlog slice. Evidence needed: Application access is restricted to required mailboxes, sender-side copies have an explicit retention policy, and diagnostics contain no raw subjects, previews, bodies, names, addresses, tokens, or secrets.
- request-AC12 -> This backlog slice. Evidence needed: An anonymized replay suite reproduces sensitive-auth, noise, ownership, deadline, delivery-failure, continuity, meeting-conflict, rendering, and localization cases; focused and full automated tests pass.
- request-AC13 -> This backlog slice. Evidence needed: Daily and weekly HTML are visually validated in rendered artifacts, and any necessary live delivery test is sent only to the explicitly authorized single test mailbox; no other production recipient is contacted during development or acceptance.
- request-AC14 -> This backlog slice. Evidence needed: Rollout uses a bounded shadow comparison or equivalent safe preview, proves at least a 40% median visible-length reduction and 80% generic-action reduction with zero surfaced authentication secrets, then repeats the sender-side production audit after release.

# Decision framing
- Product framing: Not needed
- Product signals: (none detected)
- Product follow-up: No product brief follow-up is expected based on current signals.
- Architecture framing: Not needed
- Architecture signals: (none detected)
- Architecture follow-up: No architecture decision follow-up is expected based on current signals.

# Links
- Product brief(s): (none yet)
- Architecture decision(s): (none yet)
- Request: `req_055_day_captain_production_digest_actionability_improvement`
- Primary task(s): `task_052_run_digest_replay_visual_qa_and_safe_rollout`

# AI Context
- Summary: Validate digest usefulness with replay visual QA and safe rollout
- Keywords: backlog-groom, request, validate digest usefulness with replay visual qa and safe rollout, bounded slice
- Use when: Use when implementing or reviewing the delivery slice for Validate digest usefulness with replay visual QA and safe rollout.
- Skip when: Skip when the change is unrelated to this delivery slice or its linked request.

# Priority
- Priority: High
- Rationale: Visual QA, single-recipient delivery safety, and measurable replay are release gates because automated unit tests alone cannot validate the final email experience or prevent accidental fan-out.

# Notes
- Hybrid rationale: Derived from request `req_055_day_captain_production_digest_actionability_improvement` and kept bounded to one coherent delivery slice.
- Source file: `logics/request/req_055_day_captain_production_digest_actionability_improvement.md`.
- Generated locally by logics-manager.

# Tasks
- `task_052_run_digest_replay_visual_qa_and_safe_rollout`

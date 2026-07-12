## item_114_protect_sensitive_mailbox_content_and_govern_application_access - Protect sensitive mailbox content and govern application access
> From version: 1.0.0
> Schema version: 1.0
> Status: Done
> Understanding: 98
> Confidence: 95
> Progress: 100%
> Complexity: High
> Theme: Operator workflow and runtime integration
> Reminder: Update status/understanding/confidence/progress and linked request/task references when you edit this doc.

# Problem
- Authentication-code and equivalent sensitive messages can currently enter the normal collection, persistence, scoring, optional LLM, telemetry, and rendering path.
- Suspicious-mail warnings are over-triggered by normal links, foreign-language prefixes, internal conversations, automatic replies, and expected invoices, which erodes trust in genuine warnings.
- The app-only identity can read multiple production mailboxes and the sender mailbox retains personalized copies, so access scope, diagnostics, and retention need explicit guardrails.

# Scope
- In:
  - Detect authentication codes, one-time passwords, password resets, magic links, sign-in approvals, and equivalent transient secrets at the earliest normalized trust boundary.
  - Suppress prohibited sensitive content before message persistence, LLM prompts, telemetry, summaries, and rendering; retain only a content-free suppression reason when operationally necessary.
  - Separate sensitivity classification from suspicious-mail risk classification.
  - Require either one strong trust-boundary violation or multiple independent weak signals before rendering a sender-verification warning.
  - Treat established thread history, internal domain, known participants, and expected collaboration links as trust signals without treating language as a risk signal.
  - Keep app-only access limited to required target and sender mailboxes through tenant administration, and document verification evidence without credentials.
  - Define retention and operator-access expectations for personalized copies in the sender mailbox.
  - Keep all runtime diagnostics and audit telemetry content-free.
- Out:
  - Building a general data-loss-prevention platform.
  - Storing redacted authentication codes for later analysis.
  - Weakening detection of domain impersonation, executable payloads, secret requests, or identity mismatch.
  - Committing tenant IDs, mailbox addresses, tokens, client secrets, or production message samples.

# Acceptance criteria
- AC1: Synthetic authentication-code, password-reset, and magic-link messages are suppressed before storage, LLM, telemetry, and rendering; tests prove raw secret text is absent from every downstream artifact.
- AC2: A content-free suppression event can be counted without recording subject, preview, body, sender, recipient, code, token, or URL.
- AC3: Internal collaboration links and foreign-language reply prefixes alone do not trigger verification, while fixtures with multiple independent weak signals or one strong violation do.
- AC4: Sensitivity and suspicious-mail risk are represented independently so a trusted sensitive message is suppressed rather than mislabeled suspicious.
- AC5: Application-access verification documents the bounded sender/target mailbox scope and fails closed when a mailbox falls outside the authorized scope.
- AC6: Sender-mailbox retention and operator-access expectations are documented and test evidence contains no production content or identity.
- AC7: Full auth, Graph, storage, multi-user isolation, and digest tests pass without exposing credentials in command output.

# AC Traceability
- request-AC1 -> This backlog slice. Proof deferred to sensitive-content boundary tests.
- request-AC7 -> This backlog slice. Proof deferred to independent-risk and trust-signal fixtures.
- request-AC11 -> This backlog slice. Proof deferred to mailbox-scope, retention, and content-free diagnostic evidence.
- request-AC12 -> This backlog slice. Proof deferred to anonymized security replay and full-suite results.
- request-AC14 -> This backlog slice. Proof deferred to the zero-surfaced-authentication-secret release metric.
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
- Primary task(s): `task_051_implement_sensitive_content_and_application_access_safeguards`

# AI Context
- Summary: Protect sensitive mailbox content and govern application access
- Keywords: backlog-groom, request, protect sensitive mailbox content and govern application access, bounded slice
- Use when: Use when implementing or reviewing the delivery slice for Protect sensitive mailbox content and govern application access.
- Skip when: Skip when the change is unrelated to this delivery slice or its linked request.

# Priority
- Priority: High
- Rationale: Authentication-secret suppression and least-privilege mailbox access are release blockers because a concise brief is not useful if it can expose transient credentials or overreach mailbox scope.

# Notes
- Hybrid rationale: Derived from request `req_055_day_captain_production_digest_actionability_improvement` and kept bounded to one coherent delivery slice.
- Source file: `logics/request/req_055_day_captain_production_digest_actionability_improvement.md`.
- Generated locally by logics-manager.
- Task `task_051_implement_sensitive_content_and_application_access_safeguards` was finished via `logics-manager flow finish task` on 2026-07-12.

# Tasks
- `task_051_implement_sensitive_content_and_application_access_safeguards`

## item_112_make_upcoming_meetings_preparation_and_conflict_aware - Make upcoming meetings preparation and conflict aware
> From version: 1.0.0
> Schema version: 1.0
> Status: In progress
> Understanding: 100
> Confidence: 98
> Progress: 100
> Complexity: Medium
> Theme: Calendar
> Reminder: Update status/understanding/confidence/progress and linked request/task references when you edit this doc.

# Problem
- Meeting cards often repeat generic preparation advice even when no preparation evidence exists.
- Overlapping or tightly adjacent meetings are not clearly elevated as scheduling conflicts.
- Related mail context is available but does not consistently yield decisions, documents, commitments, or questions.

# Scope
- In:
  - Only render a meeting action when related context contains an explicit preparation request, document, open decision, prior commitment, or unresolved question.
  - Detect overlaps and gaps shorter than 15 minutes after meeting collection and render a critical conflict summary.
  - Include incompatible physical/online locations in conflict detection and explain whether a conflict was created or removed by a moved meeting.
  - Summarize at most one prior decision, one open commitment, one relevant document, and one question for each preparation-worthy meeting.
  - Keep placeholder and presence events out of preparation actions while preserving useful location context.
  - Suppress unchanged recurring meetings unless they have a conflict, schedule change, new agenda/context, or concrete preparation evidence.
  - Prefer concrete wording over generic keep-in-view or prepare-key-points fallbacks.
- Out:
  - Automatically rescheduling meetings.
  - Fetching new document content beyond context already available to the application.
  - Generating preparation content when no supporting evidence exists.

# Acceptance criteria
- AC1: A context-free meeting renders without a recommended preparation action.
- AC2: A meeting with a linked request or document renders the specific preparation evidence.
- AC3: Overlapping meetings and sub-15-minute transitions produce a visible conflict or tight-transition warning.
- AC4: Placeholder and all-day presence fixtures do not become preparation tasks.
- AC5: An unchanged recurring meeting remains compact, while a moved meeting reports its new time and any conflict delta without requiring reconfirmation by default.
- AC6: A preparation card contains at most one decision, one commitment, one document, and one open question.

# AC Traceability
- request-AC6 -> This backlog slice. Proof: AC1: A context-free meeting renders without a recommended preparation action.
- request-AC10 -> This backlog slice. Proof: AC2: A meeting with a linked request or document renders the specific preparation evidence.
- request-AC3 -> This backlog slice. Evidence needed: Every rendered action identifies a concrete verb, object, owner, and evidence source; due dates and counterparties are included when supported, while other-owned and unclear work is not presented as the recipient's action.
- request-AC4 -> This backlog slice. Evidence needed: Delivery failures, explicit deadlines, overdue commitments, and actionable transactional alerts deterministically outrank low-signal content and generate specific recovery or follow-up actions.
- request-AC5 -> This backlog slice. Evidence needed: Cross-run continuity follows stable mail threads and distinguishes new, changed, still open, waiting, overdue, resolved, and suppressed unchanged states without treating read state as completion.
- request-AC7 -> This backlog slice. Evidence needed: Confidence is displayed as Reliable, Confirm, or Insufficient context with a specific reason; suspicious-mail warnings require multiple independent weak signals or one strong trust-boundary violation and do not penalize language alone.
- request-AC8 -> This backlog slice. Evidence needed: Daily and weekly subjects are distinct, empty operational sections are omitted, operational deltas precede ambient content, external news is optional/relevant/deduplicated, and weather is compact and validated.
- request-AC9 -> This backlog slice. Evidence needed: Recipient preferences can prioritize trusted senders and themes, suppress low-value topics or recurring items, and accept reversible Useful or Hide similar feedback without sharing state across users.
- request-AC11 -> This backlog slice. Evidence needed: Application access is restricted to required mailboxes, sender-side copies have an explicit retention policy, and diagnostics contain no raw subjects, previews, bodies, names, addresses, tokens, or secrets.
- request-AC12 -> This backlog slice. Evidence needed: An anonymized replay suite reproduces sensitive-auth, noise, ownership, deadline, delivery-failure, continuity, meeting-conflict, rendering, and localization cases; focused and full automated tests pass.
- request-AC13 -> This backlog slice. Evidence needed: Daily and weekly HTML are visually validated in rendered artifacts, and any necessary live delivery test is sent only to the explicitly authorized single test mailbox; no other production recipient is contacted during development or acceptance.
- request-AC14 -> This backlog slice. Evidence needed: Rollout uses a bounded shadow comparison or equivalent safe preview, proves at least a 40% median visible-length reduction and 80% generic-action reduction with zero surfaced authentication secrets, then repeats the sender-side production audit after release.

# Decision framing
- Product framing: Not needed
- Architecture framing: Not needed

# Links
- Product brief(s): `prod_002_day_captain_actionable_differential_brief`
- Architecture decision(s): (none yet)
- Request: `req_055_day_captain_production_digest_actionability_improvement`
- Primary task(s): `task_050_orchestrate_production_digest_actionability_improvements`

# AI Context
- Summary: Make upcoming meetings preparation and conflict aware
- Keywords: scaffolded-backlog, make upcoming meetings preparation and conflict aware, implementation-ready
- Use when: Implementing the scaffolded slice for Make upcoming meetings preparation and conflict aware.
- Skip when: The change belongs to another backlog slice.

# Priority
- Priority: Medium
- Rationale: Medium because meeting preparation adds meaningful value after the core mail-action and continuity signals are trustworthy.

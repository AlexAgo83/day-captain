## item_111_turn_recent_run_memory_into_a_differential_commitment_view - Turn recent-run memory into a differential commitment view
> From version: 1.0.0
> Schema version: 1.0
> Status: Done
> Understanding: 100
> Confidence: 98
> Progress: 100%
> Complexity: High
> Theme: Intelligence
> Reminder: Update status/understanding/confidence/progress and linked request/task references when you edit this doc.

# Problem
- Continuity currently keys message entries by source message ID, so a new reply in the same thread can bypass recent-memory matching.
- Already-surfaced unchanged cards remain visible, while cleared items are recorded in payload metadata but not explained to the recipient.
- The current states do not fully represent waiting, overdue, resolved, or intentionally suppressed work.

# Scope
- In:
  - Use stable thread identity from context metadata for mail memory keys, falling back to source ID only when no thread identifier exists.
  - Suppress already_surfaced unchanged items by default unless critical, overdue, flagged, or explicitly retained by preference.
  - Fingerprint normalized content and related participants so aliases or changed message IDs do not bypass continuity when stable thread identity is unavailable.
  - Keep changed and still_open items visible only with a concise explanation of what changed or why the commitment remains open.
  - Add waiting, overdue, and resolved continuity semantics using the existing continuity fields where possible.
  - Render a compact delta header with counts for new actions, changed items, deadlines, suppressed unchanged items, and cleared items.
  - Surface cleared items as a compact resolved-since-last-brief summary rather than full cards.
  - Keep memory isolated by tenant, user, and run type so weekly execution cannot consume the morning cursor or continuity state.
  - Record per-run counts for new, changed, waiting, overdue, resolved, suppressed unchanged, and repeated items.
- Out:
  - Creating a full task database separate from digest runs.
  - Inferring task completion solely because a message became read.
  - Sharing continuity state across users.

# Acceptance criteria
- AC1: A new message in an existing thread is classified as changed or still open rather than new.
- AC2: An unchanged non-critical item is suppressed on the next run and counted in the delta header.
- AC3: A disappeared prior item is represented as cleared/resolved without rendering its old full card.
- AC4: Daily and weekly memories remain independent and multi-user isolation tests pass.
- AC5: Read state alone never marks an item resolved.
- AC6: An alias or new message ID with the same stable thread/content identity does not create a duplicate new card.
- AC7: Continuity metrics are content-free and isolated by tenant, user, and run type.

# AC Traceability
- request-AC2 -> This backlog slice. Proof: AC1: A new message in an existing thread is classified as changed or still open rather than new.
- request-AC5 -> This backlog slice. Proof: AC2: An unchanged non-critical item is suppressed on the next run and counted in the delta header.
- request-AC9 -> This backlog slice. Proof: AC3: A disappeared prior item is represented as cleared/resolved without rendering its old full card.
- request-AC10 -> This backlog slice. Proof: AC4: Daily and weekly memories remain independent and multi-user isolation tests pass.
- request-AC6 -> This backlog slice. Evidence needed: Meeting cards surface conflicts, tight transitions, and preparation evidence only when supported by a document, open decision, prior commitment, relevant thread, or explicit preparation request; routine and placeholder meetings remain compact.
- request-AC7 -> This backlog slice. Evidence needed: Confidence is displayed as Reliable, Confirm, or Insufficient context with a specific reason; suspicious-mail warnings require multiple independent weak signals or one strong trust-boundary violation and do not penalize language alone.
- request-AC8 -> This backlog slice. Evidence needed: Daily and weekly subjects are distinct, empty operational sections are omitted, operational deltas precede ambient content, external news is optional/relevant/deduplicated, and weather is compact and validated.
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
- Summary: Turn recent-run memory into a differential commitment view
- Keywords: scaffolded-backlog, turn recent-run memory into a differential commitment view, implementation-ready
- Use when: Implementing the scaffolded slice for Turn recent-run memory into a differential commitment view.
- Skip when: The change belongs to another backlog slice.

# Priority
- Priority: High
- Rationale: High because stable thread continuity is required to stop repeated cards and distinguish changed, waiting, overdue, and resolved work.

# Tasks
- `task_050_orchestrate_production_digest_actionability_improvements`

# Notes
- Task `task_050_orchestrate_production_digest_actionability_improvements` was finished via `logics-manager flow finish task` on 2026-07-13.

## item_111_turn_recent_run_memory_into_a_differential_commitment_view - Turn recent-run memory into a differential commitment view
> From version: 1.0.0
> Schema version: 1.0
> Status: Ready
> Understanding: 95
> Confidence: 90
> Progress: 0
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
  - Keep changed and still_open items visible only with a concise explanation of what changed or why the commitment remains open.
  - Add waiting, overdue, and resolved continuity semantics using the existing continuity fields where possible.
  - Render a compact delta header with counts for new actions, changed items, deadlines, suppressed unchanged items, and cleared items.
  - Surface cleared items as a compact resolved-since-last-brief summary rather than full cards.
  - Keep memory isolated by tenant, user, and run type so weekly execution cannot consume the morning cursor or continuity state.
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

# AC Traceability
- request-AC2 -> This backlog slice. Proof: AC1: A new message in an existing thread is classified as changed or still open rather than new.
- request-AC5 -> This backlog slice. Proof: AC2: An unchanged non-critical item is suppressed on the next run and counted in the delta header.
- request-AC9 -> This backlog slice. Proof: AC3: A disappeared prior item is represented as cleared/resolved without rendering its old full card.
- request-AC10 -> This backlog slice. Proof: AC4: Daily and weekly memories remain independent and multi-user isolation tests pass.

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

## item_121_make_daily_output_a_strict_command_brief - Make daily output a strict command brief
> From version: 1.0.0
> Schema version: 1.0
> Status: Done
> Understanding: 90%
> Confidence: 85%
> Progress: 100%
> Complexity: High
> Theme: UX
> Reminder: Update status/understanding/confidence/progress and linked request/task references when you edit this doc.

# Problem
- Daily briefs still feel long and summary-like instead of acting as a short operational command surface.
- External news and repeated confidence labels add reading cost when they are not tied to active work.
- The overview can restate card content instead of telling the user what changed and what to do.

# Scope
- In:
  - Enforce the daily decision-brief budget at render selection: one top priority summary, 3 user-owned actions, 2 watch items, 4 meetings, and no daily external news unless relevant by configured theme or explicit preference.
  - Keep weekly briefs allowed to include a small bounded external-news section, after operational sections.
  - Change confidence rendering so labels appear only for low-confidence or decision-affecting uncertainty; localize labels consistently through the existing language table.
  - Rewrite the top summary as a delta: new actions, changed waiting items, conflicts, ignored/noise count, and cleared/resolved count when available.
  - Suppress generic recommended actions when the system cannot identify a concrete verb/object/owner.
  - Update digest metrics to count external-news inclusion, confidence-label render count, and visible control count.
- Out:
  - Removing confidence from internal scoring.
  - Removing weekly external news entirely.
  - Adding a new personalization database.

# Acceptance criteria
- AC1: Daily renderer tests enforce section budgets and fail if unrelated external news appears without theme or preference support.
- AC2: French output contains only French confidence labels when confidence is rendered.
- AC3: A high-confidence ordinary card omits the confidence badge, while a decision-affecting uncertain card keeps one short localized reason.
- AC4: The top summary is shorter than the combined card text and includes action/waiting/conflict/ignored counts when present.
- AC5: Metrics report visible length, card count, external-news count, confidence-label count, control count, generic-action count, and sensitive suppressions.

# AC Traceability
- request-AC3 -> This backlog slice. Proof: AC1: Daily renderer tests enforce section budgets and fail if unrelated external news appears without theme or preference support.
- request-AC4 -> This backlog slice. Proof: AC2: French output contains only French confidence labels when confidence is rendered.
- request-AC5 -> This backlog slice. Proof: AC3: A high-confidence ordinary card omits the confidence badge, while a decision-affecting uncertain card keeps one short localized reason.
- request-AC8 -> This backlog slice. Proof: AC4: The top summary is shorter than the combined card text and includes action/waiting/conflict/ignored counts when present.
- request-AC11 -> This backlog slice. Proof: AC5: Metrics report visible length, card count, external-news count, confidence-label count, control count, generic-action count, and sensitive suppressions.
- request-AC13 -> This backlog slice. Proof: AC5: Metrics report visible length, card count, external-news count, confidence-label count, control count, generic-action count, and sensitive suppressions.
- request-AC6 -> This backlog slice. Evidence needed: HTML and text rendering preserve readable spacing between labels, card badges, metadata, and quick-action links, including plain-text fallback output.
- request-AC7 -> This backlog slice. Evidence needed: Meeting and Outlook open controls remain available but are visually compact and do not repeat in a way that dominates card content.
- request-AC9 -> This backlog slice. Evidence needed: Scheduler and content-free delivery audit tooling can report expected target count, sent count, duplicate trigger signals, retry signals, and fan-out shape without reading or storing message bodies.
- request-AC10 -> This backlog slice. Evidence needed: Delivery-count anomaly checks cover duplicate sends, missing target sends, retry overlap, weekly/daily overlap, and manual recall overlap using synthetic or content-free fixtures.
- request-AC12 -> This backlog slice. Evidence needed: Representative daily and weekly HTML/text artifacts pass desktop and narrow-width review, and any manual mailbox verification remains single-recipient, content-free, and temporary.
- request-AC14 -> This backlog slice. Evidence needed: Documentation explains the private-ops evidence boundary: mailbox-derived audits stay temporary, aggregate-only results can be recorded, and real identities or message content never enter Git.

# Decision framing
- Product framing: Not needed
- Architecture framing: Not needed

# Links
- Product brief(s): `prod_004_day_captain_strict_decision_brief`
- Architecture decision(s): (none yet)
- Request: `req_057_day_captain_digest_friction_hardening`
- Primary task(s): `task_054_orchestrate_digest_friction_hardening`

# AI Context
- Summary: Make daily output a strict command brief
- Keywords: scaffolded-backlog, make daily output a strict command brief, implementation-ready
- Use when: Implementing the scaffolded slice for Make daily output a strict command brief.
- Skip when: The change belongs to another backlog slice.

# Priority
- Priority: High
- Rationale: Set by scaffold input or defaulted for grooming.

# Tasks
- `task_054_orchestrate_digest_friction_hardening`

# Notes
- Task `task_054_orchestrate_digest_friction_hardening` was finished via `logics-manager flow finish task` on 2026-07-23.

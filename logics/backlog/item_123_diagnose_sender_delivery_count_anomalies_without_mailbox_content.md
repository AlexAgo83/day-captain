## item_123_diagnose_sender_delivery_count_anomalies_without_mailbox_content - Diagnose sender delivery-count anomalies without mailbox content
> From version: 1.0.0
> Schema version: 1.0
> Status: Done
> Understanding: 90%
> Confidence: 85%
> Progress: 100%
> Complexity: Medium
> Theme: Operations
> Reminder: Update status/understanding/confidence/progress and linked request/task references when you edit this doc.

# Problem
- Recent content-free delivery counts show some runs with fewer or more messages than the expected target count.
- Operators need to distinguish normal fan-out, duplicate trigger, retry overlap, weekly/daily overlap, recall/manual run overlap, and missing-target delivery without reading message bodies.
- The existing private-ops boundary needs a reusable diagnostic command that records only aggregate metadata.

# Scope
- In:
  - Add or extend a content-free delivery audit command that reads only sent timestamp, normalized digest edition, recipient-count shape, attachment flag, and message identifier hash.
  - Compare observed sends against configured target count by edition and expected schedule window.
  - Flag duplicate sends when the same edition and schedule bucket exceeds target count, and missing sends when it falls below target count after the allowed delay.
  - Detect possible retry overlap from tightly clustered sends and possible manual/recall overlap from non-scheduled windows without storing subjects or recipient addresses.
  - Document that audit output is temporary, aggregate-only, and safe to summarize in Logics without mailbox identities or message content.
- Out:
  - Persisting mailbox audit exports in Git.
  - Reading message bodies for delivery-count diagnostics.
  - Automatically deleting sent messages or suppressing delivery based on audit results.

# Acceptance criteria
- AC1: Synthetic audit fixtures classify expected, missing-target, duplicate-target, retry-overlap, weekly-overlap, and manual-window cases.
- AC2: The command output contains no recipient address, subject, preview, body, client name, supplier name, token, secret, or hosted URL.
- AC3: A normal one-recipient-per-target fan-out reports pass, while extra or missing observed sends report actionable content-free diagnostics.
- AC4: Operator docs explain where private raw evidence may live and what aggregate fields can enter public-safe workflow docs.

# AC Traceability
- request-AC9 -> This backlog slice. Proof: AC1: Synthetic audit fixtures classify expected, missing-target, duplicate-target, retry-overlap, weekly-overlap, and manual-window cases.
- request-AC10 -> This backlog slice. Proof: AC2: The command output contains no recipient address, subject, preview, body, client name, supplier name, token, secret, or hosted URL.
- request-AC11 -> This backlog slice. Proof: AC3: A normal one-recipient-per-target fan-out reports pass, while extra or missing observed sends report actionable content-free diagnostics.
- request-AC13 -> This backlog slice. Proof: AC4: Operator docs explain where private raw evidence may live and what aggregate fields can enter public-safe workflow docs.
- request-AC14 -> This backlog slice. Proof: AC4: Operator docs explain where private raw evidence may live and what aggregate fields can enter public-safe workflow docs.
- request-AC5 -> This backlog slice. Evidence needed: Confidence labels render only when uncertainty changes the user's decision, are localized consistently, and never appear as English strings in French output.
- request-AC6 -> This backlog slice. Evidence needed: HTML and text rendering preserve readable spacing between labels, card badges, metadata, and quick-action links, including plain-text fallback output.
- request-AC7 -> This backlog slice. Evidence needed: Meeting and Outlook open controls remain available but are visually compact and do not repeat in a way that dominates card content.
- request-AC8 -> This backlog slice. Evidence needed: The top summary states what changed, what needs action, what is waiting on someone else, and what can be ignored, without restating full card text.
- request-AC12 -> This backlog slice. Evidence needed: Representative daily and weekly HTML/text artifacts pass desktop and narrow-width review, and any manual mailbox verification remains single-recipient, content-free, and temporary.

# Decision framing
- Product framing: Not needed
- Architecture framing: Not needed

# Links
- Product brief(s): `prod_004_day_captain_strict_decision_brief`
- Architecture decision(s): (none yet)
- Request: `req_057_day_captain_digest_friction_hardening`
- Primary task(s): `task_054_orchestrate_digest_friction_hardening`

# AI Context
- Summary: Diagnose sender delivery-count anomalies without mailbox content
- Keywords: scaffolded-backlog, diagnose sender delivery-count anomalies without mailbox content, implementation-ready
- Use when: Implementing the scaffolded slice for Diagnose sender delivery-count anomalies without mailbox content.
- Skip when: The change belongs to another backlog slice.

# Priority
- Priority: Medium
- Rationale: Set by scaffold input or defaulted for grooming.

# Tasks
- `task_054_orchestrate_digest_friction_hardening`

# Notes
- Task `task_054_orchestrate_digest_friction_hardening` was finished via `logics-manager flow finish task` on 2026-07-23.

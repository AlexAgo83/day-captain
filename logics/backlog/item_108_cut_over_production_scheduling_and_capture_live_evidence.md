## item_108_cut_over_production_scheduling_and_capture_live_evidence - Cut over production scheduling and capture live evidence
> From version: 1.0.0
> Schema version: 1.0
> Status: Ready
> Understanding: 90%
> Confidence: 85%
> Progress: 0%
> Complexity: Medium
> Theme: operations
> Reminder: Update status/understanding/confidence/progress and linked request/task references when you edit this doc.

# Problem
- The migration is not complete until the live scheduler is Power Automate and GitHub Actions schedules are disabled.
- Cutover without evidence could hide missed runs, duplicate runs, or a broken fallback.

# Scope
- In:
  - Create or update the live Power Automate flows from the runbook.
  - Run controlled manual tests for morning and weekly endpoints against the hosted service.
  - Disable active GitHub Actions schedule triggers after Power Automate evidence exists, while preserving manual workflow_dispatch.
  - Record live run IDs, timestamps, target-user scope, delivery outcome, and rollback state in the relevant Logics task notes.
- Out:
  - Changing Power Automate to inspect mailbox or calendar content directly.
  - Sending digest content to Power Automate logs.
  - Deleting the private ops repository.

# Acceptance criteria
- AC1: At least one live Power Automate run reaches the hosted morning-digest endpoint and delivery is confirmed without exposing digest content.
- AC2: Weekly-digest is validated by a safe manual Power Automate run or the first scheduled Sunday run, with evidence recorded.
- AC3: GitHub Actions schedule triggers are removed or commented out only after live Power Automate evidence exists.
- AC4: workflow_dispatch remains available and documented as fallback.
- AC5: The task closeout records rollback instructions and the final scheduler owner.

# AC Traceability
- request-AC4 -> This backlog slice. Proof: AC1: At least one live Power Automate run reaches the hosted morning-digest endpoint and delivery is confirmed without exposing digest content.
- request-AC5 -> This backlog slice. Proof: AC2: Weekly-digest is validated by a safe manual Power Automate run or the first scheduled Sunday run, with evidence recorded.
- request-AC6 -> This backlog slice. Proof: AC3: GitHub Actions schedule triggers are removed or commented out only after live Power Automate evidence exists.

# Decision framing
- Product framing: Not needed
- Architecture framing: Not needed

# Links
- Product brief(s): `prod_001_day_captain_operations_scheduler_reliability`
- Architecture decision(s): (none yet)
- Request: `req_054_day_captain_power_automate_scheduler_migration`
- Primary task(s): `task_049_orchestrate_power_automate_scheduler_migration`

# AI Context
- Summary: Cut over production scheduling and capture live evidence
- Keywords: scaffolded-backlog, cut over production scheduling and capture live evidence, implementation-ready
- Use when: Implementing the scaffolded slice for Cut over production scheduling and capture live evidence.
- Skip when: The change belongs to another backlog slice.

# Priority
- Priority: High
- Rationale: The user-facing drift remains until the live scheduler moves and evidence proves Power Automate can deliver both digest paths.

## item_107_align_day_captain_app_and_ops_docs_with_power_automate_scheduling - Align Day Captain app and ops docs with Power Automate scheduling
> From version: 1.0.0
> Schema version: 1.0
> Status: Ready
> Understanding: 90%
> Confidence: 85%
> Progress: 0%
> Complexity: Medium
> Theme: documentation
> Reminder: Update status/understanding/confidence/progress and linked request/task references when you edit this doc.

# Problem
- Application docs currently present the private GitHub Actions scheduler as the production path.
- The private ops README also describes GitHub schedules as the active scheduler, which will be misleading after the cutover.

# Scope
- In:
  - Update the application operator docs to describe Power Automate as the primary production scheduler.
  - Update the private ops README to clarify which GitHub workflows remain manual fallback surfaces.
  - Keep existing helper scripts and workflow templates documented as fallback/debug tools where still useful.
  - Update any scheduler-template language that would cause future operators to recreate the GitHub cron path as primary.
- Out:
  - Removing tests that protect existing scheduler helper behavior unless the corresponding template is intentionally retired.
  - Changing digest business logic or hosted HTTP response shape.
  - Moving production secrets into tracked files.

# Acceptance criteria
- AC1: Operator docs no longer instruct production operators to rely on GitHub Actions schedule for routine morning or weekly digest delivery.
- AC2: Docs still provide a clear manual fallback path using workflow_dispatch or direct hosted HTTP calls.
- AC3: Docs explain that Power Automate calls the existing hosted endpoints and does not own digest generation logic.
- AC4: Documentation validation and Logics lint pass after the updates.

# AC Traceability
- request-AC2 -> This backlog slice. Proof: AC1: Operator docs no longer instruct production operators to rely on GitHub Actions schedule for routine morning or weekly digest delivery.
- request-AC3 -> This backlog slice. Proof: AC2: Docs still provide a clear manual fallback path using workflow_dispatch or direct hosted HTTP calls.
- request-AC6 -> This backlog slice. Proof: AC3: Docs explain that Power Automate calls the existing hosted endpoints and does not own digest generation logic.

# Decision framing
- Product framing: Not needed
- Architecture framing: Not needed

# Links
- Product brief(s): `prod_001_day_captain_operations_scheduler_reliability`
- Architecture decision(s): (none yet)
- Request: `req_054_day_captain_power_automate_scheduler_migration`
- Primary task(s): `task_049_orchestrate_power_automate_scheduler_migration`

# AI Context
- Summary: Align Day Captain app and ops docs with Power Automate scheduling
- Keywords: scaffolded-backlog, align day captain app and ops docs with power automate scheduling, implementation-ready
- Use when: Implementing the scaffolded slice for Align Day Captain app and ops docs with Power Automate scheduling.
- Skip when: The change belongs to another backlog slice.

# Priority
- Priority: High
- Rationale: Operators currently learn the old GitHub cron path from docs, so the documentation must change before or with the production cutover.

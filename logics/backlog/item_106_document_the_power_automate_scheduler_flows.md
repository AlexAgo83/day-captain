## item_106_document_the_power_automate_scheduler_flows - Document the Power Automate scheduler flows
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
- The current scheduler behavior is encoded in GitHub Actions YAML and app docs, but there is no Day Captain Power Automate runbook that an operator or another IA can execute safely.
- Without a runbook, secrets, retry policy, target-user fan-out, and failure behavior can drift between the intended migration and the live tenant flow.

# Scope
- In:
  - Add an ops-facing runbook that mirrors the proven CTS style for scheduled Power Automate flows.
  - Specify two flows: weekday morning digest and Sunday weekly digest.
  - Specify recurrence timezone, concurrency, health warm-up, HTTP actions, target-user list source, secure secret handling, retry policy, alerting, manual test procedure, and rollback criteria.
  - Keep all payloads content-free and secret-free in docs.
- Out:
  - Creating the live Power Automate flows in this documentation slice.
  - Changing hosted job endpoint code.
  - Adding a custom scheduler service.

# Acceptance criteria
- AC1: The runbook names the exact hosted endpoints, headers, and JSON payload fields used by each flow.
- AC2: The runbook defines schedule semantics in Europe/Paris without requiring duplicate UTC cron gates.
- AC3: The runbook defines where DAY_CAPTAIN_SERVICE_URL, DAY_CAPTAIN_JOB_SECRET, and target users live in Power Platform without exposing values.
- AC4: The runbook includes a rollback section for temporarily restoring GitHub Actions schedule triggers.

# AC Traceability
- request-AC1 -> This backlog slice. Proof: AC1: The runbook names the exact hosted endpoints, headers, and JSON payload fields used by each flow.
- request-AC3 -> This backlog slice. Proof: AC2: The runbook defines schedule semantics in Europe/Paris without requiring duplicate UTC cron gates.
- request-AC6 -> This backlog slice. Proof: AC3: The runbook defines where DAY_CAPTAIN_SERVICE_URL, DAY_CAPTAIN_JOB_SECRET, and target users live in Power Platform without exposing values.

# Decision framing
- Product framing: Not needed
- Architecture framing: Not needed

# Links
- Product brief(s): `prod_001_day_captain_operations_scheduler_reliability`
- Architecture decision(s): (none yet)
- Request: `req_054_day_captain_power_automate_scheduler_migration`
- Primary task(s): `task_049_orchestrate_power_automate_scheduler_migration`

# AI Context
- Summary: Document the Power Automate scheduler flows
- Keywords: scaffolded-backlog, document the power automate scheduler flows, implementation-ready
- Use when: Implementing the scaffolded slice for Document the Power Automate scheduler flows.
- Skip when: The change belongs to another backlog slice.

# Priority
- Priority: High
- Rationale: This is the prerequisite for creating tenant flows safely; without it, cutover risks secret leakage, duplicate sends, or an untestable scheduler.

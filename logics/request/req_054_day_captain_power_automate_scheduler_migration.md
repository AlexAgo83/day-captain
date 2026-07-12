## req_054_day_captain_power_automate_scheduler_migration - Day Captain Power Automate scheduler migration
> From version: 1.0.0
> Schema version: 1.0
> Status: Done
> Understanding: 90%
> Confidence: 85%
> Complexity: Medium
> Theme: operations
> Reminder: Update status/understanding/confidence and linked backlog/task references when you edit this doc.

# Needs
- Replace the production GitHub Actions cron scheduler with Power Automate so weekday morning and Sunday weekly digests run at stable Europe/Paris wall-clock times.
- Stop relying on GitHub Actions schedule timing, checkout, Python setup, and package installation before the hosted job trigger.
- Keep the existing hosted Day Captain job endpoints and job secret contract instead of moving digest business logic into Power Automate.

# Context
- The current production scheduler lives in the private day-captain-ops repository and uses GitHub Actions schedules for morning-digest and weekly-digest.
- Operators observed severe schedule drift, with digest emails arriving around noon instead of the intended morning slot.
- The app already exposes protected hosted endpoints: POST /jobs/morning-digest and POST /jobs/weekly-digest with X-Day-Captain-Secret.
- The neighboring CTS project already documents scheduled Power Automate flows with recurrence triggers, concurrency limited to one run, HTTP actions, secret handling, and live validation evidence.
- Power Automate HTTP actions may require a Premium or trial entitlement; if unavailable, GitHub Actions remains the fallback scheduler.

# Acceptance criteria
- AC1: A Power Automate runbook exists for the Day Captain scheduler with separate morning and weekly flows, exact Europe/Paris schedule semantics, concurrency set to one, target-user fan-out, warm-up/health behavior, retry policy, and failure notification rules.
- AC2: Production scheduler documentation names Power Automate as the primary scheduler and GitHub Actions workflow_dispatch as the manual fallback only.
- AC3: The migration preserves the existing hosted HTTP contract: GET /healthz for warm-up/readiness and POST /jobs/morning-digest or /jobs/weekly-digest with X-Day-Captain-Secret and per-user JSON payloads.
- AC4: The private ops repository no longer has active GitHub Actions schedule triggers for Day Captain once the Power Automate flows have live successful-run evidence; manual workflow_dispatch remains available for emergency one-off runs.
- AC5: Live validation evidence records at least one successful Power Automate morning-digest run and one successful weekly-digest test or manual run, including run IDs/timestamps, target-user scope, and observed delivery timing without exposing mailbox content or secrets.
- AC6: Rollback guidance exists and is tested enough for an operator to temporarily re-enable GitHub Actions schedule triggers if Power Automate entitlement, connection, or recurrence execution fails.

# Definition of Ready (DoR)
- [x] Problem statement is explicit and user impact is clear.
- [x] Scope boundaries (in/out) are explicit.
- [x] Acceptance criteria are testable.
- [x] Dependencies and known risks are listed.

# Companion docs
- Product brief(s): `prod_001_day_captain_operations_scheduler_reliability`
- Architecture decision(s): (none yet)

# References
- day-captain-ops/.github/workflows/morning-digest.yml
- day-captain-ops/.github/workflows/weekly-digest.yml
- day-captain-ops/README.md
- src/day_captain/web.py
- src/day_captain/hosted_jobs.py
- docs/tenant_scoped_multi_user_operator_guide.md
- docs/private_ops_repo_bootstrap.md
- neighboring cts/docs/rh-recruit-power-automate-flow.md
- neighboring cts/docs/rh-recruit-retention-anonymization-flow.md

# AI Context
- Summary: Day Captain Power Automate scheduler migration
- Keywords: request-chain-scaffold, day captain power automate scheduler migration, development-ready
- Use when: You need to implement or review the scaffolded workflow for Day Captain Power Automate scheduler migration.
- Skip when: The change is unrelated to this scaffolded request chain.

# Backlog
- `item_106_document_the_power_automate_scheduler_flows`
- `item_107_align_day_captain_app_and_ops_docs_with_power_automate_scheduling`
- `item_108_cut_over_production_scheduling_and_capture_live_evidence`

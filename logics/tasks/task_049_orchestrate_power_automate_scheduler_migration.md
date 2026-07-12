## task_049_orchestrate_power_automate_scheduler_migration - Orchestrate Power Automate scheduler migration
> From version: 1.0.0
> Schema version: 1.0
> Status: In progress
> Understanding: 97
> Confidence: 91
> Progress: 98
> Complexity: Medium
> Theme: Implementation delivery
> Reminder: Update status/understanding/confidence/progress and linked request/backlog references when you edit this doc.
> Owner: codex

# Context
- Orchestrate the scaffolded request chain and keep sibling implementation slices linked.

# Plan
- [x] 1. Confirm the current production scheduler state in day-captain-ops and identify any drift from the application docs.
- [x] 2. Create the Day Captain Power Automate scheduler runbook from the existing hosted endpoint contract and CTS flow pattern.
- [x] 3. Update app and ops documentation so Power Automate is primary and GitHub Actions is fallback-only.
- [x] 4. Create and manually test the live morning and weekly Power Automate flows with concurrency one and secret-safe logging.
- [x] 5. After live success evidence, remove active GitHub Actions schedule triggers while preserving workflow_dispatch.
- [ ] 6. Validate docs and Logics corpus, record run evidence, and close the migration task only after fallback instructions are clear.
- [ ] GATE: do not close until lint, audit, and scaffold validation pass.

# Backlog
- `item_106_document_the_power_automate_scheduler_flows`
- `item_107_align_day_captain_app_and_ops_docs_with_power_automate_scheduling`
- `item_108_cut_over_production_scheduling_and_capture_live_evidence`

# Definition of Done (DoD)
- [ ] Power Automate scheduler runbook is present and linked from operator docs.
- [ ] App and private ops docs name Power Automate as primary and GitHub workflow_dispatch as fallback.
- [ ] Live Power Automate evidence is recorded for morning-digest and weekly-digest.
- [ ] Active GitHub Actions schedule triggers are disabled only after evidence exists.
- [ ] Lint, audit, and flow validation have been run and any remaining findings are documented.

# AC Traceability
- request-AC1 -> Plan steps 2 and 4. Proof: the task explicitly creates the Power Automate runbook and live flows.
- request-AC2 -> Plan step 3. Proof: the task explicitly updates docs so Power Automate is primary and GitHub is fallback-only.
- request-AC3 -> Plan steps 2 and 4. Proof: the task keeps the existing health and hosted job endpoint contract.
- request-AC4 -> Plan step 5. Proof: the task disables active GitHub schedule triggers only after Power Automate evidence.
- request-AC5 -> Plan steps 4 and 6. Proof: the task records live run evidence before closeout.
- request-AC6 -> Plan steps 3 and 6. Proof: the task requires fallback documentation before closeout.

# Validation
- Run `logics-manager flow validate req_054_day_captain_power_automate_scheduler_migration --fixable --explain`.
- Run `logics-manager lint --require-status`.
- Run `logics-manager audit --group-by-doc`.
- Validate live Power Automate run evidence before removing GitHub schedule triggers.

# Report
- 2026-07-12 codex: confirmed the active production scheduler still lives in the private ops GitHub Actions workflows, added `docs/power_automate_scheduler_setup.md`, updated app operator docs and README to name Power Automate as the primary scheduler, and updated the private ops README to describe GitHub Actions as fallback. Live Power Automate flow creation/testing and disabling GitHub `schedule:` blocks remain blocked until tenant Power Automate access and successful run evidence are available.
- 2026-07-12 codex: validation after docs work: `logics-manager flow validate req_054_day_captain_power_automate_scheduler_migration --fixable --explain` passed. `logics-manager lint --require-status` and `logics-manager audit --group-by-doc` still fail only on pre-existing unrelated issues: missing `Status` in `logics/specs/spec_000_day_captain_v1_digest_contract.md` and stale draft docs from req_053/item_100-105/task_048.
- 2026-07-12 codex: created and started Power Automate flows `Day Captain - Morning Digest` and `Day Captain - Weekly Digest` in the tenant Power Platform environment. Initial morning and weekly runs succeeded. Corrected weekly recurrence after the initial run to avoid a duplicate same-day Sunday execution; next morning run is `2026-07-13T06:45:29Z`, next weekly run is `2026-07-19T18:30:00Z`. Removed GitHub Actions `schedule:` blocks from the private ops workflows while preserving `workflow_dispatch`.
- 2026-07-12 codex: preserved the old GitHub cold-start posture in Power Automate by hardening both live flows with explicit HTTP retry policy on `Warm_hosted_service` and `Trigger_Day_Captain_job`: fixed interval `PT10S`, count `6`. Verified the next scheduled executions remained unchanged.
- 2026-07-12 codex: reviewed the live Power Automate hardening findings. The retry finding was stale after the cold-start fix: both HTTP actions in both flows now have explicit fixed retry policy `PT10S` count `6`. Secured HTTP outputs as well as inputs on both live flows. Verified native Power Automate owner failure alerts are subscribed on both flows. Remaining hardening before copying this pattern into `another tenant`: move the job secret from literal flow definition data into tenant-managed Power Platform configuration, then rotate the job secret.

# AI Context
- Summary: Orchestrate Power Automate scheduler migration
- Keywords: scaffolded-task, request-chain-scaffold, orchestration
- Use when: Coordinating implementation of a scaffolded request chain.
- Skip when: Working on one isolated sibling slice.

# Links
- Request: `req_054_day_captain_power_automate_scheduler_migration`
- Product brief(s): `prod_001_day_captain_operations_scheduler_reliability`
- Architecture decision(s): (none yet)

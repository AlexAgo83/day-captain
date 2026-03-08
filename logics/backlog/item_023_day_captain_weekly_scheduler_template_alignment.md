## item_023_day_captain_weekly_scheduler_template_alignment - Align weekly scheduler templates with the supported jitter-tolerant Sunday gate
> From version: 0.12.0
> Status: Ready
> Understanding: 100%
> Confidence: 100%
> Progress: 0%
> Complexity: Medium
> Theme: Operations
> Reminder: Update status/understanding/confidence/progress and linked task references when you edit this doc.

# Problem
- The supported `day-captain-ops` Sunday weekly workflow already uses the helper-backed jitter-tolerant gate.
- The copy-ready weekly scheduler templates in `.github/workflows/` and `docs/` still embed the old exact-minute gate.
- A new operator bootstrapping from the shipped templates can therefore reintroduce the production bug even though the hardened ops workflow is already fixed.

# Scope
- In:
  - align the repository weekly scheduler template with the supported Sunday gate semantics
  - align the copy-ready ops weekly scheduler template in `docs/`
  - keep the Sunday `20:30 Europe/Paris` product contract
  - confirm the shipped templates match the supported workflow model
- Out:
  - changing the weekly digest local time
  - changing weekday `morning-digest` scheduling
  - replacing GitHub Actions as the scheduler platform

```mermaid
flowchart LR
    OpsWorkflow[Supported ops workflow] --> Templates[Repo and docs templates]
    Templates --> Align[Shared jitter-tolerant gate]
    Align --> SafeBootstrap[Safe bootstrap for new ops repos]
```

# Acceptance criteria
- AC1: `.github/workflows/weekly-digest-scheduler.yml` uses the same jitter-tolerant Sunday gate semantics as the supported `day-captain-ops` workflow.
- AC2: `docs/day_captain_ops_weekly_digest_scheduler.yml` uses the same jitter-tolerant Sunday gate semantics as the supported `day-captain-ops` workflow.
- AC3: The effective operator contract remains Sunday `20:30 Europe/Paris`, with tolerance for normal GitHub schedule jitter.

# AC Traceability
- AC1 -> Scope includes repo template alignment. Proof: item explicitly aligns the repository weekly template with the supported ops workflow.
- AC2 -> Scope includes docs template alignment. Proof: item explicitly aligns the copy-ready ops weekly template in `docs/`.
- AC3 -> Scope preserves the product contract. Proof: item explicitly keeps Sunday `20:30 Europe/Paris` while changing only the gate semantics.

# Links
- Request: `req_020_day_captain_scheduler_template_and_hosted_email_command_contract_hardening`
- Primary task(s): `task_025_day_captain_scheduler_template_and_hosted_contract_orchestration` (`Ready`)

# Priority
- Impact: High - stale templates can reintroduce a known production scheduling failure.
- Urgency: High - the templates are operator-facing and currently wrong.

# Notes
- Derived from request `req_020_day_captain_scheduler_template_and_hosted_email_command_contract_hardening`.

## item_085_day_captain_hosted_delegated_auth_validation_hardening - Tighten hosted delegated-auth validation to require a real unattended token path
> From version: 1.8.0
> Status: Done
> Understanding: 100%
> Confidence: 97%
> Progress: 100%
> Complexity: Medium
> Theme: Reliability
> Reminder: Update status/understanding/confidence/progress and linked task references when you edit this doc.

# Problem
- Hosted delegated-auth validation currently accepts some production-like configurations that do not actually provide an unattended delegated token path.
- That creates a false sense of readiness because operators can pass validation while the first real hosted job still fails on missing delegated credentials.
- The hosted delegated contract needs to fail earlier and more explicitly.

# Scope
- In:
  - tighten hosted delegated-auth validation rules so accepted production-like configs include a real executable delegated token path
  - keep validation errors explicit about what is missing
  - align validation expectations with the actual runtime bootstrap path
  - add regression coverage for accepted and rejected hosted delegated configurations
- Out:
  - redesigning app-only auth
  - adding a new secret or credential store
  - replacing delegated auth with a different product model

```mermaid
flowchart LR
    Config[Hosted delegated config] --> Validate[Stricter validation]
    Validate --> Ready[Executable unattended runtime]
```

# Acceptance criteria
- AC1: Hosted delegated validation rejects production-like configurations that provide only partial delegated identity inputs without a usable token path.
- AC2: Validation errors remain explicit enough for operators to understand what credential path is missing.
- AC3: Validation rules align with the actual delegated runtime bootstrap path instead of approving shapes that cannot execute.
- AC4: Tests cover representative accepted and rejected hosted delegated configurations.

# AC Traceability
- Req039 AC3 -> This item hardens hosted delegated validation. Proof: validation behavior is the full item scope.
- Req039 AC5 -> This item keeps the validation behavior explicit and explainable. Proof: operator-readable errors are an acceptance criterion.
- Req039 AC6 -> This item requires hosted delegated validation coverage. Proof: accepted and rejected config tests are part of the item.

# Links
- Request: `req_039_day_captain_delivery_recovery_and_delegated_auth_contract_corrections`
- Primary task(s): `task_044_day_captain_delivery_recovery_and_delegated_auth_contract_orchestration` (`Done`)

# Priority
- Impact: High - false-positive hosted validation wastes operator time and causes avoidable production failures.
- Urgency: High - this should be corrected before leaning further on hosted delegated workflows.

# Notes
- Derived from `req_039_day_captain_delivery_recovery_and_delegated_auth_contract_corrections`.
- The core goal is alignment between what validation approves and what runtime can actually execute.

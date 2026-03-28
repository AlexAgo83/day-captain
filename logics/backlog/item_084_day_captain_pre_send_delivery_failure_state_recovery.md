## item_084_day_captain_pre_send_delivery_failure_state_recovery - Correct run-state recovery for clearly pre-send Graph delivery failures
> From version: 1.8.0
> Status: Done
> Understanding: 100%
> Confidence: 98%
> Progress: 100%
> Complexity: Medium
> Theme: Reliability
> Reminder: Update status/understanding/confidence/progress and linked task references when you edit this doc.

# Problem
- The hosted delivery path can leave a run in `delivery_pending` even when Microsoft Graph delivery failed before any acceptance response was returned.
- That stale pending state is operationally dangerous because later digests are intentionally blocked behind the pending-delivery reconciliation guard.
- The project needs a more accurate pre-send failure classification so clearly retryable transport failures become `delivery_failed` instead of freezing the run stream.

# Scope
- In:
  - classify timeout, connection, and equivalent pre-acceptance Graph delivery failures as safe `delivery_failed` outcomes
  - preserve the distinction between true post-send uncertainty and clearly pre-send failures
  - ensure later digest runs are not blocked by stale pending state after a clearly pre-send failure
  - add regression coverage for these delivery-state transitions
- Out:
  - building a generalized retry worker
  - changing the user-facing delivery content
  - reworking the broader hosted job API

```mermaid
flowchart LR
    Send[Graph send attempt] --> Fail[Pre-send failure]
    Fail --> Failed[delivery_failed]
    Failed --> Recover[Later runs can continue]
```

# Acceptance criteria
- AC1: Clearly pre-send Graph delivery failures are recorded as `delivery_failed`.
- AC2: Those failures no longer leave the latest run in `delivery_pending`.
- AC3: A later digest run for the same tenant/user can proceed after such a failure.
- AC4: Tests cover representative timeout or network-failure transitions.

# AC Traceability
- Req039 AC1 -> This item corrects the status transition for pre-send delivery failures. Proof: run-state recovery is the whole scope.
- Req039 AC2 -> This item removes the stale pending-run blocker after a clearly pre-send failure. Proof: later-run recovery is an acceptance criterion.
- Req039 AC6 -> This item requires timeout and network-failure regression coverage. Proof: tests are part of the item.

# Links
- Request: `req_039_day_captain_delivery_recovery_and_delegated_auth_contract_corrections`
- Primary task(s): `task_044_day_captain_delivery_recovery_and_delegated_auth_contract_orchestration` (`Done`)

# Priority
- Impact: High - a single misclassified failure can freeze routine delivery for a user.
- Urgency: High - this is a production recovery issue, not a polish concern.

# Notes
- Derived from `req_039_day_captain_delivery_recovery_and_delegated_auth_contract_corrections`.
- The implementation must preserve the intended meaning of `delivery_pending` as post-send uncertainty, not generic failure.

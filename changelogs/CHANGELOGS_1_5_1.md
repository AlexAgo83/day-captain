# Changelog (`1.5.0 -> 1.5.1`)

## Major Highlights

- Added a new reliability-oriented `logics` request, backlog split, and orchestration task for hosted runtime fail-fast behavior, delegated token freshness, durable hosted execution expectations, target-user normalization, and ISO datetime parser alignment.

## Version 1.5.1

### Delivered

- Added [req_034_day_captain_hosted_runtime_fail_fast_and_identity_normalization.md](/Users/alexandreagostini/Documents/day-captain/logics/request/req_034_day_captain_hosted_runtime_fail_fast_and_identity_normalization.md) to formalize the runtime-reliability work identified in the project review.
- Added [item_069_day_captain_hosted_fail_fast_and_durable_runtime_contract.md](/Users/alexandreagostini/Documents/day-captain/logics/backlog/item_069_day_captain_hosted_fail_fast_and_durable_runtime_contract.md), [item_070_day_captain_delegated_token_freshness_and_explicit_auth_failures.md](/Users/alexandreagostini/Documents/day-captain/logics/backlog/item_070_day_captain_delegated_token_freshness_and_explicit_auth_failures.md), and [item_071_day_captain_target_user_normalization_and_entrypoint_datetime_alignment.md](/Users/alexandreagostini/Documents/day-captain/logics/backlog/item_071_day_captain_target_user_normalization_and_entrypoint_datetime_alignment.md) to split the work into implementable slices.
- Added [task_039_day_captain_hosted_runtime_reliability_and_normalization_orchestration.md](/Users/alexandreagostini/Documents/day-captain/logics/tasks/task_039_day_captain_hosted_runtime_reliability_and_normalization_orchestration.md) to orchestrate delivery and validation for the runtime-contract changes.
- Bumped the project version from `1.5.0` to `1.5.1`.

### Validation

- `python3 logics/skills/logics-doc-linter/scripts/logics_lint.py --require-status`
- `python3 logics/skills/logics-flow-manager/scripts/workflow_audit.py --group-by-doc`

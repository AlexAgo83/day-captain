## item_069_day_captain_hosted_fail_fast_and_durable_runtime_contract - Make hosted runtime fail fast and tighten durable execution prerequisites
> From version: 1.5.0
> Status: Done
> Understanding: 100%
> Confidence: 97%
> Progress: 100%
> Complexity: Medium
> Theme: Reliability
> Reminder: Update status/understanding/confidence/progress and linked task references when you edit this doc.

# Problem
- Hosted Day Captain can still assemble with weak or misleading runtime behavior when Graph-backed execution is expected but key prerequisites are not actually satisfied.
- Silent fallback to stub auth or static collectors is acceptable for local/dev scaffolding, but it is dangerous in hosted execution because it can produce false-empty or fake-success output instead of failing explicitly.
- Hosted execution should also make durable-state expectations explicit so production-like deployments do not quietly depend on ephemeral local state.

# Scope
- In:
  - fail-fast hosted validation or bootstrap behavior when Graph-backed execution is expected but not really configured
  - preventing hosted fallback to stub auth/mail/calendar behavior in Graph-backed runtime paths
  - clarifying or enforcing durable hosted storage expectations for run history and related state
- Out:
  - digest wording or ranking changes
  - redesigning the hosted HTTP surface
  - changes to the separate `logics/skills` submodule

# Acceptance criteria
- AC1: Hosted environments cannot silently fall back to stub auth or static collectors when Graph-backed execution is expected.
- AC2: Hosted validation or bootstrap surfaces missing Graph/runtime prerequisites as explicit configuration failures.
- AC3: Durable hosted storage expectations are explicit enough in runtime validation and docs to avoid misleading ephemeral deployments.

# AC Traceability
- Req034 AC1 -> This item is the dedicated fail-fast runtime-contract slice for hosted execution. Proof: hosted Graph execution must stop on invalid prerequisites instead of degrading to stub behavior.
- Req034 AC3 -> This item explicitly covers durable hosted storage expectations and operational clarity. Proof: durable runtime requirements are part of the hosted contract enforced or documented here.
- Req034 AC7 -> This item requires the associated docs/runtime guidance to stay aligned. Proof: operator-facing hosted guidance changes with the stricter fail-fast contract.

# Links
- Request: `req_034_day_captain_hosted_runtime_fail_fast_and_identity_normalization`

# Priority
- Impact: High - silent fallback in hosted execution undermines trust in the whole product.
- Urgency: High - this is a runtime-correctness issue, not a polish issue.

# Notes
- Derived from the project review that highlighted hosted runtime fallback and durability ambiguity.
- Closed on Tuesday, March 10, 2026 after enforcing durable hosted storage, requiring explicit hosted Graph runtime inputs, and ensuring hosted bootstrap no longer degrades to stub runtime paths through invalid config.

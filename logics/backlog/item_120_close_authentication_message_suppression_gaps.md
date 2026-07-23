## item_120_close_authentication_message_suppression_gaps - Close authentication-message suppression gaps
> From version: 1.0.0
> Schema version: 1.0
> Status: Ready
> Understanding: 90%
> Confidence: 85%
> Progress: 0%
> Complexity: High
> Theme: Security
> Reminder: Update status/understanding/confidence/progress and linked request/task references when you edit this doc.

# Problem
- A temporary authentication message can still reach a rendered critical card, so the current detector misses at least one real-world login-link pattern.
- Suppression must be enforced once at the earliest shared boundary and verified across storage, metrics, recall, LLM input, memory, diagnostics, and rendering.
- Regression proof must use synthetic fixtures only, not copied mailbox content.

# Scope
- In:
  - Expand the deterministic sensitive-authentication classifier to cover login links, verification buttons, expiring access links, device confirmation prompts, one-time passcodes, password reset notices, and vendor-neutral authentication phrasing.
  - Apply the classifier at every collection path that can feed digest generation, recall, replay, metrics, and persisted run state.
  - Add synthetic replay fixtures for two bypass classes: expiring login-link email and button-based account-confirmation email.
  - Expose only aggregate sensitive_suppressions counts in payloads and metrics.
  - Add focused tests proving sensitive text is absent from stored runs, rendered HTML/text, LLM shortlist payloads, digest metrics, recall output, and replay exports.
- Out:
  - Storing redacted copies of sensitive messages for debugging.
  - Calling an external classifier for authentication detection.
  - Blocking ordinary operational security alerts that require user action but contain no temporary secret or login link.

# Acceptance criteria
- AC1: Synthetic login-link and account-confirmation fixtures are suppressed before scoring and never produce DigestCard objects.
- AC2: Tests prove no fixture secret phrase reaches storage, LLM input, metrics JSON, recall output, rendered HTML, rendered text, or replay export.
- AC3: A non-secret operational security alert remains eligible when it contains no temporary credential, code, or login-link intent.
- AC4: sensitive_suppressions increments as an integer count only, with no retained subject, preview, body, address, or vendor name.
- AC5: Existing authentication suppression tests still pass.

# AC Traceability
- request-AC1 -> This backlog slice. Proof: AC1: Synthetic login-link and account-confirmation fixtures are suppressed before scoring and never produce DigestCard objects.
- request-AC2 -> This backlog slice. Proof: AC2: Tests prove no fixture secret phrase reaches storage, LLM input, metrics JSON, recall output, rendered HTML, rendered text, or replay export.
- request-AC11 -> This backlog slice. Proof: AC3: A non-secret operational security alert remains eligible when it contains no temporary credential, code, or login-link intent.
- request-AC13 -> This backlog slice. Proof: AC4: sensitive_suppressions increments as an integer count only, with no retained subject, preview, body, address, or vendor name.
- request-AC14 -> This backlog slice. Proof: AC5: Existing authentication suppression tests still pass.

# Decision framing
- Product framing: Not needed
- Architecture framing: Not needed

# Links
- Product brief(s): `prod_004_day_captain_strict_decision_brief`
- Architecture decision(s): (none yet)
- Request: `req_057_day_captain_digest_friction_hardening`
- Primary task(s): `task_054_orchestrate_digest_friction_hardening`

# AI Context
- Summary: Close authentication-message suppression gaps
- Keywords: scaffolded-backlog, close authentication-message suppression gaps, implementation-ready
- Use when: Implementing the scaffolded slice for Close authentication-message suppression gaps.
- Skip when: The change belongs to another backlog slice.

# Priority
- Priority: High
- Rationale: Set by scaffold input or defaulted for grooming.

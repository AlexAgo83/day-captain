## item_110_generate_concrete_owner_aware_actions_and_deadlines - Generate concrete owner-aware actions and deadlines
> From version: 1.0.0
> Schema version: 1.0
> Status: Ready
> Understanding: 95
> Confidence: 90
> Progress: 0
> Complexity: High
> Theme: Intelligence
> Reminder: Update status/understanding/confidence/progress and linked request/task references when you edit this doc.

# Problem
- Generic actions such as reply, confirm, examine, or prepare do not tell the recipient what outcome is expected.
- Requests owned by another participant can be presented as if the digest recipient owns them.
- Deadline language and automatic-reply return dates are not consistently turned into scheduling signals.

# Scope
- In:
  - Only place entries in actions_to_take when ownership is user or shared; route other-owned work to watch_items with an explicit waiting-on label.
  - Extract a bounded verb, object, counterparty, and due date from the latest meaningful thread text using deterministic patterns and existing LLM rewriting only as an optional refinement.
  - Render specific actions such as send a named deliverable, call a contact, validate a document, correct a recipient, or follow up after an automatic-reply return date.
  - Suppress recommended_action when the system cannot identify a useful next step instead of emitting a generic fallback.
  - Extend DigestCard with due_at and due_source only if existing context_metadata cannot carry the fields safely.
  - Replace numeric confidence display with Reliable, Confirm, or Insufficient context plus one short evidence reason.
  - Require multiple independent suspicious signals for internal-domain messages unless a strong trust-boundary violation is present.
- Out:
  - Automatically executing the extracted action.
  - Guaranteeing natural-language deadline extraction for every language or phrasing.
  - Removing internal numeric scores used for deterministic ordering.

# Acceptance criteria
- AC1: Fixtures for user, shared, other, and unclear ownership land in the expected section and display the owner correctly.
- AC2: Explicit send, call, validate, correct-recipient, and follow-up-after-return requests render concrete next steps.
- AC3: A generic fallback is omitted when no concrete action can be derived.
- AC4: Due dates sort actionable entries before undated work and overdue items receive a visible warning.
- AC5: One internal message containing a normal shared link is not marked suspicious, while a fixture with multiple independent risk signals is.

# AC Traceability
- request-AC3 -> This backlog slice. Proof: AC1: Fixtures for user, shared, other, and unclear ownership land in the expected section and display the owner correctly.
- request-AC4 -> This backlog slice. Proof: AC2: Explicit send, call, validate, correct-recipient, and follow-up-after-return requests render concrete next steps.
- request-AC7 -> This backlog slice. Proof: AC3: A generic fallback is omitted when no concrete action can be derived.
- request-AC10 -> This backlog slice. Proof: AC4: Due dates sort actionable entries before undated work and overdue items receive a visible warning.

# Decision framing
- Product framing: Not needed
- Architecture framing: Not needed

# Links
- Product brief(s): `prod_002_day_captain_actionable_differential_brief`
- Architecture decision(s): (none yet)
- Request: `req_055_day_captain_production_digest_actionability_improvement`
- Primary task(s): `task_050_orchestrate_production_digest_actionability_improvements`

# AI Context
- Summary: Generate concrete owner-aware actions and deadlines
- Keywords: scaffolded-backlog, generate concrete owner-aware actions and deadlines, implementation-ready
- Use when: Implementing the scaffolded slice for Generate concrete owner-aware actions and deadlines.
- Skip when: The change belongs to another backlog slice.

# Priority
- Priority: High
- Rationale: High because incorrect ownership and generic actions directly undermine trust in the brief as an execution aid.

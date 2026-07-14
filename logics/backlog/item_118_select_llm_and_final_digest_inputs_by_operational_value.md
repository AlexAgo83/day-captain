## item_118_select_llm_and_final_digest_inputs_by_operational_value - Select LLM and final digest inputs by operational value
> From version: 1.0.0
> Schema version: 1.0
> Status: Ready
> Understanding: 90%
> Confidence: 85%
> Progress: 0%
> Complexity: Medium
> Theme: Intelligence
> Reminder: Update status/understanding/confidence/progress and linked request/task references when you edit this doc.

# Problem
- LlmDigestWordingEngine currently shortlists from already-prioritized items in order, so several medium-score items can consume the LLM budget before critical operational categories are represented.
- Keyword scoring can still produce action-looking cards that lack owner, object, deadline, or change evidence.
- A digest with no meaningful work should not be padded with weak watch items simply because they passed a low score threshold.

# Scope
- In:
  - Replace raw-order LLM shortlist selection with a small balanced selector.
  - Reserve bounded slots for transactional failures, user-owned actions, overdue/changed continuity, meeting conflicts, and highest-confidence watch items.
  - Add an evidence gate before final render: action cards require owner and concrete next step; critical cards require guardrail or real risk/deadline; watch cards require an explicit why-this-matters reason.
  - Suppress or downgrade unsupported generic actions rather than rendering vague fallback wording.
  - Allow a concise no-meaningful-work digest when no card passes the evidence gate.
  - Keep deterministic ordering stable for tests and replay metrics.
- Out:
  - Removing existing guardrails for delivery failures, security risk, flags, or explicit deadlines.
  - Adding a model-based ranker separate from the existing optional LLM wording path.
  - Changing delivery, recall, or storage contracts.

# Acceptance criteria
- AC1: A synthetic wrong-shortlist case sends the critical/action/conflict mix to LLM instead of the first N raw-score items.
- AC2: Unsupported action and watch fixtures are suppressed or downgraded and counted in usefulness metrics.
- AC3: A no-meaningful-work day renders a concise honest message with no padded cards.
- AC4: Critical transactional failures and user-owned explicit actions still outrank low-signal mail.
- AC5: Existing renderer budgets and multi-user isolation tests pass.

# AC Traceability
- request-AC3 -> This backlog slice. Proof: AC1: A synthetic wrong-shortlist case sends the critical/action/conflict mix to LLM instead of the first N raw-score items.
- request-AC6 -> This backlog slice. Proof: AC2: Unsupported action and watch fixtures are suppressed or downgraded and counted in usefulness metrics.
- request-AC7 -> This backlog slice. Proof: AC3: A no-meaningful-work day renders a concise honest message with no padded cards.
- request-AC9 -> This backlog slice. Proof: AC4: Critical transactional failures and user-owned explicit actions still outrank low-signal mail.
- request-AC10 -> This backlog slice. Proof: AC5: Existing renderer budgets and multi-user isolation tests pass.

# Decision framing
- Product framing: Not needed
- Architecture framing: Not needed

# Links
- Product brief(s): `prod_003_day_captain_useful_decision_brief`
- Architecture decision(s): (none yet)
- Request: `req_056_day_captain_digest_usefulness_intelligence`
- Primary task(s): `task_053_orchestrate_digest_usefulness_intelligence_improvements`

# AI Context
- Summary: Select LLM and final digest inputs by operational value
- Keywords: scaffolded-backlog, select llm and final digest inputs by operational value, implementation-ready
- Use when: Implementing the scaffolded slice for Select LLM and final digest inputs by operational value.
- Skip when: The change belongs to another backlog slice.

# Priority
- Priority: High
- Rationale: Set by scaffold input or defaulted for grooming.

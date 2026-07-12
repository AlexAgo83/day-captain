## item_109_reduce_digest_noise_and_enforce_concise_section_budgets - Reduce digest noise and enforce concise section budgets
> From version: 1.0.0
> Schema version: 1.0
> Status: Ready
> Understanding: 95
> Confidence: 90
> Progress: 0
> Complexity: Medium
> Theme: UX
> Reminder: Update status/understanding/confidence/progress and linked request/task references when you edit this doc.

# Problem
- The renderer currently applies a broad per-section limit that still allows long briefs with many similarly weighted cards.
- Unread messages, recurring entertainment newsletters, automatic replies, and low-signal watch items can consume space that should belong to explicit work.
- Empty sections and ambient information add reading cost even when there is no operational content.

# Scope
- In:
  - Apply daily section budgets of 3 critical items, 3 actions, 2 watch items, and 4 meetings; define a bounded weekly variant if weekly review needs more capacity.
  - Remove unread state as a scoring bonus while preserving its badge.
  - Filter recurring entertainment recaps, routine newsletters, bulk reports, and automatic replies unless flagged, transactional, deadline-bearing, or explicitly actionable.
  - Classify non-delivery reports and equivalent transactional failures as critical and generate a recipient-specific correction/resend action.
  - Omit empty critical/action/watch sections and place weather and external news after operational sections.
  - Default external news to at most one relevant item and allow it to be disabled without changing digest generation.
- Out:
  - Deleting unread metadata from collected messages.
  - Adding a new ranking service or external classifier.
  - Removing manual flags or transactional security guardrails.

# Acceptance criteria
- AC1: Renderer tests prove the daily section budgets and deterministic truncation order.
- AC2: A non-actionable unread newsletter is filtered while a flagged or transactional unread message remains eligible.
- AC3: A delivery-failure fixture is critical and recommends correcting the failed recipient before resending.
- AC4: Empty operational sections are omitted and ambient capsules never precede the action summary.
- AC5: Full tests pass without weakening tenant or user scoping.

# AC Traceability
- request-AC1 -> This backlog slice. Proof: AC1: Renderer tests prove the daily section budgets and deterministic truncation order.
- request-AC2 -> This backlog slice. Proof: AC2: A non-actionable unread newsletter is filtered while a flagged or transactional unread message remains eligible.
- request-AC4 -> This backlog slice. Proof: AC3: A delivery-failure fixture is critical and recommends correcting the failed recipient before resending.
- request-AC8 -> This backlog slice. Proof: AC4: Empty operational sections are omitted and ambient capsules never precede the action summary.
- request-AC10 -> This backlog slice. Proof: AC5: Full tests pass without weakening tenant or user scoping.

# Decision framing
- Product framing: Not needed
- Architecture framing: Not needed

# Links
- Product brief(s): `prod_002_day_captain_actionable_differential_brief`
- Architecture decision(s): (none yet)
- Request: `req_055_day_captain_production_digest_actionability_improvement`
- Primary task(s): `task_050_orchestrate_production_digest_actionability_improvements`

# AI Context
- Summary: Reduce digest noise and enforce concise section budgets
- Keywords: scaffolded-backlog, reduce digest noise and enforce concise section budgets, implementation-ready
- Use when: Implementing the scaffolded slice for Reduce digest noise and enforce concise section budgets.
- Skip when: The change belongs to another backlog slice.

# Priority
- Priority: High
- Rationale: High because reducing noise and enforcing section budgets is the lowest-risk prerequisite for every later actionability improvement.

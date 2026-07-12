## item_109_reduce_digest_noise_and_enforce_concise_section_budgets - Reduce digest noise and enforce concise section budgets
> From version: 1.0.0
> Schema version: 1.0
> Status: In progress
> Understanding: 100
> Confidence: 98
> Progress: 100
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
  - Filter recurring entertainment recaps, routine newsletters, bulk reports, passive presence, room holds, and automatic replies unless flagged, transactional, deadline-bearing, or explicitly actionable.
  - Parse automatic replies for a return date or alternate contact and turn them into deferred follow-up metadata rather than immediate reply actions.
  - Classify non-delivery reports and equivalent transactional failures as critical and generate a recipient-specific correction/resend action.
  - Omit empty critical/action/watch sections and place weather and external news after operational sections.
  - Default external news to at most one relevant item and allow it to be disabled without changing digest generation.
  - Remove signature-only, quoted-history-only, boilerplate-only, and low-information previews before ranking.
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
- AC6: A routine automatic reply becomes a deferred follow-up only when a usable return date or alternate contact exists.
- AC7: Signature-only and quoted-history-only messages do not consume a section budget.

# AC Traceability
- request-AC1 -> This backlog slice. Proof: AC1: Renderer tests prove the daily section budgets and deterministic truncation order.
- request-AC2 -> This backlog slice. Proof: AC2: A non-actionable unread newsletter is filtered while a flagged or transactional unread message remains eligible.
- request-AC4 -> This backlog slice. Proof: AC3: A delivery-failure fixture is critical and recommends correcting the failed recipient before resending.
- request-AC8 -> This backlog slice. Proof: AC4: Empty operational sections are omitted and ambient capsules never precede the action summary.
- request-AC10 -> This backlog slice. Proof: AC5: Full tests pass without weakening tenant or user scoping.
- request-AC6 -> This backlog slice. Evidence needed: Meeting cards surface conflicts, tight transitions, and preparation evidence only when supported by a document, open decision, prior commitment, relevant thread, or explicit preparation request; routine and placeholder meetings remain compact.
- request-AC7 -> This backlog slice. Evidence needed: Confidence is displayed as Reliable, Confirm, or Insufficient context with a specific reason; suspicious-mail warnings require multiple independent weak signals or one strong trust-boundary violation and do not penalize language alone.
- request-AC9 -> This backlog slice. Evidence needed: Recipient preferences can prioritize trusted senders and themes, suppress low-value topics or recurring items, and accept reversible Useful or Hide similar feedback without sharing state across users.
- request-AC11 -> This backlog slice. Evidence needed: Application access is restricted to required mailboxes, sender-side copies have an explicit retention policy, and diagnostics contain no raw subjects, previews, bodies, names, addresses, tokens, or secrets.
- request-AC12 -> This backlog slice. Evidence needed: An anonymized replay suite reproduces sensitive-auth, noise, ownership, deadline, delivery-failure, continuity, meeting-conflict, rendering, and localization cases; focused and full automated tests pass.
- request-AC13 -> This backlog slice. Evidence needed: Daily and weekly HTML are visually validated in rendered artifacts, and any necessary live delivery test is sent only to the explicitly authorized single test mailbox; no other production recipient is contacted during development or acceptance.
- request-AC14 -> This backlog slice. Evidence needed: Rollout uses a bounded shadow comparison or equivalent safe preview, proves at least a 40% median visible-length reduction and 80% generic-action reduction with zero surfaced authentication secrets, then repeats the sender-side production audit after release.

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

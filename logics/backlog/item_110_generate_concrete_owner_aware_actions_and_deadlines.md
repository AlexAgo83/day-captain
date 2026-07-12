## item_110_generate_concrete_owner_aware_actions_and_deadlines - Generate concrete owner-aware actions and deadlines
> From version: 1.0.0
> Schema version: 1.0
> Status: In progress
> Understanding: 100
> Confidence: 98
> Progress: 100
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
  - Classify each item as request, decision, information, blocker, waiting state, document delivery, automatic reply, or incident before generating an action.
  - Render specific actions such as send a named deliverable, call a contact, validate a document, correct a recipient, or follow up after an automatic-reply return date.
  - Suppress recommended_action when the system cannot identify a useful next step instead of emitting a generic fallback.
  - Clean salutations, signatures, phone-only fragments, Outlook separators, meeting join boilerplate, quoted history, and legal text before action extraction; preserve the original cleaned subject when reconstruction is less reliable.
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
- AC6: Decision and information fixtures do not become generic reply actions, and low-information previews do not produce invented actions.
- AC7: Deterministic extraction owns action semantics; optional LLM rewriting cannot add an unsupported owner, object, counterparty, or deadline.

# AC Traceability
- request-AC3 -> This backlog slice. Proof: AC1: Fixtures for user, shared, other, and unclear ownership land in the expected section and display the owner correctly.
- request-AC4 -> This backlog slice. Proof: AC2: Explicit send, call, validate, correct-recipient, and follow-up-after-return requests render concrete next steps.
- request-AC7 -> This backlog slice. Proof: AC3: A generic fallback is omitted when no concrete action can be derived.
- request-AC10 -> This backlog slice. Proof: AC4: Due dates sort actionable entries before undated work and overdue items receive a visible warning.
- request-AC5 -> This backlog slice. Evidence needed: Cross-run continuity follows stable mail threads and distinguishes new, changed, still open, waiting, overdue, resolved, and suppressed unchanged states without treating read state as completion.
- request-AC6 -> This backlog slice. Evidence needed: Meeting cards surface conflicts, tight transitions, and preparation evidence only when supported by a document, open decision, prior commitment, relevant thread, or explicit preparation request; routine and placeholder meetings remain compact.
- request-AC8 -> This backlog slice. Evidence needed: Daily and weekly subjects are distinct, empty operational sections are omitted, operational deltas precede ambient content, external news is optional/relevant/deduplicated, and weather is compact and validated.
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
- Summary: Generate concrete owner-aware actions and deadlines
- Keywords: scaffolded-backlog, generate concrete owner-aware actions and deadlines, implementation-ready
- Use when: Implementing the scaffolded slice for Generate concrete owner-aware actions and deadlines.
- Skip when: The change belongs to another backlog slice.

# Priority
- Priority: High
- Rationale: High because incorrect ownership and generic actions directly undermine trust in the brief as an execution aid.

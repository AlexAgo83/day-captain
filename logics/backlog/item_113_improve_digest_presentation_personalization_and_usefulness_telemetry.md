## item_113_improve_digest_presentation_personalization_and_usefulness_telemetry - Improve digest presentation personalization and usefulness telemetry
> From version: 1.0.0
> Schema version: 1.0
> Status: Ready
> Understanding: 98
> Confidence: 95
> Progress: 0
> Complexity: Medium
> Theme: UX
> Reminder: Update status/understanding/confidence/progress and linked request/task references when you edit this doc.

# Problem
- Daily and weekly emails can have identical subjects and visually similar cards despite very different operational impact.
- Weather and external news lack validation and relevance controls.
- The product cannot currently demonstrate which cards were useful or repeatedly ignored.

# Scope
- In:
  - Pass run type into rendering and use distinct localized daily and weekly subject formats.
  - Add a compact delta header with new actions, today's deadlines, suppressed unchanged items, and resolved items.
  - Render a top delta summary before all optional ambient content and give delivery failures, deadlines, and user-owned actions stronger visual hierarchy.
  - Validate weather min/max ordering, absolute bounds, and implausible day-over-day changes; omit invalid values and log a content-free diagnostic.
  - Filter external news by configured product themes and limit it to one item in daily mode; allow a larger but bounded weekly selection.
  - Deduplicate external news across runs by stable URL or normalized headline and keep daily news disabled by default unless explicitly enabled.
  - Add Useful and Hide similar item feedback actions using the existing feedback path where feasible.
  - Support reversible per-user preferences for trusted senders, priority themes, muted topics, low-value recurring meetings, and hidden item types.
  - Record content-free telemetry for impressions, opens, recall actions, suppressions, unchanged repeats, and explicit feedback.
  - Expose aggregate usefulness metrics by run type and user without retaining raw subjects, previews, bodies, names, or addresses in telemetry.
  - Keep numeric confidence internal and render only Reliable, Confirm, or Insufficient context with a specific short reason.
  - Normalize localized reply prefixes, status labels, and system wording without translating names or technical identifiers.
- Out:
  - Tracking pixels or covert read tracking.
  - Sending mailbox content to an external analytics platform.
  - A dashboard beyond a bounded export or operator-readable aggregate in this delivery slice.

# Acceptance criteria
- AC1: Daily and weekly subjects are distinct in French and English renderer tests.
- AC2: Operational delta and action content appears before weather and news.
- AC3: Invalid weather is omitted with a safe diagnostic and valid extreme weather remains visible.
- AC4: Daily external news is absent or limited to one configured relevant theme match.
- AC5: Feedback and aggregate telemetry contain identifiers and event types but no raw mailbox content or production identity.
- AC6: Repeated news does not reappear, and daily mode contains zero news by default or at most one explicitly enabled relevant item.
- AC7: User preference changes are reversible and never affect another user's ranking or suppression state.
- AC8: Median visible daily output is bounded by a 3,000-character target and a 4,500-character hard warning threshold in replay metrics.

# AC Traceability
- request-AC7 -> This backlog slice. Proof: AC1: Daily and weekly subjects are distinct in French and English renderer tests.
- request-AC8 -> This backlog slice. Proof: AC2: Operational delta and action content appears before weather and news.
- request-AC9 -> This backlog slice. Proof: AC3: Invalid weather is omitted with a safe diagnostic and valid extreme weather remains visible.
- request-AC10 -> This backlog slice. Proof: AC4: Daily external news is absent or limited to one configured relevant theme match.
- request-AC5 -> This backlog slice. Evidence needed: Cross-run continuity follows stable mail threads and distinguishes new, changed, still open, waiting, overdue, resolved, and suppressed unchanged states without treating read state as completion.
- request-AC6 -> This backlog slice. Evidence needed: Meeting cards surface conflicts, tight transitions, and preparation evidence only when supported by a document, open decision, prior commitment, relevant thread, or explicit preparation request; routine and placeholder meetings remain compact.
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
- Summary: Improve digest presentation personalization and usefulness telemetry
- Keywords: scaffolded-backlog, improve digest presentation personalization and usefulness telemetry, implementation-ready
- Use when: Implementing the scaffolded slice for Improve digest presentation personalization and usefulness telemetry.
- Skip when: The change belongs to another backlog slice.

# Priority
- Priority: Medium
- Rationale: Medium because presentation and measurement should follow the higher-priority selection, ownership, and continuity corrections they evaluate.

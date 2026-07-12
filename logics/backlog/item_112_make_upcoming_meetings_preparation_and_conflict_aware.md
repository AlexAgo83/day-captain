## item_112_make_upcoming_meetings_preparation_and_conflict_aware - Make upcoming meetings preparation and conflict aware
> From version: 1.0.0
> Schema version: 1.0
> Status: Ready
> Understanding: 95
> Confidence: 90
> Progress: 0
> Complexity: Medium
> Theme: Calendar
> Reminder: Update status/understanding/confidence/progress and linked request/task references when you edit this doc.

# Problem
- Meeting cards often repeat generic preparation advice even when no preparation evidence exists.
- Overlapping or tightly adjacent meetings are not clearly elevated as scheduling conflicts.
- Related mail context is available but does not consistently yield decisions, documents, commitments, or questions.

# Scope
- In:
  - Only render a meeting action when related context contains an explicit preparation request, document, open decision, prior commitment, or unresolved question.
  - Detect overlaps and gaps shorter than 15 minutes after meeting collection and render a critical conflict summary.
  - Summarize at most one prior decision, one open commitment, one relevant document, and one question for each preparation-worthy meeting.
  - Keep placeholder and presence events out of preparation actions while preserving useful location context.
  - Prefer concrete wording over generic keep-in-view or prepare-key-points fallbacks.
- Out:
  - Automatically rescheduling meetings.
  - Fetching new document content beyond context already available to the application.
  - Generating preparation content when no supporting evidence exists.

# Acceptance criteria
- AC1: A context-free meeting renders without a recommended preparation action.
- AC2: A meeting with a linked request or document renders the specific preparation evidence.
- AC3: Overlapping meetings and sub-15-minute transitions produce a visible conflict or tight-transition warning.
- AC4: Placeholder and all-day presence fixtures do not become preparation tasks.

# AC Traceability
- request-AC6 -> This backlog slice. Proof: AC1: A context-free meeting renders without a recommended preparation action.
- request-AC10 -> This backlog slice. Proof: AC2: A meeting with a linked request or document renders the specific preparation evidence.

# Decision framing
- Product framing: Not needed
- Architecture framing: Not needed

# Links
- Product brief(s): `prod_002_day_captain_actionable_differential_brief`
- Architecture decision(s): (none yet)
- Request: `req_055_day_captain_production_digest_actionability_improvement`
- Primary task(s): `task_050_orchestrate_production_digest_actionability_improvements`

# AI Context
- Summary: Make upcoming meetings preparation and conflict aware
- Keywords: scaffolded-backlog, make upcoming meetings preparation and conflict aware, implementation-ready
- Use when: Implementing the scaffolded slice for Make upcoming meetings preparation and conflict aware.
- Skip when: The change belongs to another backlog slice.

# Priority
- Priority: Medium
- Rationale: Medium because meeting preparation adds meaningful value after the core mail-action and continuity signals are trustworthy.

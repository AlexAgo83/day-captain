## item_122_polish_outlook_and_text_rendering_ergonomics - Polish Outlook and text rendering ergonomics
> From version: 1.0.0
> Schema version: 1.0
> Status: Ready
> Understanding: 90%
> Confidence: 85%
> Progress: 0%
> Complexity: Medium
> Theme: Email rendering
> Reminder: Update status/understanding/confidence/progress and linked request/task references when you edit this doc.

# Problem
- Delivered output can concatenate labels, metadata, recurring badges, and quick-action links without visible separators.
- Meeting and Outlook open controls repeat enough to compete with the actual card content.
- Plain-text fallback has the same spacing problems, which makes quick scanning harder.

# Scope
- In:
  - Normalize spacing around section labels, badges, metadata labels, recurring/evolving markers, quick-action links, and footer controls.
  - Group quick actions into separated links in text and visually separated buttons in HTML.
  - Render meeting open controls as compact secondary actions, with at most one primary open action per meeting card.
  - Add renderer snapshot or structural assertions for French daily output, weekly output, meeting-heavy output, and empty/compact output.
  - Update the rendering validation doc with the exact spacing/control checks a human reviewer should perform.
- Out:
  - Changing the email transport.
  - Adding a CSS framework.
  - Removing the recall actions.

# Acceptance criteria
- AC1: Tests fail on concatenated text patterns for scope labels, badge-title joins, and quick-action joins.
- AC2: HTML quick actions render as distinct controls and text quick actions render with readable separators.
- AC3: Meeting cards expose open controls without repeating both generic and desktop variants as equally weighted card text.
- AC4: Desktop and narrow-width validation instructions cover section rhythm, wrapping, buttons, metadata, and footer spacing.

# AC Traceability
- request-AC6 -> This backlog slice. Proof: AC1: Tests fail on concatenated text patterns for scope labels, badge-title joins, and quick-action joins.
- request-AC7 -> This backlog slice. Proof: AC2: HTML quick actions render as distinct controls and text quick actions render with readable separators.
- request-AC8 -> This backlog slice. Proof: AC3: Meeting cards expose open controls without repeating both generic and desktop variants as equally weighted card text.
- request-AC12 -> This backlog slice. Proof: AC4: Desktop and narrow-width validation instructions cover section rhythm, wrapping, buttons, metadata, and footer spacing.

# Decision framing
- Product framing: Not needed
- Architecture framing: Not needed

# Links
- Product brief(s): `prod_004_day_captain_strict_decision_brief`
- Architecture decision(s): (none yet)
- Request: `req_057_day_captain_digest_friction_hardening`
- Primary task(s): `task_054_orchestrate_digest_friction_hardening`

# AI Context
- Summary: Polish Outlook and text rendering ergonomics
- Keywords: scaffolded-backlog, polish outlook and text rendering ergonomics, implementation-ready
- Use when: Implementing the scaffolded slice for Polish Outlook and text rendering ergonomics.
- Skip when: The change belongs to another backlog slice.

# Priority
- Priority: High
- Rationale: Set by scaffold input or defaulted for grooming.

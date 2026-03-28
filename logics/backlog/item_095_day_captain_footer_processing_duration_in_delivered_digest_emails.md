## item_095_day_captain_footer_processing_duration_in_delivered_digest_emails - Day Captain footer processing duration in delivered digest emails
> From version: 1.8.0
> Schema version: 1.0
> Status: Ready
> Understanding: 98%
> Confidence: 95%
> Progress: 0%
> Complexity: Low
> Theme: Delivery
> Reminder: Update status/understanding/confidence/progress and linked task references when you edit this doc.

# Problem
- Show the digest processing duration in the delivered email footer.
- Display that duration directly under `Day Captain © 2026` so the operator can see how long the current digest took to generate.
- Make the displayed duration reflect the digest generation pipeline itself, not the downstream email transport latency.
- - The delivered digest already ends with a small footer block that includes the project signature line `Day Captain © 2026`.
- - That footer is a natural place for lightweight operator-facing runtime metadata.

# Scope
- In:
- Out:

```mermaid
%% logics-kind: backlog
%% logics-signature: backlog|day-captain-footer-processing-duration-i|req-049-day-captain-footer-processing-du|show-the-digest-processing-duration-in|ac1-delivered-digest-emails-include-a
flowchart LR
    Request[req_049_day_captain_footer_processing_dura] --> Problem[Show the digest processing duration in]
    Problem --> Scope[Day Captain footer processing duration in]
    Scope --> Acceptance[AC1: Delivered digest emails include a]
    Acceptance --> Tasks[Execution task]
```

# Acceptance criteria
- AC1: Delivered digest emails include a processing-duration line directly below `Day Captain © 2026` in the footer.
- AC2: The displayed value reflects the current digest generation duration, measured from run start until the delivery content is ready, and does not depend on downstream mailbox delivery latency.
- AC3: Both text and HTML rendering paths display the same duration information in a readable operator-facing format.
- AC4: If timing metadata is unavailable, the digest still renders safely without breaking footer layout or delivery.
- AC5: Tests cover timing capture/propagation and footer rendering.

# AC Traceability
- AC1 -> Scope: Delivered digest emails include a processing-duration line directly below `Day Captain © 2026` in the footer.. Proof: Implement through `task_046_day_captain_footer_timing_and_meeting_open_link_orchestration`.
- AC2 -> Scope: The displayed value reflects the current digest generation duration, measured from run start until the delivery content is ready, and does not depend on downstream mailbox delivery latency.. Proof: Timing contract and measurement point are explicitly staged in `task_046_day_captain_footer_timing_and_meeting_open_link_orchestration`.
- AC3 -> Scope: Both text and HTML rendering paths display the same duration information in a readable operator-facing format.. Proof: Shared renderer validation is required by `task_046_day_captain_footer_timing_and_meeting_open_link_orchestration`.
- AC4 -> Scope: If timing metadata is unavailable, the digest still renders safely without breaking footer layout or delivery.. Proof: Safe fallback behavior is part of the bounded renderer update in `task_046_day_captain_footer_timing_and_meeting_open_link_orchestration`.
- AC5 -> Scope: Tests cover timing capture/propagation and footer rendering.. Proof: Focused renderer and app regression coverage is required by `task_046_day_captain_footer_timing_and_meeting_open_link_orchestration`.

# Decision framing
- Product framing: Not needed
- Product signals: (none detected)
- Product follow-up: No product brief follow-up is expected based on current signals.
- Architecture framing: Not needed
- Architecture signals: Small renderer and payload propagation change.
- Architecture follow-up: No ADR is expected unless the timing contract expands beyond this bounded footer feature.

# Links
- Product brief(s): (none yet)
- Architecture decision(s): (none yet)
- Request: `req_049_day_captain_footer_processing_duration_in_delivered_digest_emails`
- Primary task(s): `task_046_day_captain_footer_timing_and_meeting_open_link_orchestration`

# AI Context
- Summary: Show the current digest generation duration below the Day Captain footer signature without conflating it with email transport...
- Keywords: footer duration, digest generation timing, email footer metadata, processing time, delivery footer
- Use when: The work is about exposing current-run generation time inside the delivered digest footer.
- Skip when: The work is about broader performance instrumentation, dashboards, or transport latency measurement.

# References
- `Footer rendering: [services.py](/Users/alexandreagostini/Documents/day-captain/src/day_captain/services.py)`
- `Application orchestration and run lifecycle: [app.py](/Users/alexandreagostini/Documents/day-captain/src/day_captain/app.py)`
- `logics/skills/logics-ui-steering/SKILL.md`

# Priority
- Impact:
- Urgency:

# Notes
- Derived from request `req_049_day_captain_footer_processing_duration_in_delivered_digest_emails`.
- Source file: `logics/request/req_049_day_captain_footer_processing_duration_in_delivered_digest_emails.md`.
- Request context seeded into this backlog item from `logics/request/req_049_day_captain_footer_processing_duration_in_delivered_digest_emails.md`.

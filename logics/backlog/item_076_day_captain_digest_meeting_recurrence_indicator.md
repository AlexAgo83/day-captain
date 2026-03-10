## item_076_day_captain_digest_meeting_recurrence_indicator - Expose a visible recurrence indicator on meeting cards when calendar metadata supports it
> From version: 1.5.1
> Status: Ready
> Understanding: 96%
> Confidence: 94%
> Progress: 0%
> Complexity: Small
> Theme: Product Quality
> Reminder: Update status/understanding/confidence/progress and linked task references when you edit this doc.

# Problem
- Upcoming meetings are visible and readable, but the digest does not currently tell the user whether a meeting is part of a recurrence.
- That distinction matters because a recurring ritual such as a daily or 1:1 does not carry the same meaning as a one-off meeting, even if the title looks similar.

# Scope
- In:
  - detecting recurrence when the calendar metadata already supports that distinction
  - showing a visible recurrence indicator on meeting cards
  - keeping the indicator compact and Outlook-safe
  - tests for recurring versus non-recurring meeting rendering
- Out:
  - meeting-series management features
  - inference of recurrence from heuristics alone when the calendar data does not support it
  - redesign of meeting cards beyond a bounded indicator

# Acceptance criteria
- AC1: Meeting cards can indicate when an event is part of a recurrence if the calendar metadata supports that conclusion.
- AC2: Non-recurring meetings are not mislabeled as recurring.
- AC3: The recurrence indicator remains compact and visually subordinate to the main meeting information.
- AC4: Tests cover representative recurring and non-recurring meeting cases.

# AC Traceability
- Req035 AC6 -> This item is the dedicated recurrence-indicator slice. Proof: it explicitly covers visible recurrence indication on meeting cards.
- Req035 AC8 -> This item requires recurrence rendering coverage. Proof: closure depends on representative recurring/non-recurring tests.

# Links
- Request: `req_035_day_captain_digest_summary_coherence_privacy_weather_and_footer_polish`

# Priority
- Impact: Medium - the signal improves meeting comprehension without changing core digest structure.
- Urgency: Medium - useful and visible, but not a blocker.

# Notes
- Derived from live digest review where recurring meetings were visible but not explicitly identified as recurring.

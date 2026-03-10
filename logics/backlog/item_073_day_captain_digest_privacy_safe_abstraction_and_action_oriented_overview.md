## item_073_day_captain_digest_privacy_safe_abstraction_and_action_oriented_overview - Reduce over-literal business carry-over and make overview/confidence wording more action-oriented
> From version: 1.5.1
> Status: Ready
> Understanding: 97%
> Confidence: 95%
> Progress: 0%
> Complexity: Medium
> Theme: Product Quality
> Reminder: Update status/understanding/confidence/progress and linked task references when you edit this doc.

# Problem
- Some visible summaries and `En bref` lines still carry raw business fragments too literally, which makes the digest feel closer to excerpt reuse than assistant synthesis.
- The product should stay useful without exposing more operational or business detail than necessary in the rendered output.
- Confidence remains helpful, but the current reason line is sometimes too long and repetitive for fast scanning.

# Scope
- In:
  - safer abstraction rules for visible digest copy
  - more action-oriented `En bref` wording
  - lighter confidence reason wording on cards
  - tests and docs for the editorial/privacy-safe behavior
- Out:
  - generalized privacy classification or redaction infrastructure
  - hiding all source meaning behind vague summaries
  - layout redesign of confidence rendering

# Acceptance criteria
- AC1: Representative summaries and top-summary lines are more assistant-style and less like direct raw business-fragment carry-over.
- AC2: Digest wording stays useful while avoiding unnecessary exposure of raw business detail in visible copy.
- AC3: Confidence reason wording is shorter and easier to scan without removing the confidence signal itself.
- AC4: Tests and docs cover the abstraction and shorter-confidence-copy behavior.

# AC Traceability
- Req035 AC3 -> This item is the dedicated abstraction and action-oriented overview slice. Proof: it explicitly covers less literal visible wording.
- Req035 AC4 -> This item also covers lighter confidence copy. Proof: shorter confidence reasons are part of the same editorial-output pass.
- Req035 AC7 -> This item requires aligned tests and docs. Proof: closure depends on updated wording and coverage.

# Links
- Request: `req_035_day_captain_digest_summary_coherence_privacy_weather_and_footer_polish`

# Priority
- Impact: High - over-literal visible wording reduces both trust and discretion.
- Urgency: Medium - the digest is usable, but this is a meaningful product-quality gap.

# Notes
- Derived from live Outlook review and explicit product guidance to avoid exposing business content too literally in visible digest text.

## item_072_day_captain_digest_summary_coherence_length_and_short_message_handling - Fix fragmented summaries, relax hard stops, and improve short-message rendering
> From version: 1.5.1
> Status: Done
> Understanding: 100%
> Confidence: 97%
> Progress: 100%
> Complexity: Medium
> Theme: Product Quality
> Reminder: Update status/understanding/confidence/progress and linked task references when you edit this doc.

# Problem
- Some digest summaries still begin in the middle of a phrase or stop too abruptly, which makes them look like half-cleaned mail excerpts.
- The current bounded length can become too short to carry a coherent phrase in cases where a location, purpose, or subject needs one more clause to make sense.
- Product direction now accepts longer summary text when needed, provided the output stays bounded and readable.
- Product direction also allows the bound to vary by item type instead of forcing one rigid limit everywhere.
- Very short direct messages such as `Voici !` currently produce weak assistant wording because the output contract treats them like normal summary material.
- More broadly, surfaced thread summaries should routinely use earlier thread context to strengthen the visible synthesis, with special care for cases where the latest reply is too short to stand on its own.

# Scope
- In:
  - summary-boundary cleanup so cards do not start or end at visibly awkward points
  - relaxing the current summary-size cap enough to preserve coherent phrasing where useful
  - allowing different bounded length caps by item type when that improves coherence
  - better rendering rules for very short direct-message content
  - explicit use of earlier thread context to reinforce surfaced thread synthesis by default
  - tests for fragmented-summary and short-message cases
- Out:
  - rewriting the whole briefing architecture
  - removing all bounded length constraints entirely
  - changing card layout or section structure

# Acceptance criteria
- AC1: Representative digest summaries no longer begin mid-sentence or end at obvious fragment cut points.
- AC2: Summary length remains bounded but is permissive enough to keep a coherent phrase in cases that would otherwise stop too early.
- AC2 supporting rule: the allowed summary length can increase visibly when needed to avoid cutting a meaningful phrase too early.
- AC2 supporting rule: the bound can vary by item type if that produces cleaner mail-card, meeting-card, and overview wording.
- AC3: Very short direct messages are rendered with more natural assistant wording than a literal source echo.
- AC3 supporting rule: surfaced thread summaries use older thread context by default when it helps recover the real subject or intent of the exchange.
- AC4: Tests cover fragment cleanup, longer coherent phrasing, and short direct-message cases.

# AC Traceability
- Req035 AC1 -> This item is the dedicated summary-coherence and bounded-length slice. Proof: it explicitly targets awkward starts/stops and coherent phrasing.
- Req035 AC1 supporting length direction -> This item also carries the more-generous-but-still-bounded summary length rule. Proof: longer coherent phrasing belongs to this slice.
- Req035 AC1 supporting rule on variable bounds -> This item also carries the variable-by-item-type bound rule. Proof: cleaner summary limits belong to the same slice.
- Req035 AC2 -> This item is also the short-message-rendering slice. Proof: weak direct-message wording remains part of the same problem family.
- Req035 AC2 supporting rule -> This item explicitly makes older thread context part of the default synthesis path. Proof: stronger thread-aware summaries are part of this slice, not an edge-case fallback only.
- Req035 AC8 -> This item requires regression coverage for the affected summary cases. Proof: closure depends on fragment and short-message tests.

# Links
- Request: `req_035_day_captain_digest_summary_coherence_privacy_weather_and_footer_polish`

# Priority
- Impact: High - fragmented summaries undermine trust in the digest immediately.
- Urgency: High - this is visible in live mail samples already.

# Notes
- Derived from live Outlook review where summaries still looked partially mechanical or incomplete.
- Closed on Wednesday, March 11, 2026 after implementing thread-reinforced preview selection, more generous item-type bounds, and regression tests for short replies.

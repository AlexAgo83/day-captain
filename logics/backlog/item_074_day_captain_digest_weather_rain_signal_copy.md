## item_074_day_captain_digest_weather_rain_signal_copy - Add a rain expectation signal to the weather line when forecast data supports it
> From version: 1.5.1
> Status: Ready
> Understanding: 96%
> Confidence: 94%
> Progress: 0%
> Complexity: Small
> Theme: Product Quality
> Reminder: Update status/understanding/confidence/progress and linked task references when you edit this doc.

# Problem
- The weather line already gives temperature context, but a practical daily question remains unanswered: is rain expected.
- The digest user often needs a simple weather-action hint rather than temperature alone.

# Scope
- In:
  - weather copy that indicates rain expectation when the forecast data supports it
  - bounded wording that fits the existing weather line/capsule
  - tests for representative rain and no-rain cases
- Out:
  - replacing the current weather provider
  - introducing fine-grained precipitation analytics or a new weather UI block

# Acceptance criteria
- AC1: The weather line can indicate when rain is expected on the forecast day if the available data supports that conclusion.
- AC2: The no-rain case remains clear and does not degrade existing temperature wording.
- AC3: Tests cover representative rain and non-rain copy cases.

# AC Traceability
- Req035 AC5 -> This item is the dedicated weather-rain-copy slice. Proof: it explicitly adds a rain expectation signal when data allows it.
- Req035 AC7 -> This item requires representative weather-copy coverage. Proof: closure depends on rain/no-rain tests.

# Links
- Request: `req_035_day_captain_digest_summary_coherence_privacy_weather_and_footer_polish`

# Priority
- Impact: Medium - practical daily usefulness improves immediately.
- Urgency: Medium - not critical, but directly helpful in the live digest.

# Notes
- Derived from live digest review where temperature was visible but precipitation expectation was still missing.

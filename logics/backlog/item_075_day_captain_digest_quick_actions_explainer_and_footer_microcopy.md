## item_075_day_captain_digest_quick_actions_explainer_and_footer_microcopy - Explain the quick-action buttons and add a small Day Captain footer line
> From version: 1.5.1
> Status: Ready
> Understanding: 100%
> Confidence: 96%
> Progress: 0%
> Complexity: Small
> Theme: Product Quality
> Reminder: Update status/understanding/confidence/progress and linked task references when you edit this doc.

# Problem
- The quick-action buttons work, but the current intro text `Ouvre un brouillon Day Captain.` does not clearly explain what each button is for.
- The digest currently ends without a small branded footer, which leaves the bottom of the mail a bit abrupt.
- Product direction is to keep the helper copy slightly explanatory, not just terse, and to use a minimal footer of the form `Day Captain © YEAR` with the text linked to GitHub.

# Scope
- In:
  - replacing the quick-actions intro line with copy that explains the purpose of the buttons
  - adding a small Day Captain footer/copyright line with a hyperlink on the product name to GitHub
  - keeping the changes Outlook-safe and visually quiet
- Out:
  - redesigning the quick-action controls
  - adding legal boilerplate or large branding blocks

# Acceptance criteria
- AC1: The quick-actions area explains the purpose of the recall buttons more clearly than the current generic draft wording.
- AC1 supporting rule: the helper copy is slightly explanatory rather than overly terse.
- AC2: The digest includes a small `Day Captain © YEAR` footer/copyright line with the product name linked to GitHub.
- AC3: Rendering remains stable in text and HTML outputs.

# AC Traceability
- Req035 AC6 -> This item is the dedicated quick-actions and footer microcopy slice. Proof: it explicitly covers both requested bottom-of-mail changes.
- Req035 AC7 -> This item requires stable rendering coverage. Proof: closure depends on text and HTML behavior staying aligned.

# Links
- Request: `req_035_day_captain_digest_summary_coherence_privacy_weather_and_footer_polish`

# Priority
- Impact: Medium - small copy changes, but they affect every delivered digest.
- Urgency: Medium - visible polish gap rather than a functional blocker.

# Notes
- Derived from live digest review of the bottom-of-mail experience.

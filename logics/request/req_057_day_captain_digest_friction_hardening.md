## req_057_day_captain_digest_friction_hardening - Day Captain digest friction hardening
> From version: 1.0.0
> Schema version: 1.0
> Status: Draft
> Understanding: 90%
> Confidence: 85%
> Complexity: High
> Theme: UX
> Reminder: Update status/understanding/confidence and linked backlog/task references when you edit this doc.

# Needs
- Turn the current digest from a still-noisy operational summary into a strict daily command brief that surfaces only what the recipient can act on or must watch.
- Close the remaining sensitive-authentication gap so login codes, magic links, and equivalent authentication messages cannot appear in critical cards, summaries, metrics, recall output, or rendered emails.
- Reduce visible fatigue from repeated external-news, confidence, meeting-open, and quick-action controls while preserving real delivery failures, explicit deadlines, and meeting conflicts.
- Fix plain-text and HTML rendering seams that make the delivered email look machine-generated, including concatenated labels, crowded buttons, and mixed-language confidence labels.
- Investigate recent sender-mailbox delivery-count anomalies without persisting mailbox content or exposing recipient identities.

# Context
- A recent content-free review of sent Day Captain briefs found that daily output remains long enough to feel like a mailbox digest rather than a decision brief.
- The same review found a temporary authentication message surfacing as a critical item, which means the existing sensitive-authentication suppression is too narrow or is not applied at every ingestion and replay boundary.
- External news appeared in every sampled brief, including dense operational briefs, creating filler-like reading cost when it is not connected to the recipient's active work.
- Confidence labels appear frequently and can mix languages, making the digest feel uncertain even when the user needs a concrete next step.
- Rendered text contains spacing and grouping issues such as adjacent labels/buttons without separators, which harms trust in the email even when the underlying ranking is useful.
- Meeting and Outlook open controls are useful but repeated heavily enough to dominate visual weight in long briefs.
- Recent content-free delivery counts show the normal one-message-per-recipient shape, but some runs produced fewer or more messages than the expected target count. This must be diagnosed from content-free delivery metadata only.
- All evidence in this corpus is anonymized and aggregate-only. No real mailbox addresses, personal names, client names, supplier names, message subjects, previews, bodies, run IDs, tenant names, or hosted URLs are included.

# Acceptance criteria
- AC1: Authentication codes, password resets, magic links, login prompts, and equivalent temporary access messages are suppressed before storage, scoring, LLM input, metrics, memory, recall, diagnostics, and rendering.
- AC2: The built-in replay contains at least two synthetic authentication-message variants that previously bypassed suppression, and both are absent from every downstream artifact.
- AC3: Daily briefs follow a strict decision-brief budget: at most one top priority summary, 3 user-owned actions, 2 watch items, 4 meetings, and optional ambient content only when relevant.
- AC4: External news is omitted by default from daily briefs unless it matches configured work themes or explicit user preference; weekly briefs may include a small bounded digest.
- AC5: Confidence labels render only when uncertainty changes the user's decision, are localized consistently, and never appear as English strings in French output.
- AC6: HTML and text rendering preserve readable spacing between labels, card badges, metadata, and quick-action links, including plain-text fallback output.
- AC7: Meeting and Outlook open controls remain available but are visually compact and do not repeat in a way that dominates card content.
- AC8: The top summary states what changed, what needs action, what is waiting on someone else, and what can be ignored, without restating full card text.
- AC9: Scheduler and content-free delivery audit tooling can report expected target count, sent count, duplicate trigger signals, retry signals, and fan-out shape without reading or storing message bodies.
- AC10: Delivery-count anomaly checks cover duplicate sends, missing target sends, retry overlap, weekly/daily overlap, and manual recall overlap using synthetic or content-free fixtures.
- AC11: Existing multi-user isolation, recall, feedback, Graph delivery guardrails, and content-free diagnostics remain covered by focused and full tests.
- AC12: Representative daily and weekly HTML/text artifacts pass desktop and narrow-width review, and any manual mailbox verification remains single-recipient, content-free, and temporary.
- AC13: A public-safe aggregate report compares before/after visible length, section count, external-news inclusion, confidence-label count, control repetition, sensitive suppressions, and delivery-count anomalies.
- AC14: Documentation explains the private-ops evidence boundary: mailbox-derived audits stay temporary, aggregate-only results can be recorded, and real identities or message content never enter Git.

# Definition of Ready (DoR)
- [x] Problem statement is explicit and user impact is clear.
- [x] Scope boundaries (in/out) are explicit.
- [x] Acceptance criteria are testable.
- [x] Dependencies and known risks are listed.

# Companion docs
- Product brief(s): `prod_004_day_captain_strict_decision_brief`
- Architecture decision(s): (none yet)

# References
- src/day_captain/app.py
- src/day_captain/services.py
- src/day_captain/digest_metrics.py
- src/day_captain/replay.py
- src/day_captain/scheduler.py
- src/day_captain/models.py
- tests/test_app.py
- tests/test_digest_renderer.py
- tests/test_replay.py
- tests/test_scheduler.py
- docs/digest_rendering_validation.md
- docs/power_automate_scheduler_setup.md

# AI Context
- Summary: Day Captain digest friction hardening
- Keywords: request-chain-scaffold, day captain digest friction hardening, development-ready
- Use when: You need to implement or review the scaffolded workflow for Day Captain digest friction hardening.
- Skip when: The change is unrelated to this scaffolded request chain.

# Backlog
- `item_120_close_authentication_message_suppression_gaps`
- `item_121_make_daily_output_a_strict_command_brief`
- `item_122_polish_outlook_and_text_rendering_ergonomics`
- `item_123_diagnose_sender_delivery_count_anomalies_without_mailbox_content`

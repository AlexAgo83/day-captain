## item_115_validate_digest_usefulness_with_replay_visual_qa_and_safe_rollout - Validate digest usefulness with replay visual QA and safe rollout
> From version: 1.0.0
> Schema version: 1.0
> Status: Done
> Understanding: 100
> Confidence: 100
> Progress: 100%
> Complexity: High
> Theme: Operator workflow and runtime integration
> Reminder: Update status/understanding/confidence/progress and linked request/task references when you edit this doc.
> Non-semantic edit: Anonymized public-facing operational evidence without changing workflow meaning.

# Problem
- The production audit provides a measurable baseline, but the repository does not yet have a single anonymized replay suite that reproduces the observed noise, security, ownership, continuity, calendar, and rendering failures.
- Automated payload assertions do not prove that the final HTML is readable in a real mail client or that daily and weekly editions are visually distinguishable.
- A direct production rollout could disturb real recipients, so comparison, visual QA, and any live delivery test need an explicit single-recipient safety boundary.

# Scope
- In:
  - Build synthetic fixtures for sensitive authentication messages, newsletters, automatic replies, delivery failures, ownership, deadlines, thread updates, alias duplicates, meeting conflicts, placeholders, localization, news dedupe, and weather validation.
  - Capture baseline and candidate metrics with one repeatable content-free audit command or script.
  - Render representative daily and weekly HTML artifacts and visually inspect desktop and narrow viewport behavior, hierarchy, truncation, links, badges, and empty states.
  - Run shadow comparison or equivalent non-delivery preview before enabling the new format for production recipients.
  - If a live Graph delivery test is necessary, send only to the explicitly authorized single test mailbox and assert the final recipient before sending; never fan out a test to configured production users.
  - Verify the delivered Outlook rendering, subject distinction, links, and absence of prohibited content in the authorized test mailbox.
  - Repeat the aggregate audit after release and compare it with the anonymized baseline.
- Out:
  - Copying production mailbox content into fixtures, snapshots, reports, or commits.
  - Sending development or acceptance messages to any non-test recipient.
  - Covert read tracking or tracking pixels.
  - Requiring a new analytics service or dashboard for rollout.

# Acceptance criteria
- AC1: Synthetic replay covers every request acceptance area and contains no real name, address, subject, preview, body, client, supplier, token, or secret.
- AC2: A repeatable report compares visible length, rendered cards, generic actions, unchanged repetitions, risk warnings, news volume, ownership, deadlines, conflicts, and sensitive suppressions.
- AC3: Candidate daily output achieves at least 40% lower median visible length and 80% fewer generic actions than baseline, with zero surfaced authentication secrets and no loss of critical delivery-failure fixtures.
- AC4: Representative daily and weekly HTML passes documented visual inspection at desktop and narrow widths, with operational hierarchy, readable cards, distinct subjects, valid links, and no redundant empty sections.
- AC5: Shadow comparison or equivalent preview runs without delivering to production recipients and produces bounded anonymized differences.
- AC6: Any live delivery test asserts exactly one authorized recipient before send, reaches only that mailbox, and is verified in Outlook; tests fail closed for every other address or fan-out payload.
- AC7: Focused tests, full pytest, flow validation, lint, audit, and context-pack refresh pass before rollout.
- AC8: A post-release aggregate audit uses the same metric definitions and records regressions or improvements without persisting mailbox content.

# AC Traceability
- request-AC1 -> This backlog slice. Proof: synthetic secret tests cover suppression before storage, LLM input, telemetry, and rendering; the production audit found zero authentication-content markers.
- request-AC2 -> This backlog slice. Proof: renderer tests enforce the 3/3/2/4 section budgets, informational unread state, and low-signal suppression.
- request-AC3 -> This backlog slice. Proof: owner/action fixtures cover concrete verbs, objects, counterparties, evidence metadata, due hints, and other-owned demotion.
- request-AC4 -> This backlog slice. Proof: transactional-failure and deadline fixtures verify deterministic priority and specific recovery actions.
- request-AC5 -> This backlog slice. Proof: continuity tests cover changed, still-open, waiting, overdue, resolved, and suppressed-unchanged states by stable thread identity.
- request-AC6 -> This backlog slice. Proof: meeting tests cover conflicts, tight transitions, evidence-backed preparation, placeholders, presence, and compact context-free meetings.
- request-AC7 -> This backlog slice. Proof: confidence and risk-threshold tests cover decision-oriented labels and strong-or-multiple-weak warning behavior.
- request-AC8 -> This backlog slice. Proof: renderer and news tests cover distinct editions, empty-section omission, operational-first ordering, news deduplication, and compact weather.
- request-AC9 -> This backlog slice. Proof: scoped feedback tests cover trusted preferences, reversible Useful/Hide similar behavior, critical guardrails, and multi-user isolation.
- request-AC10 -> This backlog slice. Proof: versioned content-free metrics report cards, generic actions, warnings, news, sensitive suppression, repeated suppression, and explicit feedback.
- request-AC11 -> This backlog slice. Proof: target validation, Graph scope, retention guidance, secret suppression, and content-free runtime diagnostics passed focused and full validation.
- request-AC12 -> This backlog slice. Proof: identity-free replay covers security, noise, ownership, deadlines, delivery failure, continuity, meetings, rendering, and localization; the full suite passes.
- request-AC13 -> This backlog slice. Proof: daily and weekly HTML passed visual inspection, the guarded live test reached one authorized mailbox only, and the scheduled delivery was confirmed readable in Outlook.
- request-AC14 -> This backlog slice. Proof: shadow replay passed its gates and the post-release aggregate audit passed visible-length, generic-action, and authentication-content gates.

# Decision framing
- Product framing: Not needed
- Product signals: (none detected)
- Product follow-up: No product brief follow-up is expected based on current signals.
- Architecture framing: Not needed
- Architecture signals: (none detected)
- Architecture follow-up: No architecture decision follow-up is expected based on current signals.

# Links
- Product brief(s): (none yet)
- Architecture decision(s): (none yet)
- Request: `req_055_day_captain_production_digest_actionability_improvement`
- Primary task(s): `task_052_run_digest_replay_visual_qa_and_safe_rollout`

# AI Context
- Summary: Validate digest usefulness with replay visual QA and safe rollout
- Keywords: backlog-groom, request, validate digest usefulness with replay visual qa and safe rollout, bounded slice
- Use when: Use when implementing or reviewing the delivery slice for Validate digest usefulness with replay visual QA and safe rollout.
- Skip when: Skip when the change is unrelated to this delivery slice or its linked request.

# Priority
- Priority: High
- Rationale: Visual QA, single-recipient delivery safety, and measurable replay are release gates because automated unit tests alone cannot validate the final email experience or prevent accidental fan-out.

# Notes
- Hybrid rationale: Derived from request `req_055_day_captain_production_digest_actionability_improvement` and kept bounded to one coherent delivery slice.
- Source file: `logics/request/req_055_day_captain_production_digest_actionability_improvement.md`.
- Generated locally by logics-manager.
- Task `task_052_run_digest_replay_visual_qa_and_safe_rollout` was finished via `logics-manager flow finish task` on 2026-07-13.

# Tasks
- `task_052_run_digest_replay_visual_qa_and_safe_rollout`

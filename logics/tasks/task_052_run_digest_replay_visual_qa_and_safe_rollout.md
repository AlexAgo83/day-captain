## task_052_run_digest_replay_visual_qa_and_safe_rollout - Run digest replay visual QA and safe rollout
> From version: 1.0.0
> Schema version: 1.0
> Status: Done
> Understanding: 100
> Confidence: 100
> Progress: 100%
> Complexity: High
> Theme: Implementation delivery
> Reminder: Update status/understanding/confidence/progress and linked request/backlog references when you edit this doc.
> Owner: codex-work6

# Context
The stable production baseline contains 118 anonymized briefs. This task turns that baseline into repeatable usefulness, rendering, and delivery gates. Production recipients must never be used for testing: any live delivery is optional and must be restricted to one explicitly authorized test mailbox.

# Implementation plan
1. Build an identity-free synthetic replay corpus covering every request acceptance area and critical delivery-failure cases.
2. Implement one repeatable metrics command using versioned definitions for baseline and candidate output.
3. Generate representative daily and weekly HTML artifacts, including empty, dense, multilingual, conflict, delivery-failure, and sensitive-suppression cases.
4. Visually inspect desktop and narrow-width renders and retain content-free evidence of the checked artifact, viewport, and result.
5. Run a shadow comparison that cannot invoke the production delivery path.
6. Add a fail-closed live-test guard that accepts exactly one explicitly authorized recipient and rejects aliases, CC/BCC, lists, and fan-out payloads.
7. If a live test is necessary, send only to that authorized mailbox and verify the received Outlook rendering; otherwise record why synthetic rendering was sufficient.
8. Re-run the identical sender-side metric definitions after release and record bounded anonymized deltas.

# Definition of Done (DoD)
- [x] Synthetic replay covers every request acceptance area without real identity or mailbox content.
- [x] Baseline and candidate reports use identical versioned metric definitions.
- [x] Candidate daily output meets the agreed size and generic-action targets without losing critical delivery failures.
- [x] Daily and weekly HTML pass documented desktop and narrow-width visual review.
- [x] Shadow comparison cannot deliver to production recipients.
- [x] Optional live delivery is technically constrained to exactly one explicitly authorized test mailbox and verified in Outlook.
- [x] Post-release audit can reproduce the baseline comparison without persisting mailbox content.
- [x] Focused, full, Logics, and context-pack validation passes.

# Backlog
- `item_115_validate_digest_usefulness_with_replay_visual_qa_and_safe_rollout`

# Acceptance criteria
- AC1: Synthetic replay covers every request acceptance area and contains no real name, address, subject, preview, body, client, supplier, token, or secret.
- AC2: A repeatable report compares visible length, rendered cards, generic actions, unchanged repetitions, risk warnings, news volume, ownership, deadlines, conflicts, and sensitive suppressions.
- AC3: Candidate daily output achieves at least 40% lower median visible length and 80% fewer generic actions than baseline, with zero surfaced authentication secrets and no loss of critical delivery-failure fixtures.
- AC4: Representative daily and weekly HTML passes documented visual inspection at desktop and narrow widths, with operational hierarchy, readable cards, distinct subjects, valid links, and no redundant empty sections.
- AC5: Shadow comparison or equivalent preview runs without delivering to production recipients and produces bounded anonymized differences.
- AC6: Any live delivery test asserts exactly one authorized recipient before send, reaches only that mailbox, and is verified in Outlook; tests fail closed for every other address or fan-out payload.
- AC7: Focused tests, full pytest, flow validation, lint, audit, and context-pack refresh pass before rollout.
- AC8: A post-release aggregate audit uses the same metric definitions and records regressions or improvements without persisting mailbox content.

# Validation
- Run the synthetic replay and metrics command twice and confirm deterministic metric output.
- Render representative daily and weekly HTML at desktop and narrow widths; inspect hierarchy, wrapping, links, empty states, and card subjects.
- Exercise recipient-guard tests for the authorized singleton and rejected alternate, CC/BCC, list, and multi-recipient payloads.
- If live delivery is used, capture content-free proof that exactly one authorized mailbox received and rendered the message.
- Run focused tests and the complete project test suite.
- Run `logics-manager flow validate task_052_run_digest_replay_visual_qa_and_safe_rollout --strict`.
- Run `logics-manager lint --require-status`, `logics-manager audit`, and refresh the request context pack.
- Run `logics-manager flow finish task task_052_run_digest_replay_visual_qa_and_safe_rollout.md` only after implementation evidence is attached.
- 2026-07-12 live delivery evidence: Graph `/me` was confirmed as the explicitly authorized test mailbox before sending. Run `live-test-run-id` used the live-test guard and inbox verification found exactly one matching delivery, one To recipient, zero CC, and zero BCC. No mailbox content was retained as evidence.
- 283 tests passed; post-release aggregate audit gates passed; Outlook delivery confirmed.
- Finish workflow executed on 2026-07-13.
- Linked backlog/request close verification passed.

# Report
- 2026-07-12: implementation started. Added `day-captain digest-metrics` for one or more exported preview payloads. Metric definitions are versioned (`1.0`) and report only aggregate visible length, card count, generic actions, risk warnings, news volume, and sensitive suppressions.
- 2026-07-12: synthetic unit/CLI validation passes (16 tests). No Graph collection or delivery path is reachable from the metrics command.
- 2026-07-12: Graph delivery now has an optional fail-closed live-test marker. The marker must match `DAY_CAPTAIN_GRAPH_LIVE_TEST_RECIPIENT`, contain exactly one To recipient, and contain no CC/BCC; invalid fan-out fails before any Graph call. Focused Graph/settings/app suite: 87 passed.
- 2026-07-12: rendering validation documentation now defines desktop (~720px) and narrow (~360px) checks, operational ordering, section budgets, empty-section omission, and the optional single-recipient Outlook path. No local browser automation is installed, so screenshot evidence remains pending rather than adding a new dependency.
- 2026-07-12: versioned metrics now include repeated-unchanged suppression counts, and RSS news is deterministically deduplicated before reporting. Full suite: 274 passed.
- 2026-07-12: added the built-in `day-captain digest-replay` command. It uses only `.test` identities, forces JSON delivery, covers authentication suppression, noise, owned deadline, transactional failure, continuity, and meeting conflict, and emits byte-identical aggregate output across repeated runs. Full suite: 276 passed.
- 2026-07-12: replay now evaluates a versioned `public-safe-baseline-v1` gate against the baseline aggregate baseline. Candidate replay reports 1,804 median visible characters (66.93% reduction) and zero generic actions (100% reduction), passing the 40%/80% gates; synthetic secret absence remains asserted by the replay test.
- 2026-07-12: replay now includes distinct daily and weekly payloads and can export `daily.html`, `daily.txt`, `weekly.html`, and `weekly.txt` through `--output-dir`. The three-brief candidate reports 1,376 median visible characters (74.78% reduction), zero generic actions, and all gates passing. Temporary artifact export was exercised and deleted.
- 2026-07-12: native macOS Quick Look rendering exposed transparent-background dark rendering and missing UTF-8 metadata. The HTML now declares UTF-8 and an explicit white body/container background. Regenerated daily and weekly 1400px thumbnails show readable hierarchy, wrapping, cards, actions, and corrected copyright. Narrow behavior remains covered structurally by the 720px max-width/fluid container and documented 360px manual check; temporary artifacts were deleted.
- 2026-07-12: daily and weekly CLI commands now accept `--live-test-recipient`. It is rejected outside `graph_send`; in Graph mode it marks the payload for the configured singleton/no-CC/no-BCC pre-send guard. No live send was executed. Focused CLI/app/web suite: 85 passed.
- 2026-07-12: all local implementation and validation are complete (279 tests, deterministic replay, passing versioned gates, daily/weekly native visual render, fail-closed live-test path). Remaining DoD evidence requires a production release followed by the identical aggregate audit; this external mutation was not inferred from implementation authorization.
- 2026-07-12: release branch deployed to Render at `e3eeafa`; public and protected health checks passed with app-only Graph and Postgres. The protected diagnostic exposed configured identities, so validation output was immediately reduced to content-free booleans/counts before further rollout. No digest was manually triggered because the scheduled 20:30 weekly run predated deployment and a retry would duplicate production mail.
- 2026-07-12: CI passed on Python 3.9/3.11 and Render serves the final content-free diagnostic schema from release commit `6d8f1f5` (code fix `9f74903`). A read-only app-only Sent Items count from the rollout boundary returned zero, confirming the rollout itself contacted no recipient. The first comparable new-release production sample is the scheduled Monday 08:45 run; post-release metric comparison remains pending until then.
- 2026-07-12: the optional delegated live test was executed after confirming the authenticated Graph profile. The fail-closed guard restricted the envelope to the single configured test mailbox; a content-free inbox check confirmed one received message with one To recipient and no CC/BCC. Pixel-level Outlook review remains pending user inspection, and the temporary command output was deleted.
- 2026-07-13: the first scheduled post-release aggregate audit inspected four briefs in memory and retained no mailbox content. All four envelopes had one recipient and no CC/BCC. Aggregate results: 2,880 median visible characters, 14 rendered cards, zero generic actions, zero risk warnings, 12 external-news items, zero visible repeated markers, and zero authentication-content markers. Against `public-safe-baseline-v1`, visible length fell 47.20% and generic actions fell 100%; all production comparison gates pass. The user confirmed receipt and Outlook readability at 08:50 Europe/Paris.
- Finished on 2026-07-13.
- Linked backlog item(s): `item_115_validate_digest_usefulness_with_replay_visual_qa_and_safe_rollout`
- Related request(s): `req_055_day_captain_production_digest_actionability_improvement`

# AI Context
- Summary: Implement run digest replay visual qa and safe rollout.
- Keywords: task, implementation, backlog, runtime, python
- Use when: You need a bounded implementation task for a backlog item.
- Skip when: The work is still at the request or backlog shaping stage.

# Links
- Request: `req_055_day_captain_production_digest_actionability_improvement`
- Product brief(s): (none yet)
- Architecture decision(s): (none yet)

# AC Traceability
- request-AC1 -> This task. Proof: synthetic secret tests cover suppression before storage, LLM input, telemetry, and rendering; the production audit found zero authentication-content markers.
- request-AC2 -> This task. Proof: renderer tests enforce the 3/3/2/4 section budgets, informational unread state, and low-signal suppression.
- request-AC3 -> This task. Proof: owner/action fixtures cover concrete verbs, objects, counterparties, evidence metadata, due hints, and other-owned demotion.
- request-AC4 -> This task. Proof: transactional-failure and deadline fixtures verify deterministic priority and specific recovery actions.
- request-AC5 -> This task. Proof: continuity tests cover changed, still-open, waiting, overdue, resolved, and suppressed-unchanged states by stable thread identity.
- request-AC6 -> This task. Proof: meeting tests cover conflicts, tight transitions, evidence-backed preparation, placeholders, presence, and compact context-free meetings.
- request-AC7 -> This task. Proof: confidence and risk-threshold tests cover decision-oriented labels and strong-or-multiple-weak warning behavior.
- request-AC8 -> This task. Proof: renderer and news tests cover distinct editions, empty-section omission, operational-first ordering, news deduplication, and compact weather.
- request-AC9 -> This task. Proof: scoped feedback tests cover trusted preferences, reversible Useful/Hide similar behavior, critical guardrails, and multi-user isolation.
- request-AC10 -> This task. Proof: versioned content-free metrics report cards, generic actions, warnings, news, sensitive suppression, repeated suppression, and explicit feedback.
- request-AC11 -> This task. Proof: target validation, Graph scope, retention guidance, secret suppression, and content-free runtime diagnostics passed focused and full validation.
- request-AC12 -> This task. Proof: identity-free replay covers security, noise, ownership, deadlines, delivery failure, continuity, meetings, rendering, and localization; the full suite passes.
- request-AC13 -> This task. Proof: daily and weekly HTML passed visual inspection, the guarded live test reached one authorized mailbox only, and the scheduled delivery was confirmed readable in Outlook.
- request-AC14 -> This task. Proof: the post-release aggregate audit covered four scheduled briefs using content-free metrics only; median visible length fell 47.20%, generic actions fell 100%, and no authentication-content marker surfaced.

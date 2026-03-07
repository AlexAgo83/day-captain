## spec_000_day_captain_v1_digest_contract - Day Captain V1 digest contract and service architecture
> From version: 0.1.0
> Understanding: 97%
> Confidence: 94%

# Overview
Day Captain V1 is a single-user Microsoft 365 daily briefing service. It reads Outlook mail and calendar data through Microsoft Graph, scores only the most relevant signals, renders a concise morning digest, persists the run snapshot in a lightweight relational store, and supports same-day recall without replaying the entire mailbox history.

This spec operationalizes:
- request `req_000_day_captain_daily_assistant_for_microsoft_365`
- backlog item `item_000_day_captain_daily_assistant_for_microsoft_365`

# Goals
- Deliver one reliable morning digest per day for a heavy Microsoft 365 user.
- Reduce inbox triage time by surfacing only critical topics, actions, watch items, and upcoming meetings.
- Keep V1 cheap by using deterministic filtering/scoring and limiting LLM usage to digest phrasing over shortlisted items.
- Preserve likely critical business signals even when personalization rules would otherwise demote them.
- Support same-day recall from persisted state instead of reprocessing all message history.

# Non-goals
- Multi-user tenancy in V1.
- App-only Microsoft Graph auth in V1.
- Real-time assistant behavior across the full mailbox.
- Complex UI beyond structured JSON output and email delivery.
- Advanced analytics, admin tooling, or enterprise governance features.

# Users & use cases
- A single heavy Microsoft 365 user runs a scheduled morning digest before the workday starts.
- The same user triggers a later recall to recover the morning summary or check unresolved watch items.
- The user marks digest items as useful or not useful so sender/topic preferences can be adjusted over time.

# Scope
- In:
  - delegated Microsoft Graph auth for one user
  - morning collection of emails and meetings for a fixed V1 window
  - deterministic noise filtering, scoring, personalization, and critical-topic guardrails
  - digest rendering to a normalized JSON contract and email-friendly output
  - local `SQLite` persistence and a hosted Postgres-compatible relational schema for normalized entities, digest runs, digest items, and feedback
  - same-day recall based on the latest completed digest snapshot
  - Render-hosted Python runtime with GitHub Actions scheduling for the first deployment path
- Out:
  - Teams chat ingestion
  - mailbox mutation beyond optional sending of the digest
  - cross-user preference learning
  - near-real-time event processing

# Requirements
- REQ1. Auth model: V1 uses delegated Microsoft Graph auth for a single user. Minimum Graph scopes are `Mail.Read` and `Calendars.Read`; `Mail.Send` is optional when the service sends the digest through Outlook.
- REQ2. Collection window: the morning run reads emails from the previous successful digest timestamp up to the current run start; if no previous run exists, it falls back to the last 24 hours. Meeting collection covers the current time through the end of the same day.
- REQ3. Digest contract: every completed run produces a normalized digest with sections `critical_topics`, `actions_to_take`, `watch_items`, and `upcoming_meetings`, plus metadata (`run_id`, `window_start`, `window_end`, `generated_at`, `delivery_mode`).
- REQ4. Filtering: newsletters, automated notifications, and low-signal CC-only traffic are excluded when confidence is sufficient. Filter decisions must remain inspectable in stored item metadata.
- REQ5. Scoring: item ranking combines deterministic global signals (sender importance, direct recipient vs CC, recency, reply/action cues, meeting proximity, thread activity) with explicit user-specific boosts/penalties for senders, domains, and keywords.
- REQ6. Guardrails: potentially critical items must bypass suppression even if personalization would demote them. Guardrail examples include manager/executive senders, explicit action requests, deadlines, incident keywords, or meetings within 24 hours that require preparation.
- REQ7. Persistence: local development uses `SQLite`, while hosted deployment must target a Postgres-compatible relational schema for normalized messages, normalized meetings, digest runs, digest items, and user feedback. Writes must be idempotent for repeated runs over the same window.
- REQ8. Recall and feedback: same-day recall reads the latest completed digest snapshot and may enrich it with stored item state, but it does not re-fetch full mailbox history. Feedback updates only explicit preference weights in V1.
- REQ9. Orchestration boundary: Render owns the hosted runtime, GitHub Actions owns the scheduled trigger, and Python owns Graph calls, scoring, rendering, persistence, and response payload generation.

# Architecture
- Trigger boundary:
  - GitHub Actions scheduled workflow invokes a protected Python HTTP entrypoint for the morning run on Render.
  - Optional authenticated webhook or CLI command invokes same-day recall.
- Python service modules:
  - `auth`: delegated Graph token acquisition/refresh
  - `collectors`: mail and calendar retrieval
  - `storage`: relational schema and repositories, implemented first in `SQLite` and then hosted on Postgres
  - `scoring`: deterministic filters, ranking, personalization, and guardrails
  - `digest`: normalized digest model and renderer
  - `recall`: read-only lookup over stored digest snapshots
  - `feedback`: explicit preference updates
- Delivery modes:
  - `json`: return a structured payload to the caller/webhook consumer
  - `graph_send`: optionally send the rendered digest through Microsoft Graph mail APIs

# Data model
- `messages`
  - `graph_message_id`, `thread_id`, `internet_message_id`, `subject`, `from_address`, `to_addresses`, `cc_addresses`, `received_at`, `is_unread`, `has_attachments`, `categories_json`, `body_preview`, `raw_payload_json`, `first_seen_at`, `last_seen_at`
- `meetings`
  - `graph_event_id`, `subject`, `start_at`, `end_at`, `organizer_address`, `attendees_json`, `is_online_meeting`, `join_url`, `location`, `body_preview`, `raw_payload_json`
- `digest_runs`
  - `run_id`, `run_type`, `window_start`, `window_end`, `status`, `generated_at`, `delivery_mode`, `summary_json`
- `digest_items`
  - `run_id`, `item_type`, `source_kind`, `source_id`, `score`, `reason_codes_json`, `guardrail_applied`, `section_name`, `rendered_text`
- `feedback`
  - `feedback_id`, `run_id`, `source_kind`, `source_id`, `signal_type`, `signal_value`, `recorded_at`
- `preferences`
  - `preference_key`, `preference_type`, `weight`, `source`, `updated_at`

# Interfaces
- Morning run entrypoint:
  - input: `run_morning_digest(now, delivery_mode, force=false)`
  - output: normalized digest JSON plus persisted `run_id`
- Recall entrypoint:
  - input: `recall_digest(run_id=None, day=today)`
  - output: latest stored digest snapshot for the requested day, optionally with unresolved watch items
- Feedback entrypoint:
  - input: `record_feedback(run_id, source_kind, source_id, signal_type, signal_value)`
  - output: updated preference state confirmation
- Config contract:
  - Graph tenant/client settings
  - delegated auth mode
  - optional Graph send-mail toggle
  - local `SQLITE` file path or hosted Postgres connection string
  - delivery mode (`json` or `graph_send`)

# Acceptance criteria
- AC1: V1 auth is explicitly defined as delegated Microsoft Graph auth with minimum required scopes and optional digest send capability.
- AC2: The morning run fetches emails and meetings for the fixed V1 window, normalizes them, and persists run metadata in a relational store compatible with local `SQLite` and hosted Postgres.
- AC3: The digest output contract is fixed and contains `critical_topics`, `actions_to_take`, `watch_items`, and `upcoming_meetings`.
- AC4: Noise filtering explicitly handles newsletters, automated notifications, and low-signal CC traffic, while keeping decision reasons inspectable.
- AC5: Prioritization combines deterministic global signals with explicit user preference weights and a non-bypassable critical-signal guardrail path.
- AC6: Same-day recall reuses stored digest snapshots without replaying the full mailbox history.
- AC7: The Python service boundary vs Render runtime and GitHub Actions scheduler boundary is explicit enough to implement without guessing responsibilities.
- AC8: The first deployment path remains compatible with Render, GitHub Actions, hosted Postgres, and Outlook/Graph-based delivery.

# Validation / test plan
- Unit tests:
  - Graph payload normalization for mail and calendar responses
  - noise filtering, scoring, and guardrail rules
  - digest renderer and recall reconstruction
- Integration tests:
  - idempotent relational writes across repeated runs
  - morning run over mocked Graph responses
  - webhook payload contract for morning digest and recall
- Manual checks:
  - execute one morning run and inspect stored digest JSON
  - trigger one recall on the same day and confirm no full-history re-fetch
  - verify that one critical message survives an otherwise suppressive preference rule
- Commands:
  - `python3 -m pytest`
  - `python3 logics/skills/logics-doc-linter/scripts/logics_lint.py --require-status`
  - `python3 logics/skills/logics-flow-manager/scripts/workflow_audit.py --group-by-doc`

# Open questions
- Should V1 delivery send the digest directly through Graph mail APIs, or return structured JSON to a caller/webhook consumer for the final delivery step?
- Which initial sender/topic preference seeds should be configured before the first feedback loop exists?

# Changelog (`1.9.0 -> 1.9.1`)

## Major Highlights

- Tightened digest relevance so marketing mail, weak meeting-mail matches, and low-signal direct-recipient mail no longer surface like real operational follow-up.
- Preserved critical automated suspension and billing alerts while collapsing duplicate alias copies into a single grouped operational item.
- Removed placeholder calendar slots from the upcoming-meetings briefing while keeping legitimate private work blocks visible.

## Version 1.9.1

### Delivered

- Expanded promotional and newsletter detection with stronger sender hints, browser-view markers, and event-marketing cues.
- Replaced overly generic critical-topic keywords such as bare `security` and `production` with more operationally specific incident and outage signals.
- Preserved automated transactional suspension and billing alerts from `no-reply` style senders so they remain visible in `critical_topics`.
- Added conservative alias-level alert grouping using normalized sender, subject, preview, and short time proximity, with grouped-alias context carried into the digest payload.
- Tightened meeting-related mail context so weak single-token overlaps no longer leak unrelated mail content into meeting briefings.
- Ignored placeholder calendar body previews for confidence scoring and filtered self-organized placeholder meetings out of the upcoming-meetings section.
- Tightened `Actions to take` / `Actions à mener` routing so direct-recipient presence alone no longer promotes informational mail without an explicit follow-up cue.
- Added regression coverage for marketing false positives, automated transactional alerts, alias dedupe, placeholder meetings, and stronger action gating.
- Added a canonical repository `VERSION` file and aligned package metadata for scripted release publication.

### Validation

- `PYTHONPATH=src python3 -m unittest tests.test_scoring tests.test_digest_renderer tests.test_llm`
- `PYTHONPATH=src python3 -m unittest discover -s tests`
- `python3 logics/skills/logics-doc-linter/scripts/logics_lint.py --require-status`
- `python3 logics/skills/logics-flow-manager/scripts/workflow_audit.py --group-by-doc --refs req_051_day_captain_digest_alias_dedupe_placeholder_meeting_filtering_and_action_signal_tightening item_097_day_captain_alias_level_operational_alert_dedupe item_098_day_captain_placeholder_meeting_filtering_and_compact_rendering item_099_day_captain_stronger_action_gating_for_informational_mail task_047_day_captain_remaining_digest_trust_fixes_orchestration`
- `python3 logics/skills/logics-version-release-manager/scripts/publish_version_release.py --dry-run`

# Changelog (`1.10.0 -> 1.11.0`)

## Major Highlights

- Improved daily digest actionability from real user feedback: mail from moved folders is now considered, thread context is read, and attachments are summarized safely by type and size.
- Added a dedicated `Actions équipe` section for team-owned follow-ups, so copied threads can surface as potential tickets without mixing them into personal actions.
- Tightened the opening `En bref` format with labelled lines and made team-action wording name the concrete action, not only the owner.

## Version 1.11.0

### Delivered

- Expanded Graph mail collection beyond Inbox, added thread enrichment by conversation, and included bounded attachment metadata without downloading file contents.
- Added owner-aware team actions, persisted/rendered the new section, and included it in metrics, memory, web acknowledgements, and LLM prompts.
- Reduced digest noise from Day Captain replies and Read AI pre-read messages.
- Fixed meeting update wording and removed the meeting render cap.
- Added deterministic fallback formatting for `Priorité`, `À surveiller`, and `Réunion la plus proche`.

### Validation

- `python3 -m pytest`

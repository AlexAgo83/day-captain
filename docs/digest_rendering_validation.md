# Digest Rendering Validation

Use this workflow when you want to review the current digest presentation before or alongside a real Outlook send.

## Why

- the renderer now has a denser Outlook-oriented layout, but local JSON output alone is still awkward to review
- local HTML and text export lets you inspect the current contract before spending time on a live mailbox validation
- the final closure gate for `task_026` is still a real Outlook rendering check, not only a local preview

## Local preview workflow

1. Load the local environment and run a digest with preview export enabled.
2. Review the generated `.html` file in a browser and the `.txt` file in a plain-text editor.
3. Confirm the top summary remains complete and readable, sections feel balanced, meetings are compact, and empty states stay light.

Example:

```bash
set -a
source .env
set +a
PYTHONPATH=src python3 -m day_captain morning-digest \
  --preview \
  --force \
  --output-html tmp/day-captain-preview.html \
  --output-text tmp/day-captain-preview.txt
```

Important:
- `--preview` is the no-send lever for local rendering
- `--output-html` and `--output-text` only control file export and do not suppress delivery by themselves

You can use the same `--output-html` and `--output-text` flags on:
- `weekly-digest`
- `recall-digest`
- `email-command-recall`

## Development stub preview

In a minimal local development environment, Day Captain can still render a preview even when Microsoft Graph is not configured yet.

That path uses the app's built-in stub auth and empty collectors, which means:
- it is valid for layout and copy review
- it is not a substitute for real mailbox-content validation
- it is the fastest way to sanity-check digest presentation before wiring live auth

On Sunday, March 8, 2026, this repository was validated locally with:

```bash
python3 -m day_captain validate-config
python3 -m day_captain morning-digest --preview --force \
  --output-html tmp/day-captain-preview.html \
  --output-text tmp/day-captain-preview.txt
```

That run produced a stub preview with:
- the compact header enabled
- the `In brief` summary block enabled
- light empty states enabled
- the weekend Monday meeting fallback visible in both text and HTML output

## What to check locally

- header:
  - the mail starts with a short as-of line plus a single window line
  - the header does not read like a verbose generated report
- executive summary:
  - `In brief` / `En bref` remains faithful to the generated recap and is not forcibly truncated by the app
  - it does not restate every downstream section
- sections:
  - `Critical topics`, `Actions to take`, `Watch items`, and `Upcoming meetings` have a steady visual rhythm
  - item cards remain readable without large vertical gaps
  - flagged items remain more visible than ordinary messages without overwhelming the full digest
  - surfaced mail items clearly show whether the latest message is unread or already read
  - surfaced mail items show a low-prominence received timestamp without cluttering the card
- footer:
  - if quick actions are present, the `mailto:` links point to the intended Day Captain mailbox
  - the command subjects are prefilled as `recall`, `recall-today`, or `recall-week`
  - the draft body also starts with the same command for client-side robustness
  - the helper copy makes it clear that clicking opens a draft rather than auto-sending a command
- source-open controls:
  - Outlook web links remain the reliable baseline
  - if a native Outlook desktop protocol link is explicitly available in the source metadata, the renderer may prefer it instead of the web link
  - if no native desktop link is available, the renderer falls back to the standard web link
- meetings:
  - each meeting line emphasizes title, time, organizer, and location quickly
  - the section does not expand into a tall report for a single meeting
- empty states:
  - empty sections stay explicit
  - the copy feels lighter than a status report

## Real Outlook validation

The local preview is only a preflight step. Before closing the readability slice, validate one real Outlook delivery:

1. Send or recall a digest into the real target mailbox.
2. Open it in Outlook using the actual mailbox view used day to day.
3. Confirm:
   - the hero/header block still looks compact
   - the executive summary remains readable even when it is longer than previous bounded versions
   - section spacing survives Outlook rendering
   - meeting rows stay compact
   - flagged items still stand out appropriately
   - unread/read mail status is easy to spot at a glance
   - received timestamps stay visible but secondary
   - source-open controls use the expected desktop/web fallback behavior on the actual Outlook client
   - empty states remain light and readable

If Outlook introduces a regression that the local preview did not reveal, treat Outlook as the source of truth and adjust the renderer accordingly.

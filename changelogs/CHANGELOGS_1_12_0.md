# Changelog (`1.11.0 -> 1.12.0`)

## Major Highlights

- Hardened public repository hygiene with a publication checklist, an exposure scanner, and sanitized workflow documentation.
- Made daily digests more actionable by suppressing authentication noise, tightening daily brief length, and reducing generic recommendation clutter.
- Added a content-free delivery audit helper to diagnose duplicate or missing sends without storing mailbox-derived subjects, bodies, or addresses.

## Version 1.12.0

### Delivered

- Added `scripts/check_public_exposure.sh` and documented the publication checklist for GitHub-facing material.
- Added a ready-to-dev Logics corpus for digest friction hardening and closed the implementation task with validation evidence.
- Expanded suppression for one-time codes, login links, authentication prompts, and related French/English authentication wording.
- Limited daily meeting output, omitted non-operational external news from daily digests, and reduced redundant confidence labels.
- Improved Outlook and plain-text rendering spacing for coverage labels, badges, quick actions, and meeting controls.
- Added `day-captain delivery-audit` for sanitized delivery-count diagnostics.

### Validation

- `python3 -m pytest -q`
- `python3 -m day_captain digest-replay`
- `scripts/check_public_exposure.sh`
- `logics-manager flow validate req_057_day_captain_digest_friction_hardening`
- `logics-manager lint --require-status`
- `logics-manager audit --group-by-doc`

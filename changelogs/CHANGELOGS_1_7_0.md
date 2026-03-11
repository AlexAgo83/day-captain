# Changelog (`1.5.1 -> 1.7.0`)

## Major Highlights

- Improved digest editorial quality with more coherent summaries, privacy-safer phrasing, nuanced rain-aware weather copy, meeting recurrence indicators, and clearer footer/quick-action microcopy.
- Added bounded promotional-mail handling so commercial emails no longer surface as assistant-endorsed actions or get repeated in `En bref`.
- Aligned repository planning artifacts and version metadata for the promotional-mail handling slice under the released `1.7.0` package version.

## Version 1.7.0

### Delivered

- Polished digest summary behavior so surfaced items read more coherently, use older thread context more consistently, and avoid abrupt fragment-style endings.
- Made visible digest wording more privacy-safe and action-oriented without overexposing raw business fragments in rendered copy.
- Extended the daily weather capsule with more nuanced rain wording and added discreet recurrence indicators on supported meeting cards.
- Refined bottom-of-mail product copy with clearer quick-action helper text and the small branded footer line.
- Added a bounded promotional signal in mail scoring using heuristic-first detection, including demotion of commercial messages out of `Actions à mener` when they are not genuine operational follow-ups.
- Extended the LLM rewrite contract so ambiguous surfaced mail can carry structured promotional classification metadata instead of only rewritten summaries.
- Prevented promotional items from receiving action-forward `À faire` / `Next step` wording by default and rendered them with a low-prominence promotional badge instead.
- Excluded promotional-only items from both deterministic and LLM-driven `En bref` synthesis so top summaries no longer amplify those false positives.
- Added regression coverage for promotional scoring, LLM promotional demotion, overview exclusion, and renderer behavior.
- Closed the related Logics request/backlog/task artifacts and aligned the project version metadata to `1.7.0`.

### Validation

- `python3 -m unittest discover -s tests`
- `python3 logics/skills/logics-doc-linter/scripts/logics_lint.py --require-status`
- `python3 logics/skills/logics-flow-manager/scripts/workflow_audit.py --group-by-doc`


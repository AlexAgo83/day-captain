# Contributing

## Scope

Day Captain is developed with a Logics-first workflow. Code, docs, and delivery
changes should stay traceable to the request, backlog, and task documents in
[`logics/`](./logics/).

## Development setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

Start from [`.env.example`](./.env.example) and keep local secrets in `.env`.
Do not commit secrets, local auth caches, or local databases.

## Before opening a change

1. Check whether the work should update or create a Logics request, backlog
   item, or task.
2. Keep changes scoped to the current task instead of mixing unrelated cleanup.
3. Update docs when behavior, commands, or operator workflows change.

## Validation

Run the full validation set before submitting a change:

```bash
python3 -m unittest discover -s tests
python3 logics/skills/logics-doc-linter/scripts/logics_lint.py --require-status
python3 logics/skills/logics-flow-manager/scripts/workflow_audit.py --group-by-doc
```

If you changed only a narrow area, you can run targeted tests in addition to,
not instead of, the full suite.

## Coding notes

- Prefer small, reviewable commits.
- Preserve the existing deterministic fallback behavior around scoring, LLM
  wording, and delivery paths.
- Keep hosted changes explicit about auth mode, target user scope, and delivery
  semantics.
- When changing digest rendering, verify both local preview output and the
  documented Outlook validation workflow in
  [`docs/digest_rendering_validation.md`](./docs/digest_rendering_validation.md).

## Pull requests

A good pull request should include:

- a short problem statement
- the main implementation decision or tradeoff
- the validation commands you ran
- any follow-up work or remaining operational validation, if applicable

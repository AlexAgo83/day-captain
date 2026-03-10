# Day Captain Changelogs

Versioned changelog artifacts live in this folder.

Contract:
- filename pattern: `CHANGELOGS_x_y_z.md`
- version source of truth: repository `pyproject.toml`
- generation moment: at delivery closure time, using the real current project version at that moment

Generate a scaffold with:

```bash
python3 scripts/generate_changelog.py --previous-version 1.4.2
```

This keeps changelog filenames aligned with the current package version instead of guessing a release number in advance.

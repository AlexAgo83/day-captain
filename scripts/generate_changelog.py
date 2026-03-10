#!/usr/bin/env python3
"""Generate a versioned changelog scaffold under changelogs/."""

from argparse import ArgumentParser
from pathlib import Path
import sys


REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = REPO_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from day_captain.changelog import changelog_path_for_version
from day_captain.changelog import resolve_project_version
from day_captain.changelog import scaffold_changelog


def main() -> int:
    parser = ArgumentParser(description="Generate a versioned changelog scaffold for Day Captain.")
    parser.add_argument("--repo-root", default=str(REPO_ROOT), help="Repository root. Defaults to the current project root.")
    parser.add_argument("--version", default="", help="Override the version used for the changelog filename.")
    parser.add_argument("--previous-version", default="", help="Optional previous version for the changelog title.")
    parser.add_argument("--force", action="store_true", help="Overwrite the output file if it already exists.")
    args = parser.parse_args()

    repo_root = Path(args.repo_root).resolve()
    pyproject_path = repo_root / "pyproject.toml"
    version = str(args.version or "").strip() or resolve_project_version(pyproject_path)
    output_path = changelog_path_for_version(repo_root, version)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    if output_path.exists() and not args.force:
        raise SystemExit("Refusing to overwrite existing changelog: {0}".format(output_path))
    output_path.write_text(
        scaffold_changelog(version=version, previous_version=str(args.previous_version or "").strip()),
        encoding="utf-8",
    )
    print(output_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

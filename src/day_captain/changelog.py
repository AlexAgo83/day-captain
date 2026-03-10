"""Helpers for Day Captain versioned changelog artifacts."""

from pathlib import Path
import re


_VERSION_PATTERN = re.compile(r'^version\s*=\s*"([^"]+)"\s*$', re.MULTILINE)


def resolve_project_version(pyproject_path: Path) -> str:
    raw = pyproject_path.read_text(encoding="utf-8")
    match = _VERSION_PATTERN.search(raw)
    if not match:
        raise ValueError("Unable to resolve project version from pyproject.toml.")
    return match.group(1).strip()


def changelog_filename_for_version(version: str) -> str:
    normalized = str(version or "").strip()
    if not re.fullmatch(r"\d+\.\d+\.\d+", normalized):
        raise ValueError("Version must use semantic format x.y.z.")
    return "CHANGELOGS_{0}.md".format(normalized.replace(".", "_"))


def changelog_path_for_version(repo_root: Path, version: str) -> Path:
    return repo_root / "changelogs" / changelog_filename_for_version(version)


def scaffold_changelog(version: str, previous_version: str = "") -> str:
    current = str(version or "").strip()
    previous = str(previous_version or "").strip()
    title = (
        "# Changelog (`{0} -> {1}`)".format(previous, current)
        if previous
        else "# Changelog (`{0}`)".format(current)
    )
    return "\n".join(
        (
            title,
            "",
            "## Major Highlights",
            "",
            "- Summarize the main delivery outcomes for this version.",
            "",
            "## Version {0}".format(current),
            "",
            "### Delivered",
            "",
            "- Describe the shipped product and engineering changes.",
            "",
            "### Validation",
            "",
            "- List the validation commands or evidence used before closure.",
            "",
        )
    )

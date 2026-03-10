from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from day_captain.changelog import changelog_filename_for_version
from day_captain.changelog import changelog_path_for_version
from day_captain.changelog import resolve_project_version
from day_captain.changelog import scaffold_changelog


class ChangelogHelpersTest(unittest.TestCase):
    def test_resolves_version_from_pyproject(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            pyproject = Path(tmpdir) / "pyproject.toml"
            pyproject.write_text('[project]\nname = "day-captain"\nversion = "1.4.3"\n', encoding="utf-8")

            self.assertEqual(resolve_project_version(pyproject), "1.4.3")

    def test_builds_versioned_filename_and_path(self) -> None:
        repo_root = Path("/tmp/day-captain")

        self.assertEqual(changelog_filename_for_version("1.4.3"), "CHANGELOGS_1_4_3.md")
        self.assertEqual(
            changelog_path_for_version(repo_root, "1.4.3"),
            repo_root / "changelogs" / "CHANGELOGS_1_4_3.md",
        )

    def test_scaffolds_changelog_with_optional_previous_version(self) -> None:
        rendered = scaffold_changelog("1.4.3", previous_version="1.4.2")

        self.assertIn("# Changelog (`1.4.2 -> 1.4.3`)", rendered)
        self.assertIn("## Version 1.4.3", rendered)
        self.assertIn("### Validation", rendered)

    def test_generate_changelog_script_uses_repo_version_by_default(self) -> None:
        repo_root = Path(__file__).resolve().parents[1]
        script_path = repo_root / "scripts" / "generate_changelog.py"

        with tempfile.TemporaryDirectory() as tmpdir:
            temp_repo = Path(tmpdir)
            (temp_repo / "pyproject.toml").write_text(
                '[project]\nname = "day-captain"\nversion = "2.0.1"\n',
                encoding="utf-8",
            )

            result = subprocess.run(
                [sys.executable, str(script_path), "--repo-root", str(temp_repo), "--previous-version", "2.0.0"],
                check=True,
                capture_output=True,
                text=True,
            )

            output_path = temp_repo / "changelogs" / "CHANGELOGS_2_0_1.md"
            self.assertEqual(Path(result.stdout.strip()).resolve(), output_path.resolve())
            self.assertTrue(output_path.is_file())
            rendered = output_path.read_text(encoding="utf-8")
            self.assertIn("# Changelog (`2.0.0 -> 2.0.1`)", rendered)


if __name__ == "__main__":
    unittest.main()

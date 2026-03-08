from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]


class WeeklySchedulerTemplateTest(unittest.TestCase):
    def test_repository_weekly_template_uses_shared_scheduler_helper(self) -> None:
        content = (ROOT / ".github" / "workflows" / "weekly-digest-scheduler.yml").read_text()

        self.assertIn("from day_captain.scheduler import should_run_sunday_weekly_digest", content)
        self.assertIn("should_run = should_run_sunday_weekly_digest()", content)
        self.assertNotIn("local_now.weekday() == 6 and local_now.hour == 20 and local_now.minute == 30", content)

    def test_docs_weekly_ops_template_uses_shared_scheduler_helper(self) -> None:
        content = (ROOT / "docs" / "day_captain_ops_weekly_digest_scheduler.yml").read_text()

        self.assertIn("from day_captain.scheduler import should_run_sunday_weekly_digest", content)
        self.assertIn("should_run = should_run_sunday_weekly_digest()", content)
        self.assertNotIn("local_now.weekday() == 6 and local_now.hour == 20 and local_now.minute == 30", content)


if __name__ == "__main__":
    unittest.main()

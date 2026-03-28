from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]


class MorningSchedulerTemplateTest(unittest.TestCase):
    def test_repository_morning_template_is_manual_only(self) -> None:
        content = (ROOT / ".github" / "workflows" / "morning-digest-scheduler.yml").read_text()

        self.assertIn("workflow_dispatch:", content)
        self.assertNotIn("\n  schedule:\n", content)
        self.assertNotIn('cron: "45 6 * * 1-5"', content)
        self.assertNotIn('cron: "45 7 * * 1-5"', content)
        self.assertNotIn("should_run_weekday_morning_digest", content)

    def test_docs_morning_ops_template_uses_shared_scheduler_helper(self) -> None:
        content = (ROOT / "docs" / "day_captain_ops_morning_digest_scheduler.yml").read_text()

        self.assertIn("from day_captain.scheduler import should_run_weekday_morning_digest", content)
        self.assertIn("should_run = should_run_weekday_morning_digest()", content)
        self.assertIn('- cron: "45 6 * * 1-5"', content)
        self.assertIn('- cron: "45 7 * * 1-5"', content)


class WeeklySchedulerTemplateTest(unittest.TestCase):
    def test_repository_weekly_template_is_manual_only(self) -> None:
        content = (ROOT / ".github" / "workflows" / "weekly-digest-scheduler.yml").read_text()

        self.assertIn("workflow_dispatch:", content)
        self.assertNotIn("\n  schedule:\n", content)
        self.assertNotIn("should_run_sunday_weekly_digest", content)
        self.assertNotIn("local_now.weekday() == 6 and local_now.hour == 20 and local_now.minute == 30", content)

    def test_docs_weekly_ops_template_uses_shared_scheduler_helper(self) -> None:
        content = (ROOT / "docs" / "day_captain_ops_weekly_digest_scheduler.yml").read_text()

        self.assertIn("from day_captain.scheduler import should_run_sunday_weekly_digest", content)
        self.assertIn("should_run = should_run_sunday_weekly_digest()", content)
        self.assertNotIn("local_now.weekday() == 6 and local_now.hour == 20 and local_now.minute == 30", content)


if __name__ == "__main__":
    unittest.main()

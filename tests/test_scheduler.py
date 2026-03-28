from datetime import datetime
from datetime import timezone
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from day_captain.scheduler import should_run_sunday_weekly_digest
from day_captain.scheduler import should_run_weekday_morning_digest


class SchedulerGateTest(unittest.TestCase):
    def test_weekday_morning_digest_gate_accepts_exact_target_minute_in_cet(self) -> None:
        now = datetime(2026, 3, 9, 7, 45, tzinfo=timezone.utc)  # 08:45 CET

        self.assertTrue(should_run_weekday_morning_digest(now))

    def test_weekday_morning_digest_gate_accepts_exact_target_minute_in_cest(self) -> None:
        now = datetime(2026, 4, 6, 6, 45, tzinfo=timezone.utc)  # 08:45 CEST

        self.assertTrue(should_run_weekday_morning_digest(now))

    def test_weekday_morning_digest_gate_accepts_delayed_run_within_same_local_hour(self) -> None:
        now = datetime(2026, 3, 9, 7, 59, tzinfo=timezone.utc)  # 08:59 CET

        self.assertTrue(should_run_weekday_morning_digest(now))

    def test_weekday_morning_digest_gate_rejects_weekend(self) -> None:
        now = datetime(2026, 3, 8, 7, 45, tzinfo=timezone.utc)  # Sunday 08:45 CET

        self.assertFalse(should_run_weekday_morning_digest(now))

    def test_weekday_morning_digest_gate_rejects_wrong_local_hour(self) -> None:
        now = datetime(2026, 3, 9, 7, 30, tzinfo=timezone.utc)  # 08:30 CET

        self.assertFalse(should_run_weekday_morning_digest(now))

    def test_weekday_morning_digest_gate_rejects_next_local_hour(self) -> None:
        now = datetime(2026, 3, 9, 8, 0, tzinfo=timezone.utc)  # 09:00 CET

        self.assertFalse(should_run_weekday_morning_digest(now))

    def test_weekly_digest_gate_accepts_exact_target_minute(self) -> None:
        now = datetime(2026, 3, 8, 19, 30, tzinfo=timezone.utc)  # 20:30 CET

        self.assertTrue(should_run_sunday_weekly_digest(now))

    def test_weekly_digest_gate_accepts_delayed_run_within_same_local_hour(self) -> None:
        now = datetime(2026, 3, 8, 19, 37, tzinfo=timezone.utc)  # 20:37 CET

        self.assertTrue(should_run_sunday_weekly_digest(now))

    def test_weekly_digest_gate_rejects_wrong_local_hour(self) -> None:
        now = datetime(2026, 3, 8, 20, 0, tzinfo=timezone.utc)  # 21:00 CET

        self.assertFalse(should_run_sunday_weekly_digest(now))

    def test_weekly_digest_gate_rejects_before_target_minute(self) -> None:
        now = datetime(2026, 3, 8, 18, 45, tzinfo=timezone.utc)  # 19:45 CET

        self.assertFalse(should_run_sunday_weekly_digest(now))


if __name__ == "__main__":
    unittest.main()

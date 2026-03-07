from datetime import datetime
from datetime import timezone
from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from day_captain.adapters.storage import SQLiteStorage
from day_captain.app import StaticCalendarCollector
from day_captain.app import StaticMailCollector
from day_captain.app import StubAuthProvider
from day_captain.app import build_application
from day_captain.config import DayCaptainSettings
from day_captain.models import MeetingRecord
from day_captain.models import MessageRecord


class MorningRunPersistenceTest(unittest.TestCase):
    def test_repeated_runs_reuse_previous_window_end(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            path = str(Path(tmpdir) / "day_captain.sqlite3")
            settings = DayCaptainSettings(sqlite_path=path)
            storage = SQLiteStorage(path)
            first_now = datetime(2026, 3, 7, 8, 0, tzinfo=timezone.utc)
            second_now = datetime(2026, 3, 7, 12, 0, tzinfo=timezone.utc)
            app = build_application(
                settings=settings,
                storage=storage,
                auth_provider=StubAuthProvider(),
                mail_collector=StaticMailCollector(
                    [
                        MessageRecord(
                            graph_message_id="msg-1",
                            thread_id="thread-1",
                            subject="Action needed on roadmap",
                            from_address="pm@example.com",
                            received_at=datetime(2026, 3, 7, 7, 45, tzinfo=timezone.utc),
                            body_preview="Need your input for planning.",
                        ),
                        MessageRecord(
                            graph_message_id="msg-2",
                            thread_id="thread-2",
                            subject="Urgent budget review",
                            from_address="boss@example.com",
                            received_at=datetime(2026, 3, 7, 9, 30, tzinfo=timezone.utc),
                            body_preview="Please review before noon.",
                        ),
                    ]
                ),
                calendar_collector=StaticCalendarCollector(
                    [
                        MeetingRecord(
                            graph_event_id="mtg-1",
                            subject="Weekly leadership sync",
                            start_at=datetime(2026, 3, 7, 10, 0, tzinfo=timezone.utc),
                            end_at=datetime(2026, 3, 7, 10, 30, tzinfo=timezone.utc),
                            organizer_address="ceo@example.com",
                        )
                    ]
                ),
            )

            first_run = app.run_morning_digest(now=first_now)
            second_run = app.run_morning_digest(now=second_now)

            self.assertEqual(first_run.window_end, second_run.window_start)
            self.assertEqual(len(second_run.critical_topics), 1)
            self.assertIsNotNone(storage.get_latest_completed_run())


if __name__ == "__main__":
    unittest.main()

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
from day_captain.models import MessageRecord


class FeedbackLearningTest(unittest.TestCase):
    def test_positive_feedback_creates_sender_preference(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            path = str(Path(tmpdir) / "day_captain.sqlite3")
            app = build_application(
                settings=DayCaptainSettings(sqlite_path=path),
                storage=SQLiteStorage(path),
                auth_provider=StubAuthProvider(),
                mail_collector=StaticMailCollector(
                    [
                        MessageRecord(
                            graph_message_id="msg-1",
                            thread_id="thread-1",
                            subject="Action needed on roadmap",
                            from_address="pm@example.com",
                            to_addresses=("alex@example.com",),
                            received_at=datetime(2026, 3, 7, 7, 50, tzinfo=timezone.utc),
                            body_preview="Need your input for planning.",
                        ),
                    ]
                ),
                calendar_collector=StaticCalendarCollector(()),
            )

            run = app.run_morning_digest(now=datetime(2026, 3, 7, 8, 0, tzinfo=timezone.utc), force=True)
            app.record_feedback(
                run_id=run.run_id,
                source_kind="message",
                source_id="msg-1",
                signal_type="useful",
                signal_value="true",
                recorded_at=datetime(2026, 3, 7, 8, 5, tzinfo=timezone.utc),
            )

            preferences = app.storage.load_preferences()
            sender_preferences = [item for item in preferences if item.preference_key == "sender:pm@example.com"]
            self.assertEqual(len(sender_preferences), 1)
            self.assertGreater(sender_preferences[0].weight, 0)

    def test_feedback_updates_only_the_target_user_scope(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            path = str(Path(tmpdir) / "day_captain.sqlite3")
            app = build_application(
                settings=DayCaptainSettings(
                    sqlite_path=path,
                    target_users=("alice@example.com", "bob@example.com"),
                ),
                storage=SQLiteStorage(path),
                auth_provider=StubAuthProvider(),
                mail_collector=StaticMailCollector(
                    [
                        MessageRecord(
                            graph_message_id="msg-1",
                            thread_id="thread-1",
                            subject="Action needed on roadmap",
                            from_address="pm@example.com",
                            to_addresses=("alex@example.com",),
                            received_at=datetime(2026, 3, 7, 7, 50, tzinfo=timezone.utc),
                            body_preview="Need your input for planning.",
                        ),
                    ]
                ),
                calendar_collector=StaticCalendarCollector(()),
            )

            alice_run = app.run_morning_digest(
                now=datetime(2026, 3, 7, 8, 0, tzinfo=timezone.utc),
                force=True,
                target_user_id="alice@example.com",
            )
            app.run_morning_digest(
                now=datetime(2026, 3, 7, 8, 0, tzinfo=timezone.utc),
                force=True,
                target_user_id="bob@example.com",
            )
            app.record_feedback(
                run_id=alice_run.run_id,
                source_kind="message",
                source_id="msg-1",
                signal_type="useful",
                signal_value="true",
                recorded_at=datetime(2026, 3, 7, 8, 5, tzinfo=timezone.utc),
            )

            alice_preferences = app.storage.load_preferences(tenant_id="common", user_id="alice@example.com")
            bob_preferences = app.storage.load_preferences(tenant_id="common", user_id="bob@example.com")

            self.assertEqual(len([item for item in alice_preferences if item.preference_key == "sender:pm@example.com"]), 1)
            self.assertEqual(len([item for item in bob_preferences if item.preference_key == "sender:pm@example.com"]), 0)


if __name__ == "__main__":
    unittest.main()

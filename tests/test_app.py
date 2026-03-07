from datetime import datetime
from datetime import timezone
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from day_captain.app import InMemoryStorage
from day_captain.app import StaticCalendarCollector
from day_captain.app import StaticMailCollector
from day_captain.app import build_application
from day_captain.config import DayCaptainSettings
from day_captain.models import MeetingRecord
from day_captain.models import MessageRecord
from day_captain.models import UserPreference


class DayCaptainApplicationTest(unittest.TestCase):
    def test_morning_digest_returns_sections_and_persists_run(self) -> None:
        now = datetime(2026, 3, 7, 8, 0, tzinfo=timezone.utc)
        storage = InMemoryStorage(
            preferences=[
                UserPreference(
                    preference_key="sender:boss@example.com",
                    preference_type="sender",
                    weight=2.0,
                    source="seed",
                    updated_at=now,
                )
            ]
        )
        app = build_application(
            settings=DayCaptainSettings(),
            storage=storage,
            mail_collector=StaticMailCollector(
                [
                    MessageRecord(
                        graph_message_id="msg-1",
                        thread_id="thread-1",
                        subject="Urgent budget review",
                        from_address="boss@example.com",
                        received_at=datetime(2026, 3, 7, 7, 30, tzinfo=timezone.utc),
                        body_preview="Please review before noon.",
                    ),
                    MessageRecord(
                        graph_message_id="msg-2",
                        thread_id="thread-2",
                        subject="Action needed on roadmap",
                        from_address="pm@example.com",
                        received_at=datetime(2026, 3, 7, 7, 45, tzinfo=timezone.utc),
                        body_preview="Need your input for planning.",
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

        payload = app.run_morning_digest(now=now)

        self.assertEqual(payload.delivery_mode, "json")
        self.assertEqual(len(payload.critical_topics), 1)
        self.assertEqual(payload.critical_topics[0].source_id, "msg-1")
        self.assertEqual(len(payload.actions_to_take), 1)
        self.assertEqual(len(payload.upcoming_meetings), 1)
        self.assertIsNotNone(storage.get_latest_completed_run())

    def test_recall_returns_latest_run_for_day(self) -> None:
        now = datetime(2026, 3, 7, 8, 0, tzinfo=timezone.utc)
        storage = InMemoryStorage()
        app = build_application(settings=DayCaptainSettings(), storage=storage)

        created = app.run_morning_digest(now=now)
        recalled = app.recall_digest(day=now.date())

        self.assertEqual(recalled.run_id, created.run_id)

    def test_record_feedback_saves_signal(self) -> None:
        now = datetime(2026, 3, 7, 8, 0, tzinfo=timezone.utc)
        storage = InMemoryStorage()
        app = build_application(settings=DayCaptainSettings(), storage=storage)
        run = app.run_morning_digest(now=now)

        feedback = app.record_feedback(
            run_id=run.run_id,
            source_kind="message",
            source_id="msg-1",
            signal_type="useful",
            signal_value="true",
            recorded_at=now,
        )

        self.assertEqual(feedback.run_id, run.run_id)
        self.assertEqual(len(storage.list_feedback(run.run_id)), 1)


if __name__ == "__main__":
    unittest.main()

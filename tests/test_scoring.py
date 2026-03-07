from datetime import datetime
from datetime import timezone
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from day_captain.models import MeetingRecord
from day_captain.models import MessageRecord
from day_captain.models import UserPreference
from day_captain.services import DeterministicScoringEngine


class DeterministicScoringEngineTest(unittest.TestCase):
    def test_filters_newsletter_noise_and_preserves_critical_message(self) -> None:
        now = datetime(2026, 3, 7, 8, 0, tzinfo=timezone.utc)
        engine = DeterministicScoringEngine()
        messages = (
            MessageRecord(
                graph_message_id="msg-news",
                thread_id="thread-news",
                subject="Weekly newsletter digest",
                from_address="noreply@vendor.example",
                received_at=datetime(2026, 3, 7, 7, 30, tzinfo=timezone.utc),
                body_preview="Top stories for the week.",
            ),
            MessageRecord(
                graph_message_id="msg-critical",
                thread_id="thread-critical",
                subject="Urgent production incident",
                from_address="boss@example.com",
                to_addresses=("alex@example.com",),
                received_at=datetime(2026, 3, 7, 7, 45, tzinfo=timezone.utc),
                body_preview="Please join immediately.",
            ),
        )

        prioritized = engine.prioritize(messages, (), (), reference_time=now)

        self.assertEqual(len(prioritized), 1)
        self.assertEqual(prioritized[0].source_id, "msg-critical")
        self.assertEqual(prioritized[0].section_name, "critical_topics")
        self.assertIn("critical_keyword", prioritized[0].reason_codes)

    def test_uses_preferences_and_action_cues_for_actions_section(self) -> None:
        now = datetime(2026, 3, 7, 8, 0, tzinfo=timezone.utc)
        engine = DeterministicScoringEngine()
        preferences = (
            UserPreference(
                preference_key="sender:pm@example.com",
                preference_type="sender",
                weight=1.5,
                source="seed",
                updated_at=now,
            ),
        )
        messages = (
            MessageRecord(
                graph_message_id="msg-action",
                thread_id="thread-action",
                subject="Action needed on roadmap",
                from_address="pm@example.com",
                to_addresses=("alex@example.com",),
                received_at=datetime(2026, 3, 7, 7, 50, tzinfo=timezone.utc),
                body_preview="Need your input for planning.",
            ),
        )

        prioritized = engine.prioritize(messages, (), preferences, reference_time=now)

        self.assertEqual(prioritized[0].section_name, "actions_to_take")
        self.assertIn("preference_signal", prioritized[0].reason_codes)
        self.assertIn("action_keyword", prioritized[0].reason_codes)
        self.assertGreater(prioritized[0].score, 2.0)

    def test_scores_meetings_into_upcoming_section(self) -> None:
        now = datetime(2026, 3, 7, 8, 0, tzinfo=timezone.utc)
        engine = DeterministicScoringEngine()
        meetings = (
            MeetingRecord(
                graph_event_id="mtg-1",
                subject="Leadership sync",
                start_at=datetime(2026, 3, 7, 9, 0, tzinfo=timezone.utc),
                end_at=datetime(2026, 3, 7, 9, 30, tzinfo=timezone.utc),
                organizer_address="ceo@example.com",
                location="Teams",
            ),
        )

        prioritized = engine.prioritize((), meetings, (), reference_time=now)

        self.assertEqual(prioritized[0].section_name, "upcoming_meetings")
        self.assertIn("meeting_soon", prioritized[0].reason_codes)


if __name__ == "__main__":
    unittest.main()

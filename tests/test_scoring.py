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

    def test_filters_dmarc_aggregate_reports_and_cold_outreach(self) -> None:
        now = datetime(2026, 3, 7, 8, 0, tzinfo=timezone.utc)
        engine = DeterministicScoringEngine()
        messages = (
            MessageRecord(
                graph_message_id="msg-dmarc",
                thread_id="thread-dmarc",
                subject="Report Domain: example.com Submitter: protection.outlook.com",
                from_address="postmaster@protection.outlook.com",
                to_addresses=("alex@example.com",),
                received_at=datetime(2026, 3, 7, 7, 30, tzinfo=timezone.utc),
                body_preview="This is a DMARC aggregate report. You are receiving this because of the rua tag.",
                has_attachments=True,
            ),
            MessageRecord(
                graph_message_id="msg-sales",
                thread_id="thread-sales",
                subject="Custom Cable Solutions for ELD Hardware",
                from_address="sales@vendor.example",
                to_addresses=("alex@example.com",),
                received_at=datetime(2026, 3, 7, 7, 35, tzinfo=timezone.utc),
                body_preview="We help ELD providers with custom cables. Key features include connector customization and OEM support.",
                is_unread=True,
            ),
        )

        prioritized = engine.prioritize(messages, (), (), reference_time=now)

        self.assertEqual(prioritized, ())

    def test_collapses_duplicate_messages_from_same_thread(self) -> None:
        now = datetime(2026, 3, 7, 8, 0, tzinfo=timezone.utc)
        engine = DeterministicScoringEngine()
        messages = (
            MessageRecord(
                graph_message_id="msg-thread-1",
                thread_id="thread-print",
                subject="Print request",
                from_address="vendor@example.com",
                to_addresses=("alex@example.com",),
                received_at=datetime(2026, 3, 7, 7, 0, tzinfo=timezone.utc),
                body_preview="First reply in the thread.",
            ),
            MessageRecord(
                graph_message_id="msg-thread-2",
                thread_id="thread-print",
                subject="Re: Print request",
                from_address="vendor@example.com",
                to_addresses=("alex@example.com",),
                received_at=datetime(2026, 3, 7, 7, 30, tzinfo=timezone.utc),
                body_preview="Latest reply in the thread.",
                has_attachments=True,
            ),
        )

        prioritized = engine.prioritize(messages, (), (), reference_time=now)

        self.assertEqual(len(prioritized), 1)
        self.assertEqual(prioritized[0].source_id, "msg-thread-2")
        self.assertIn("thread_collapsed", prioritized[0].reason_codes)

    def test_filters_trivial_no_subject_messages_and_cleans_summary(self) -> None:
        now = datetime(2026, 3, 7, 8, 0, tzinfo=timezone.utc)
        engine = DeterministicScoringEngine()
        messages = (
            MessageRecord(
                graph_message_id="msg-empty",
                thread_id="thread-empty",
                subject="",
                from_address="vendor@example.com",
                received_at=datetime(2026, 3, 7, 7, 45, tzinfo=timezone.utc),
                body_preview="Sent from Outlook for Mac",
            ),
            MessageRecord(
                graph_message_id="msg-clean",
                thread_id="thread-clean",
                subject="Print request",
                from_address="vendor@example.com",
                to_addresses=("alex@example.com",),
                received_at=datetime(2026, 3, 7, 7, 50, tzinfo=timezone.utc),
                body_preview=(
                    "Bonjour,\r\n\r\nVoici la piece jointe.\r\n\r\n"
                    "De : Vendor <vendor@example.com>\r\nObjet : Print request"
                ),
            ),
        )

        prioritized = engine.prioritize(messages, (), (), reference_time=now)

        self.assertEqual(len(prioritized), 1)
        self.assertEqual(prioritized[0].source_id, "msg-clean")
        self.assertEqual(
            prioritized[0].summary,
            "Likely needs your follow-up: Bonjour, Voici la piece jointe.",
        )

    def test_marks_feedback_requests_as_actions(self) -> None:
        now = datetime(2026, 3, 7, 8, 0, tzinfo=timezone.utc)
        engine = DeterministicScoringEngine()
        messages = (
            MessageRecord(
                graph_message_id="msg-feedback",
                thread_id="thread-feedback",
                subject="Re: product demo review",
                from_address="agency@example.com",
                to_addresses=("alex@example.com",),
                received_at=datetime(2026, 3, 7, 7, 55, tzinfo=timezone.utc),
                body_preview="Bonjour, voici les dernieres remarques et feedback a integrer.",
            ),
        )

        prioritized = engine.prioritize(messages, (), (), reference_time=now)

        self.assertEqual(len(prioritized), 1)
        self.assertEqual(prioritized[0].section_name, "actions_to_take")
        self.assertIn("action_keyword", prioritized[0].reason_codes)

    def test_marks_print_and_download_deliverables_as_actions(self) -> None:
        now = datetime(2026, 3, 7, 8, 0, tzinfo=timezone.utc)
        engine = DeterministicScoringEngine()
        messages = (
            MessageRecord(
                graph_message_id="msg-print",
                thread_id="thread-print",
                subject="A imprimer",
                from_address="agency@example.com",
                to_addresses=("alex@example.com",),
                received_at=datetime(2026, 3, 7, 7, 50, tzinfo=timezone.utc),
                body_preview="Bonjour, voici notre logo en piece jointe.",
                has_attachments=True,
            ),
            MessageRecord(
                graph_message_id="msg-download",
                thread_id="thread-download",
                subject="Re: Rendu Salon MotiveX",
                from_address="agency@example.com",
                to_addresses=("alex@example.com",),
                received_at=datetime(2026, 3, 7, 7, 55, tzinfo=timezone.utc),
                body_preview="Voici la version modifiee. Lien de telechargement https://we.tl/example",
            ),
        )

        prioritized = engine.prioritize(messages, (), (), reference_time=now)

        self.assertEqual(prioritized[0].section_name, "actions_to_take")
        self.assertEqual(prioritized[0].title, "À imprimer")
        self.assertIn("deliverable_shared", prioritized[0].reason_codes)
        self.assertEqual(prioritized[1].section_name, "actions_to_take")

    def test_filters_self_sent_day_captain_digest_messages(self) -> None:
        now = datetime(2026, 3, 7, 8, 0, tzinfo=timezone.utc)
        engine = DeterministicScoringEngine()
        messages = (
            MessageRecord(
                graph_message_id="msg-digest",
                thread_id="thread-digest",
                subject="Your Day Captain brief for Sat 07 Mar",
                from_address="alex@example.com",
                to_addresses=("alex@example.com",),
                received_at=datetime(2026, 3, 7, 7, 59, tzinfo=timezone.utc),
                body_preview="Your Day Captain brief Prepared for you Sat 07 Mar 2026 at 17:39 CET",
            ),
        )

        prioritized = engine.prioritize(messages, (), (), reference_time=now)

        self.assertEqual(prioritized, ())

    def test_localizes_french_meeting_summary(self) -> None:
        now = datetime(2026, 3, 9, 8, 0, tzinfo=timezone.utc)
        engine = DeterministicScoringEngine(digest_language="fr", display_timezone="Europe/Paris")
        meetings = (
            MeetingRecord(
                graph_event_id="mtg-fr",
                subject="Point équipe",
                start_at=datetime(2026, 3, 9, 9, 0, tzinfo=timezone.utc),
                end_at=datetime(2026, 3, 9, 9, 30, tzinfo=timezone.utc),
                organizer_address="lead@example.com",
                location="Teams",
            ),
        )

        prioritized = engine.prioritize((), meetings, (), reference_time=now)

        self.assertEqual(prioritized[0].summary, "Aujourd'hui, 10:00 | Lead | Teams")

    def test_uses_natural_next_day_meeting_wording(self) -> None:
        now = datetime(2026, 3, 9, 8, 0, tzinfo=timezone.utc)
        engine = DeterministicScoringEngine(digest_language="en", display_timezone="Europe/Paris")
        meetings = (
            MeetingRecord(
                graph_event_id="mtg-next",
                subject="Planning sync",
                start_at=datetime(2026, 3, 10, 9, 0, tzinfo=timezone.utc),
                end_at=datetime(2026, 3, 10, 9, 30, tzinfo=timezone.utc),
                organizer_address="lead@example.com",
                location="Teams",
            ),
        )

        prioritized = engine.prioritize((), meetings, (), reference_time=now)

        self.assertEqual(prioritized[0].summary, "Tomorrow, 10:00 | Lead | Teams")

    def test_avoids_self_reference_in_meeting_summary(self) -> None:
        now = datetime(2026, 3, 9, 8, 0, tzinfo=timezone.utc)
        engine = DeterministicScoringEngine(digest_language="fr", display_timezone="Europe/Paris")
        meetings = (
            MeetingRecord(
                graph_event_id="mtg-self",
                subject="Site- Horizon",
                start_at=datetime(2026, 3, 10, 0, 0, tzinfo=timezone.utc),
                end_at=datetime(2026, 3, 10, 1, 0, tzinfo=timezone.utc),
                organizer_address="target.user@company.com",
                location="Site Horizon",
                user_id="target.user@company.com",
            ),
        )

        prioritized = engine.prioritize((), meetings, (), reference_time=now)

        self.assertEqual(prioritized[0].title, "Site Horizon")
        self.assertEqual(prioritized[0].summary, "Demain, 01:00 | Site Horizon")


if __name__ == "__main__":
    unittest.main()

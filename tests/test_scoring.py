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

    def test_filters_marketing_teaser_with_webpage_view_and_generic_security_language(self) -> None:
        now = datetime(2026, 3, 7, 8, 0, tzinfo=timezone.utc)
        engine = DeterministicScoringEngine()
        messages = (
            MessageRecord(
                graph_message_id="msg-marketing-teaser",
                thread_id="thread-marketing-teaser",
                subject="Industry outlook for connected operations",
                from_address="marketing@vendor.example",
                to_addresses=("alex@example.com",),
                received_at=datetime(2026, 3, 7, 7, 30, tzinfo=timezone.utc),
                body_preview="View as Webpage. Explore safety and cybersecurity trends shaping the industry this quarter.",
            ),
        )

        prioritized = engine.prioritize(messages, (), (), reference_time=now)

        self.assertEqual(prioritized, ())

    def test_filters_marketing_onboarding_sequence(self) -> None:
        now = datetime(2026, 3, 7, 8, 0, tzinfo=timezone.utc)
        engine = DeterministicScoringEngine()
        messages = (
            MessageRecord(
                graph_message_id="msg-marketing-onboarding",
                thread_id="thread-marketing-onboarding",
                subject="Welcome! Discover your Marketing Hub",
                from_address="hello@newsletter.example",
                to_addresses=("alex@example.com",),
                received_at=datetime(2026, 3, 7, 7, 40, tzinfo=timezone.utc),
                body_preview="Manage preferences and learn how to generate leads with our onboarding series.",
            ),
        )

        prioritized = engine.prioritize(messages, (), (), reference_time=now)

        self.assertEqual(prioritized, ())

    def test_keeps_automated_transactional_suspension_alert(self) -> None:
        now = datetime(2026, 3, 7, 8, 0, tzinfo=timezone.utc)
        engine = DeterministicScoringEngine(digest_language="fr", display_timezone="Europe/Paris")
        messages = (
            MessageRecord(
                graph_message_id="msg-service-alert",
                thread_id="thread-service-alert",
                subject="Action requise - le compte risque d'être suspendu",
                from_address="no-reply@service.example",
                to_addresses=("ops-team@example.com",),
                user_id="alex@example.com",
                received_at=datetime(2026, 3, 7, 7, 40, tzinfo=timezone.utc),
                body_preview="Le service sera suspendu pour défaut de paiement si le solde n'est pas régularisé.",
            ),
        )

        prioritized = engine.prioritize(messages, (), (), reference_time=now)

        self.assertEqual(len(prioritized), 1)
        self.assertEqual(prioritized[0].section_name, "critical_topics")
        self.assertIn("transactional_alert", prioritized[0].reason_codes)

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
                raw_payload={"webLink": "https://outlook.office.com/calendar/item/mtg-1"},
            ),
        )

        prioritized = engine.prioritize((), meetings, (), reference_time=now)

        self.assertEqual(prioritized[0].section_name, "upcoming_meetings")
        self.assertIn("meeting_soon", prioritized[0].reason_codes)
        self.assertEqual(prioritized[0].source_url, "https://outlook.office.com/calendar/item/mtg-1")

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

    def test_collapses_duplicate_operational_alerts_across_aliases(self) -> None:
        now = datetime(2026, 3, 7, 8, 0, tzinfo=timezone.utc)
        engine = DeterministicScoringEngine(digest_language="fr", display_timezone="Europe/Paris")
        messages = (
            MessageRecord(
                graph_message_id="msg-alert-a",
                thread_id="thread-alert-a",
                subject="Action requise - le service risque d'etre suspendu",
                from_address="no-reply@service.example",
                to_addresses=("ops-team@example.com",),
                received_at=datetime(2026, 3, 7, 7, 40, tzinfo=timezone.utc),
                body_preview="Le service sera suspendu pour defaut de paiement si le solde n'est pas regularise.",
            ),
            MessageRecord(
                graph_message_id="msg-alert-b",
                thread_id="thread-alert-b",
                subject="Action requise - le service risque d'etre suspendu",
                from_address="no-reply@service.example",
                to_addresses=("finance-team@example.com",),
                received_at=datetime(2026, 3, 7, 7, 42, tzinfo=timezone.utc),
                body_preview="Le service sera suspendu pour defaut de paiement si le solde n'est pas regularise.",
            ),
        )

        prioritized = engine.prioritize(messages, (), (), reference_time=now)

        self.assertEqual(len(prioritized), 1)
        self.assertEqual(prioritized[0].section_name, "critical_topics")
        self.assertIn("alias_deduped", prioritized[0].reason_codes)
        self.assertEqual(prioritized[0].context_metadata["grouping_kind"], "alias")
        self.assertEqual(prioritized[0].context_metadata["grouped_message_count"], 2)
        self.assertEqual(
            prioritized[0].context_metadata["grouped_aliases"],
            ["ops-team@example.com", "finance-team@example.com"],
        )

    def test_keeps_distinct_operational_alerts_separate_when_preview_differs(self) -> None:
        now = datetime(2026, 3, 7, 8, 0, tzinfo=timezone.utc)
        engine = DeterministicScoringEngine(digest_language="fr", display_timezone="Europe/Paris")
        messages = (
            MessageRecord(
                graph_message_id="msg-alert-account",
                thread_id="thread-alert-account",
                subject="Action requise - le service risque d'etre suspendu",
                from_address="no-reply@service.example",
                to_addresses=("ops-team@example.com",),
                received_at=datetime(2026, 3, 7, 7, 40, tzinfo=timezone.utc),
                body_preview="Le service sera suspendu pour defaut de paiement si le solde n'est pas regularise.",
            ),
            MessageRecord(
                graph_message_id="msg-alert-quota",
                thread_id="thread-alert-quota",
                subject="Action requise - le service risque d'etre suspendu",
                from_address="no-reply@service.example",
                to_addresses=("ops-team@example.com",),
                received_at=datetime(2026, 3, 7, 7, 42, tzinfo=timezone.utc),
                body_preview="Le service sera suspendu si le quota de verification n'est pas augmente.",
            ),
        )

        prioritized = engine.prioritize(messages, (), (), reference_time=now)

        self.assertEqual(len(prioritized), 2)
        self.assertTrue(all("alias_deduped" not in item.reason_codes for item in prioritized))

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
            "Likely needs your follow-up: Voici la piece jointe.",
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

    def test_demotes_promotional_ticket_mail_out_of_actions(self) -> None:
        now = datetime(2026, 3, 11, 7, 51, tzinfo=timezone.utc)
        engine = DeterministicScoringEngine(digest_language="fr", display_timezone="Europe/Paris")
        messages = (
            MessageRecord(
                graph_message_id="msg-promo-train",
                thread_id="thread-promo-train",
                subject="Romaric, les billets pour l'été sont en ligne !",
                from_address="info@rail.example",
                to_addresses=("romaric@example.com",),
                user_id="romaric@example.com",
                received_at=datetime(2026, 3, 11, 6, 55, tzinfo=timezone.utc),
                body_preview="Réservez dès maintenant vos billets pour la France et l'Europe. Consultez la version en ligne.",
            ),
        )

        prioritized = engine.prioritize(messages, (), (), reference_time=now)

        self.assertTrue(all(item.section_name != "actions_to_take" for item in prioritized))
        if prioritized:
            self.assertIn("promotional", prioritized[0].reason_codes)
            self.assertEqual(prioritized[0].recommended_action, "")

    def test_promotes_messages_directly_addressed_to_target_user(self) -> None:
        now = datetime(2026, 3, 10, 8, 0, tzinfo=timezone.utc)
        engine = DeterministicScoringEngine(digest_language="fr", display_timezone="Europe/Paris")
        messages = (
            MessageRecord(
                graph_message_id="msg-romaric",
                thread_id="thread-target",
                subject="Payment discussion-feedback",
                from_address="finance@example.com",
                to_addresses=("casey.morgan@example.com",),
                user_id="casey.morgan@example.com",
                received_at=datetime(2026, 3, 10, 7, 35, tzinfo=timezone.utc),
                body_preview="IM only edit the bank account and keep the same invoice No (B2334).",
                raw_payload={
                    "toRecipients": (
                        {
                            "emailAddress": {
                                "address": "casey.morgan@example.com",
                                "name": "Casey Morgan",
                            }
                        },
                    )
                },
            ),
        )

        prioritized = engine.prioritize(messages, (), (), reference_time=now)

        self.assertEqual(len(prioritized), 1)
        self.assertEqual(prioritized[0].section_name, "actions_to_take")
        self.assertIn("direct_target_recipient", prioritized[0].reason_codes)
        self.assertTrue(prioritized[0].summary.startswith("Vous êtes attendu sur ce point :"))
        self.assertIn("bank account", prioritized[0].summary)
        self.assertEqual(prioritized[0].context_metadata["target_recipient_display_name"], "Casey Morgan")
        self.assertIn("direct_follow_up_signal", prioritized[0].reason_codes)

    def test_direct_target_without_follow_up_signal_stays_out_of_actions(self) -> None:
        now = datetime(2026, 3, 10, 8, 0, tzinfo=timezone.utc)
        engine = DeterministicScoringEngine(digest_language="fr", display_timezone="Europe/Paris")
        messages = (
            MessageRecord(
                graph_message_id="msg-weekly-note",
                thread_id="thread-weekly-note",
                subject="Weekly coordination note",
                from_address="teamlead@example.com",
                to_addresses=("casey.morgan@example.com",),
                user_id="casey.morgan@example.com",
                received_at=datetime(2026, 3, 10, 7, 35, tzinfo=timezone.utc),
                body_preview="Le point hebdomadaire reste prevu demain a 09:00 dans la salle habituelle.",
            ),
        )

        prioritized = engine.prioritize(messages, (), (), reference_time=now)

        self.assertEqual(len(prioritized), 1)
        self.assertNotEqual(prioritized[0].section_name, "actions_to_take")
        self.assertNotIn("direct_follow_up_signal", prioritized[0].reason_codes)
        self.assertTrue(prioritized[0].summary.startswith("À noter :"))
        self.assertEqual(prioritized[0].recommended_action, "Garder ce sujet en vue ; aucune action explicite n'est encore certaine.")

    def test_keeps_english_action_text_clear_in_french_digest(self) -> None:
        now = datetime(2026, 3, 10, 8, 0, tzinfo=timezone.utc)
        engine = DeterministicScoringEngine(digest_language="fr", display_timezone="Europe/Paris")
        messages = (
            MessageRecord(
                graph_message_id="msg-bilingual",
                thread_id="thread-bilingual",
                subject="Payment discussion",
                from_address="finance@example.com",
                to_addresses=("team@example.com",),
                received_at=datetime(2026, 3, 10, 7, 40, tzinfo=timezone.utc),
                body_preview="Need your input before noon on the bank account update.",
            ),
        )

        prioritized = engine.prioritize(messages, (), (), reference_time=now)

        self.assertEqual(prioritized[0].section_name, "actions_to_take")
        self.assertTrue(prioritized[0].summary.startswith("Action : Need your input before noon"))
        self.assertEqual(prioritized[0].context_metadata["source_language_hint"], "en")

    def test_demotes_cc_only_action_when_next_step_appears_owned_by_someone_else(self) -> None:
        now = datetime(2026, 3, 10, 8, 0, tzinfo=timezone.utc)
        engine = DeterministicScoringEngine(digest_language="en", display_timezone="Europe/Paris")
        messages = (
            MessageRecord(
                graph_message_id="msg-owner-other",
                thread_id="thread-owner-other",
                subject="Please review the contract",
                from_address="legal@example.com",
                to_addresses=("jordan@example.com",),
                cc_addresses=("alex@example.com",),
                user_id="alex@example.com",
                received_at=datetime(2026, 3, 10, 7, 45, tzinfo=timezone.utc),
                body_preview="Jordan, please review the contract before noon.",
            ),
        )

        prioritized = engine.prioritize(messages, (), (), reference_time=now)

        self.assertEqual(prioritized[0].section_name, "watch_items")
        self.assertEqual(prioritized[0].card.action_owner, "other")
        self.assertFalse(prioritized[0].card.action_expected_from_user)
        self.assertIn("belong to Jordan", prioritized[0].recommended_action)

    def test_marks_sensitive_urgent_mail_as_suspicious_and_conservative(self) -> None:
        now = datetime(2026, 3, 10, 8, 0, tzinfo=timezone.utc)
        engine = DeterministicScoringEngine(digest_language="en", display_timezone="Europe/Paris")
        messages = (
            MessageRecord(
                graph_message_id="msg-suspicious",
                thread_id="thread-suspicious",
                subject="Urgent invoice update needed",
                from_address="billing@vendor-payments.example",
                to_addresses=("alex@example.com",),
                user_id="alex@example.com",
                received_at=datetime(2026, 3, 10, 7, 50, tzinfo=timezone.utc),
                body_preview="Urgent: confirm the bank account immediately via https://pay-now.example/reset.",
                has_attachments=True,
            ),
        )

        prioritized = engine.prioritize(messages, (), (), reference_time=now)

        self.assertEqual(prioritized[0].card.risk_level, "high")
        self.assertIn("suspicious_mail", prioritized[0].reason_codes)
        self.assertEqual(prioritized[0].section_name, "watch_items")
        self.assertEqual(prioritized[0].recommended_action, "Verify the sender before acting.")

    def test_populates_typed_card_for_recurring_meeting(self) -> None:
        now = datetime(2026, 3, 10, 8, 0, tzinfo=timezone.utc)
        engine = DeterministicScoringEngine(digest_language="fr", display_timezone="Europe/Paris")
        meetings = (
            MeetingRecord(
                graph_event_id="mtg-weekly-card",
                subject="Point équipe",
                start_at=datetime(2026, 3, 10, 9, 0, tzinfo=timezone.utc),
                end_at=datetime(2026, 3, 10, 9, 30, tzinfo=timezone.utc),
                organizer_address="lead@example.com",
                raw_payload={"recurrence": {"pattern": {"type": "weekly"}}},
            ),
        )

        prioritized = engine.prioritize((), meetings, (), reference_time=now)

        self.assertEqual(prioritized[0].card.recurrence_label, "Hebdo")

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
                organizer_address="target.user@example.com",
                location="Site Horizon",
                user_id="target.user@example.com",
            ),
        )

        prioritized = engine.prioritize((), meetings, (), reference_time=now)

        self.assertEqual(prioritized[0].title, "Site Horizon")
        self.assertEqual(prioritized[0].summary, "Demain, 01:00")

    def test_compacts_candidate_profile_message_summary(self) -> None:
        now = datetime(2026, 3, 9, 8, 0, tzinfo=timezone.utc)
        engine = DeterministicScoringEngine(digest_language="fr", display_timezone="Europe/Paris")
        messages = (
            MessageRecord(
                graph_message_id="msg-candidate",
                thread_id="thread-candidate",
                subject="Candidature spontanée - Designer",
                from_address="candidate@example.com",
                received_at=datetime(2026, 3, 9, 7, 30, tzinfo=timezone.utc),
                body_preview=(
                    "Madame, Monsieur, issu d'un bachelor en design transport et d'un master en design urbain, "
                    "je suis désormais designer chez Studio Meridian depuis plus de 4 ans et cherche une nouvelle opportunité."
                ),
            ),
        )

        prioritized = engine.prioritize(messages, (), (), reference_time=now)

        self.assertEqual(prioritized[0].section_name, "watch_items")
        self.assertEqual(
            prioritized[0].summary,
            "Profil candidat : designer chez Studio Meridian. Examiner la candidature ou proposer un suivi.",
        )

    def test_does_not_label_business_event_brief_as_candidate_profile(self) -> None:
        now = datetime(2026, 3, 10, 8, 0, tzinfo=timezone.utc)
        engine = DeterministicScoringEngine(digest_language="fr", display_timezone="Europe/Paris")
        messages = (
            MessageRecord(
                graph_message_id="msg-salon",
                thread_id="thread-salon",
                subject="Forum MotiveX | Organisation de la journée & brief",
                from_address="sara@example.com",
                to_addresses=("alex@example.com",),
                received_at=datetime(2026, 3, 10, 7, 30, tzinfo=timezone.utc),
                body_preview=(
                    "Le forum se tiendra le 12 mars au centre expo, un événement dédié à la mobilité "
                    "et aux solutions terrain. Objectif pour Northstar Mobility : identifier de nouvelles opportunités."
                ),
            ),
        )

        prioritized = engine.prioritize(messages, (), (), reference_time=now)

        self.assertEqual(prioritized[0].section_name, "watch_items")
        self.assertNotIn("Profil candidat", prioritized[0].summary)

    def test_cleans_reply_and_request_prefixes_from_message_titles(self) -> None:
        now = datetime(2026, 3, 9, 8, 0, tzinfo=timezone.utc)
        engine = DeterministicScoringEngine(digest_language="fr", display_timezone="Europe/Paris")
        messages = (
            MessageRecord(
                graph_message_id="msg-title",
                thread_id="thread-title",
                subject="RE: [Request received] A imprimer",
                from_address="agency@example.com",
                to_addresses=("alex@example.com",),
                received_at=datetime(2026, 3, 9, 7, 50, tzinfo=timezone.utc),
                body_preview="Votre badge est disponible.",
            ),
        )

        prioritized = engine.prioritize(messages, (), (), reference_time=now)

        self.assertEqual(prioritized[0].title, "À imprimer")

    def test_filters_low_signal_editorial_watch_items(self) -> None:
        now = datetime(2026, 3, 9, 8, 0, tzinfo=timezone.utc)
        engine = DeterministicScoringEngine(digest_language="fr", display_timezone="Europe/Paris")
        messages = (
            MessageRecord(
                graph_message_id="msg-article",
                thread_id="thread-article",
                subject="How to build SEO authority from scratch",
                from_address="founder@newsletter.example",
                to_addresses=("alex@example.com",),
                user_id="alex@example.com",
                received_at=datetime(2026, 3, 9, 7, 30, tzinfo=timezone.utc),
                body_preview="A practical look at directory backlinks and why they still matter in early SEO.",
            ),
        )

        prioritized = engine.prioritize(messages, (), (), reference_time=now)

        self.assertEqual(prioritized, ())

    def test_drops_courtesy_lead_in_action_summary(self) -> None:
        now = datetime(2026, 3, 9, 8, 0, tzinfo=timezone.utc)
        engine = DeterministicScoringEngine(digest_language="fr", display_timezone="Europe/Paris")
        messages = (
            MessageRecord(
                graph_message_id="msg-courtesy",
                thread_id="thread-courtesy",
                subject="RE: A imprimer",
                from_address="agency@example.com",
                to_addresses=("alex@example.com",),
                received_at=datetime(2026, 3, 9, 7, 50, tzinfo=timezone.utc),
                body_preview="Merci pour votre retour. Je vous confirme que votre badge sera disponible demain matin à l'agence.",
            ),
        )

        prioritized = engine.prioritize(messages, (), (), reference_time=now)

        self.assertEqual(prioritized[0].title, "À imprimer")
        self.assertNotIn("Merci pour votre retour", prioritized[0].summary)
        self.assertIn("badge sera disponible demain matin", prioritized[0].summary)

    def test_propagates_message_weblink_when_available(self) -> None:
        now = datetime(2026, 3, 9, 8, 0, tzinfo=timezone.utc)
        engine = DeterministicScoringEngine()
        messages = (
            MessageRecord(
                graph_message_id="msg-linked",
                thread_id="thread-linked",
                subject="Action needed on roadmap",
                from_address="pm@example.com",
                to_addresses=("alex@example.com",),
                received_at=datetime(2026, 3, 9, 7, 50, tzinfo=timezone.utc),
                body_preview="Need your input for planning.",
                raw_payload={"webLink": "https://outlook.office.com/mail/msg-linked"},
            ),
        )

        prioritized = engine.prioritize(messages, (), (), reference_time=now)

        self.assertEqual(prioritized[0].source_url, "https://outlook.office.com/mail/msg-linked")

    def test_promotes_flagged_messages_into_actions(self) -> None:
        now = datetime(2026, 3, 9, 8, 0, tzinfo=timezone.utc)
        engine = DeterministicScoringEngine()
        messages = (
            MessageRecord(
                graph_message_id="msg-flagged",
                thread_id="thread-flagged",
                subject="Budget note",
                from_address="pm@example.com",
                to_addresses=("alex@example.com",),
                received_at=datetime(2026, 3, 9, 7, 45, tzinfo=timezone.utc),
                body_preview="Please keep this in view.",
                raw_payload={
                    "flag": {"flagStatus": "flagged"},
                    "webLink": "https://outlook.office.com/mail/msg-flagged",
                },
            ),
        )

        prioritized = engine.prioritize(messages, (), (), reference_time=now)

        self.assertEqual(len(prioritized), 1)
        self.assertEqual(prioritized[0].section_name, "actions_to_take")
        self.assertIn("flagged", prioritized[0].reason_codes)
        self.assertEqual(prioritized[0].source_url, "https://outlook.office.com/mail/msg-flagged")

    def test_uses_first_non_self_attendee_when_organizer_is_target_user(self) -> None:
        now = datetime(2026, 3, 9, 8, 0, tzinfo=timezone.utc)
        engine = DeterministicScoringEngine(digest_language="fr", display_timezone="Europe/Paris")
        meetings = (
            MeetingRecord(
                graph_event_id="mtg-peer",
                subject="Point boîte email partagé",
                start_at=datetime(2026, 3, 9, 13, 30, tzinfo=timezone.utc),
                end_at=datetime(2026, 3, 9, 14, 0, tzinfo=timezone.utc),
                organizer_address="target.user@example.com",
                attendees=("morgan.lee@example.com", "target.user@example.com"),
                location="Réunion Microsoft Teams",
                user_id="target.user@example.com",
            ),
        )

        prioritized = engine.prioritize((), meetings, (), reference_time=now)

        self.assertEqual(prioritized[0].summary, "Aujourd'hui, 14:30 | Morgan Lee | Réunion Microsoft Teams")

    def test_detects_recently_cancelled_meeting_changes(self) -> None:
        now = datetime(2026, 3, 10, 8, 0, tzinfo=timezone.utc)
        window_start = datetime(2026, 3, 9, 22, 0, tzinfo=timezone.utc)
        engine = DeterministicScoringEngine(digest_language="fr", display_timezone="Europe/Paris")
        meetings = (
            MeetingRecord(
                graph_event_id="mtg-cancelled",
                subject="Equipe projet Hardware",
                start_at=datetime(2026, 3, 10, 9, 30, tzinfo=timezone.utc),
                end_at=datetime(2026, 3, 10, 10, 0, tzinfo=timezone.utc),
                organizer_address="engineering@example.com",
                location="Réunion Microsoft Teams",
                raw_payload={
                    "isCancelled": True,
                    "createdDateTime": "2026-03-01T08:00:00Z",
                    "lastModifiedDateTime": "2026-03-10T06:45:00Z",
                },
            ),
        )

        prioritized = engine.prioritize((), meetings, (), reference_time=now, window_start=window_start)

        self.assertEqual(len(prioritized), 1)
        self.assertIn("meeting_cancelled", prioritized[0].reason_codes)
        self.assertIn("meeting_updated", prioritized[0].reason_codes)
        self.assertTrue(prioritized[0].summary.startswith("Annulé :"))

    def test_classifies_all_day_presence_events_separately_from_meetings(self) -> None:
        now = datetime(2026, 3, 10, 8, 0, tzinfo=timezone.utc)
        engine = DeterministicScoringEngine(digest_language="fr", display_timezone="Europe/Paris")
        meetings = (
            MeetingRecord(
                graph_event_id="presence-1",
                subject="Télétravail",
                start_at=datetime(2026, 3, 10, 0, 0, tzinfo=timezone.utc),
                end_at=datetime(2026, 3, 10, 23, 59, tzinfo=timezone.utc),
                organizer_address="target.user@example.com",
                location="Télétravail",
                raw_payload={"isAllDay": True},
                user_id="target.user@example.com",
            ),
        )

        prioritized = engine.prioritize((), meetings, (), reference_time=now)

        self.assertEqual(prioritized[0].section_name, "daily_presence")
        self.assertIn("Signal de télétravail", prioritized[0].summary)
        self.assertEqual(prioritized[0].handling_bucket, "daily_presence")
        self.assertGreaterEqual(prioritized[0].confidence_score, 80)

    def test_thread_entries_include_context_and_confidence_metadata(self) -> None:
        now = datetime(2026, 3, 10, 8, 0, tzinfo=timezone.utc)
        engine = DeterministicScoringEngine(digest_language="en", display_timezone="Europe/Paris")
        messages = (
            MessageRecord(
                graph_message_id="msg-thread-1",
                thread_id="thread-budget",
                subject="Budget review",
                from_address="boss@example.com",
                to_addresses=("alex@example.com",),
                received_at=datetime(2026, 3, 10, 6, 30, tzinfo=timezone.utc),
                body_preview="Please review the budget deck.",
            ),
            MessageRecord(
                graph_message_id="msg-thread-2",
                thread_id="thread-budget",
                subject="Re: Budget review",
                from_address="boss@example.com",
                to_addresses=("alex@example.com",),
                received_at=datetime(2026, 3, 10, 7, 30, tzinfo=timezone.utc),
                body_preview="Need your input before noon.",
            ),
        )

        prioritized = engine.prioritize(messages, (), (), reference_time=now)

        self.assertEqual(prioritized[0].context_metadata["message_count"], 2)
        self.assertEqual(len(prioritized[0].context_metadata["messages"]), 2)
        self.assertTrue(prioritized[0].recommended_action)
        self.assertTrue(prioritized[0].confidence_label)
        self.assertGreater(prioritized[0].confidence_score, 0)

    def test_thread_summary_uses_older_context_when_latest_reply_is_too_short(self) -> None:
        now = datetime(2026, 3, 10, 8, 0, tzinfo=timezone.utc)
        engine = DeterministicScoringEngine(digest_language="fr", display_timezone="Europe/Paris")
        messages = (
            MessageRecord(
                graph_message_id="msg-thread-older",
                thread_id="thread-render",
                subject="Rendu clip salon",
                from_address="agency@example.com",
                to_addresses=("alex@example.com",),
                received_at=datetime(2026, 3, 10, 6, 45, tzinfo=timezone.utc),
                body_preview="Le rendu export final est prêt au téléchargement pour validation.",
            ),
            MessageRecord(
                graph_message_id="msg-thread-latest",
                thread_id="thread-render",
                subject="Re: Rendu clip salon",
                from_address="agency@example.com",
                to_addresses=("alex@example.com",),
                received_at=datetime(2026, 3, 10, 7, 30, tzinfo=timezone.utc),
                body_preview="Voici !",
            ),
        )

        prioritized = engine.prioritize(messages, (), (), reference_time=now)

        self.assertEqual(len(prioritized), 1)
        self.assertNotIn("Voici !", prioritized[0].summary)
        self.assertIn("rendu export final", prioritized[0].summary.lower())

    def test_meeting_summary_uses_related_message_context_when_available(self) -> None:
        now = datetime(2026, 3, 10, 8, 0, tzinfo=timezone.utc)
        engine = DeterministicScoringEngine(digest_language="en", display_timezone="Europe/Paris")
        meetings = (
            MeetingRecord(
                graph_event_id="mtg-context",
                subject="Roadmap sync",
                start_at=datetime(2026, 3, 10, 9, 0, tzinfo=timezone.utc),
                end_at=datetime(2026, 3, 10, 9, 30, tzinfo=timezone.utc),
                organizer_address="pm@example.com",
                location="Teams",
            ),
        )
        messages = (
            MessageRecord(
                graph_message_id="msg-roadmap",
                thread_id="thread-roadmap",
                subject="Roadmap sync prep",
                from_address="pm@example.com",
                to_addresses=("alex@example.com",),
                received_at=datetime(2026, 3, 10, 7, 15, tzinfo=timezone.utc),
                body_preview="Please review the launch milestones before the sync.",
            ),
        )

        prioritized = engine.prioritize(messages, meetings, (), reference_time=now)
        meeting_entry = next(item for item in prioritized if item.source_kind == "meeting")

        self.assertIn("Context:", meeting_entry.summary)
        self.assertIn("launch milestones", meeting_entry.summary)
        self.assertIn("meeting_related_context", meeting_entry.reason_codes)

    def test_meeting_summary_ignores_weak_single_token_message_overlap(self) -> None:
        now = datetime(2026, 3, 10, 8, 0, tzinfo=timezone.utc)
        engine = DeterministicScoringEngine(digest_language="fr", display_timezone="Europe/Paris")
        meetings = (
            MeetingRecord(
                graph_event_id="mtg-vendor-review",
                subject="Vendor review",
                start_at=datetime(2026, 3, 10, 9, 0, tzinfo=timezone.utc),
                end_at=datetime(2026, 3, 10, 9, 30, tzinfo=timezone.utc),
                organizer_address="contact@example.com",
                location="Teams",
            ),
        )
        messages = (
            MessageRecord(
                graph_message_id="msg-vendor-mail",
                thread_id="thread-vendor-mail",
                subject="Vendor contract",
                from_address="contact@example.com",
                to_addresses=("alex@example.com",),
                received_at=datetime(2026, 3, 10, 7, 15, tzinfo=timezone.utc),
                body_preview="Voici le point sur le contrat fournisseur pour validation.",
            ),
        )

        prioritized = engine.prioritize(messages, meetings, (), reference_time=now)
        meeting_entry = next(item for item in prioritized if item.source_kind == "meeting")

        self.assertNotIn("Contexte :", meeting_entry.summary)
        self.assertNotIn("meeting_related_context", meeting_entry.reason_codes)

    def test_filters_placeholder_meeting_from_upcoming_section(self) -> None:
        now = datetime(2026, 3, 10, 8, 0, tzinfo=timezone.utc)
        engine = DeterministicScoringEngine(digest_language="fr", display_timezone="Europe/Paris")
        meetings = (
            MeetingRecord(
                graph_event_id="mtg-placeholder",
                subject="HOLDING SLOT : vendor review and action items",
                start_at=datetime(2026, 3, 10, 9, 0, tzinfo=timezone.utc),
                end_at=datetime(2026, 3, 10, 9, 30, tzinfo=timezone.utc),
                organizer_address="alex@example.com",
                user_id="alex@example.com",
                location="Microsoft Teams Meeting",
                body_preview="*** CECI EST UN ESPACE RÉSERVÉ TEMPORAIRE *** Les modifications apportées à cet événement peuvent ne pas être conservées.",
            ),
        )

        prioritized = engine.prioritize((), meetings, (), reference_time=now)

        self.assertEqual(prioritized, ())

    def test_keeps_non_placeholder_private_work_block_visible(self) -> None:
        now = datetime(2026, 3, 10, 8, 0, tzinfo=timezone.utc)
        engine = DeterministicScoringEngine(digest_language="fr", display_timezone="Europe/Paris")
        meetings = (
            MeetingRecord(
                graph_event_id="mtg-focus-block",
                subject="Bloc de travail focus",
                start_at=datetime(2026, 3, 10, 9, 0, tzinfo=timezone.utc),
                end_at=datetime(2026, 3, 10, 10, 30, tzinfo=timezone.utc),
                organizer_address="alex@example.com",
                user_id="alex@example.com",
                location="Bureau",
                is_online_meeting=False,
                body_preview="Temps reserve pour finaliser la revue technique avant midi.",
            ),
        )

        prioritized = engine.prioritize((), meetings, (), reference_time=now)

        self.assertEqual(len(prioritized), 1)
        self.assertEqual(prioritized[0].section_name, "upcoming_meetings")

    def test_meeting_context_marks_recurring_events_when_metadata_supports_it(self) -> None:
        now = datetime(2026, 3, 10, 8, 0, tzinfo=timezone.utc)
        engine = DeterministicScoringEngine(digest_language="fr", display_timezone="Europe/Paris")
        meetings = (
            MeetingRecord(
                graph_event_id="mtg-weekly",
                subject="Point équipe",
                start_at=datetime(2026, 3, 11, 9, 0, tzinfo=timezone.utc),
                end_at=datetime(2026, 3, 11, 9, 30, tzinfo=timezone.utc),
                organizer_address="lead@example.com",
                location="Teams",
                raw_payload={
                    "type": "occurrence",
                    "seriesMasterId": "series-1",
                    "recurrence": {"pattern": {"type": "weekly"}},
                },
            ),
        )

        prioritized = engine.prioritize((), meetings, (), reference_time=now)

        self.assertIn("meeting_recurring", prioritized[0].reason_codes)
        self.assertEqual(prioritized[0].context_metadata["recurrence_label"], "Hebdo")


if __name__ == "__main__":
    unittest.main()

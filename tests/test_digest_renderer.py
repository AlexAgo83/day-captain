from datetime import datetime
from datetime import timezone
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from day_captain.models import DigestEntry
from day_captain.models import DigestCard
from day_captain.models import ExternalNewsItem
from day_captain.models import WeatherSnapshot
from day_captain.services import StructuredDigestRenderer


class StructuredDigestRendererTest(unittest.TestCase):
    def test_builds_delivery_body_and_graph_send_payload(self) -> None:
        renderer = StructuredDigestRenderer(display_timezone="Europe/Paris", digest_language="en")
        now = datetime(2026, 3, 7, 8, 0, tzinfo=timezone.utc)
        payload = renderer.render(
            run_id="run-1",
            generated_at=now,
            window_start=datetime(2026, 3, 6, 8, 0, tzinfo=timezone.utc),
            window_end=now,
            delivery_mode="graph_send",
            user_id="alex@example.com",
            command_mailbox="daycaptain@example.com",
            prioritized_items=(
                DigestEntry(
                    title="Urgent budget review",
                    summary="Critical: Please review before noon.",
                    section_name="critical_topics",
                    source_kind="message",
                    source_id="msg-1",
                    score=3.0,
                    reason_codes=("critical_keyword",),
                    guardrail_applied=True,
                ),
            ),
            top_summary="Budget review is the main priority this morning.",
            top_summary_source="llm",
            meeting_horizon={"mode": "same_day", "source_date": "2026-03-07", "target_date": "2026-03-07"},
        )

        self.assertIn("In brief", payload.delivery_body)
        self.assertIn("Budget review is the main priority this morning.", payload.delivery_body)
        self.assertIn("Critical topics", payload.delivery_body)
        self.assertIn("As of", payload.delivery_body)
        self.assertIn("Window: From Fri 06 Mar 2026 at 09:00 to Sat 07 Mar 2026 at 09:00 CET", payload.delivery_body)
        self.assertIn("Sat 07 Mar 2026 at 09:00 CET", payload.delivery_body)
        self.assertEqual(payload.delivery_subject, "Your Day Captain brief for Sat 07 Mar")
        self.assertEqual(payload.top_summary, "Budget review is the main priority this morning.")
        self.assertEqual(payload.delivery_payload["top_summary_source"], "llm")
        self.assertEqual(payload.delivery_payload["command_mailbox"], "daycaptain@example.com")
        self.assertIn("graph_message", payload.delivery_payload)
        self.assertEqual(payload.delivery_payload["graph_message"]["subject"], payload.delivery_subject)
        self.assertEqual(payload.delivery_payload["graph_message"]["body"]["contentType"], "HTML")
        self.assertEqual(
            payload.delivery_payload["graph_message"]["toRecipients"][0]["emailAddress"]["address"],
            "alex@example.com",
        )
        self.assertIn("<html>", payload.delivery_payload["html_body"])
        self.assertIn("In brief", payload.delivery_payload["html_body"])
        self.assertIn("No meetings are lined up for today.", payload.delivery_body)
        self.assertIn("Quick actions", payload.delivery_body)
        self.assertIn("Use these buttons to ask Day Captain for this brief again, today's brief, or this week's brief.", payload.delivery_body)
        self.assertIn("subject/body: recall", payload.delivery_body)
        self.assertIn("mailto:daycaptain@example.com?subject=recall&amp;body=recall", payload.delivery_payload["html_body"])
        self.assertIn("Day Captain © 2026: https://github.com/AlexAgo83/day-captain", payload.delivery_body)
        self.assertIn("margin:10px 0 24px;padding:0 0 0 14px;border-left:3px solid #94a3b8;", payload.delivery_payload["html_body"])
        self.assertNotIn("background:#f8fafc", payload.delivery_payload["html_body"])

    def test_localizes_french_copy_and_meeting_fallback_note(self) -> None:
        renderer = StructuredDigestRenderer(display_timezone="Europe/Paris", digest_language="fr")
        now = datetime(2026, 3, 8, 8, 0, tzinfo=timezone.utc)

        payload = renderer.render(
            run_id="run-2",
            generated_at=now,
            window_start=datetime(2026, 3, 7, 8, 0, tzinfo=timezone.utc),
            window_end=now,
            delivery_mode="json",
            prioritized_items=(),
            meeting_horizon={"mode": "weekend_monday", "source_date": "2026-03-08", "target_date": "2026-03-09"},
        )

        self.assertIn("Votre brief Day Captain", payload.delivery_body)
        self.assertIn("À jour au", payload.delivery_body)
        self.assertIn("Périmètre : Du sam. 07 mars 2026 à 09:00 au dim. 08 mars 2026 à 09:00 CET", payload.delivery_body)
        self.assertIn("Points critiques", payload.delivery_body)
        self.assertIn("Aperçu des réunions de lundi.", payload.delivery_body)
        self.assertEqual(payload.delivery_subject, "Votre brief Day Captain du dim. 08 mars")

    def test_compacts_meeting_entries_in_text_and_html(self) -> None:
        renderer = StructuredDigestRenderer(display_timezone="Europe/Paris", digest_language="fr")
        now = datetime(2026, 3, 9, 8, 0, tzinfo=timezone.utc)

        payload = renderer.render(
            run_id="run-3",
            generated_at=now,
            window_start=datetime(2026, 3, 8, 8, 0, tzinfo=timezone.utc),
            window_end=now,
            delivery_mode="json",
            prioritized_items=(
                DigestEntry(
                    title="Point equipe",
                    summary="Aujourd'hui, 10:00 | Lead | Teams",
                    section_name="upcoming_meetings",
                    source_kind="meeting",
                    source_id="mtg-1",
                    score=2.5,
                ),
            ),
        )

        self.assertIn("- Point equipe", payload.delivery_body)
        self.assertIn("Aujourd'hui, 10:00 | Lead | Teams", payload.delivery_body)
        self.assertIn("Confiance:", payload.delivery_body)
        self.assertIn("Point equipe", payload.delivery_payload["html_body"])
        self.assertIn("Aujourd'hui, 10:00 | Lead | Teams", payload.delivery_payload["html_body"])

    def test_renders_message_sender_meta_in_text_and_html(self) -> None:
        renderer = StructuredDigestRenderer(display_timezone="Europe/Paris", digest_language="fr")
        now = datetime(2026, 3, 10, 8, 0, tzinfo=timezone.utc)

        payload = renderer.render(
            run_id="run-sender",
            generated_at=now,
            window_start=datetime(2026, 3, 9, 8, 0, tzinfo=timezone.utc),
            window_end=now,
            delivery_mode="json",
            prioritized_items=(
                DigestEntry(
                    title="Point partenaire",
                    summary="Vous êtes attendu sur ce point : On reporte après le salon ?",
                    section_name="actions_to_take",
                    source_kind="message",
                    source_id="msg-1",
                    score=2.0,
                    context_metadata={"latest_sender_display_name": "Jordan Blake"},
                ),
            ),
        )

        self.assertIn("Expéditeur: Jordan Blake", payload.delivery_body)
        self.assertIn("<strong>Expéditeur:</strong> Jordan Blake", payload.delivery_payload["html_body"])

    def test_renders_message_read_state_and_received_time_in_text_and_html(self) -> None:
        renderer = StructuredDigestRenderer(display_timezone="Europe/Paris", digest_language="fr")
        now = datetime(2026, 3, 10, 8, 0, tzinfo=timezone.utc)

        payload = renderer.render(
            run_id="run-meta-fr",
            generated_at=now,
            window_start=datetime(2026, 3, 9, 8, 0, tzinfo=timezone.utc),
            window_end=now,
            delivery_mode="json",
            prioritized_items=(
                DigestEntry(
                    title="Suivi client",
                    summary="Vous êtes attendu sur ce point : Peut-on confirmer le créneau ?",
                    section_name="actions_to_take",
                    source_kind="message",
                    source_id="msg-meta-fr",
                    score=2.4,
                    sort_at=datetime(2026, 3, 10, 7, 15, tzinfo=timezone.utc),
                    context_metadata={
                        "latest_sender_display_name": "Jordan Blake",
                        "latest_is_unread": True,
                    },
                ),
            ),
        )

        self.assertIn("[Non lu] Suivi client", payload.delivery_body)
        self.assertIn("Statut: Non lu", payload.delivery_body)
        self.assertIn("Reçu: mar. 10 mars 2026 à 08:15 CET", payload.delivery_body)
        self.assertIn(">Non lu</span>Suivi client", payload.delivery_payload["html_body"])
        self.assertIn("<strong>Statut:</strong> Non lu", payload.delivery_payload["html_body"])
        self.assertIn("<strong>Reçu:</strong> mar. 10 mars 2026 à 08:15 CET", payload.delivery_payload["html_body"])

    def test_renders_read_state_without_unread_badge_for_read_messages(self) -> None:
        renderer = StructuredDigestRenderer(display_timezone="Europe/Paris", digest_language="en")
        now = datetime(2026, 3, 10, 8, 0, tzinfo=timezone.utc)

        payload = renderer.render(
            run_id="run-meta-en",
            generated_at=now,
            window_start=datetime(2026, 3, 9, 8, 0, tzinfo=timezone.utc),
            window_end=now,
            delivery_mode="json",
            prioritized_items=(
                DigestEntry(
                    title="Budget follow-up",
                    summary="Likely needs your follow-up: Can we close this today?",
                    section_name="actions_to_take",
                    source_kind="message",
                    source_id="msg-meta-en",
                    score=2.2,
                    sort_at=datetime(2026, 3, 10, 7, 5, tzinfo=timezone.utc),
                    context_metadata={"latest_is_unread": False},
                ),
            ),
        )

        self.assertIn("Status: Read", payload.delivery_body)
        self.assertIn("Received: Tue 10 Mar 2026 at 08:05 CET", payload.delivery_body)
        self.assertNotIn("[Unread] Budget follow-up", payload.delivery_body)
        self.assertIn("<strong>Status:</strong> Read", payload.delivery_payload["html_body"])

    def test_orders_upcoming_meetings_chronologically(self) -> None:
        renderer = StructuredDigestRenderer(display_timezone="Europe/Paris", digest_language="fr")
        now = datetime(2026, 3, 10, 8, 0, tzinfo=timezone.utc)

        payload = renderer.render(
            run_id="run-3-order",
            generated_at=now,
            window_start=datetime(2026, 3, 9, 8, 0, tzinfo=timezone.utc),
            window_end=now,
            delivery_mode="json",
            prioritized_items=(
                DigestEntry(
                    title="Réunion de 11h",
                    summary="Aujourd'hui, 11:00 | Lead | Teams",
                    section_name="upcoming_meetings",
                    source_kind="meeting",
                    source_id="mtg-11",
                    score=4.0,
                    sort_at=datetime(2026, 3, 10, 10, 0, tzinfo=timezone.utc),
                ),
                DigestEntry(
                    title="Réunion de 10h",
                    summary="Aujourd'hui, 10:00 | Lead | Teams",
                    section_name="upcoming_meetings",
                    source_kind="meeting",
                    source_id="mtg-10",
                    score=2.0,
                    sort_at=datetime(2026, 3, 10, 9, 0, tzinfo=timezone.utc),
                ),
            ),
        )

        self.assertLess(payload.delivery_body.index("Réunion de 10h"), payload.delivery_body.index("Réunion de 11h"))

    def test_renders_meeting_change_prefixes(self) -> None:
        renderer = StructuredDigestRenderer(display_timezone="Europe/Paris", digest_language="fr")
        now = datetime(2026, 3, 10, 8, 0, tzinfo=timezone.utc)

        payload = renderer.render(
            run_id="run-3-status",
            generated_at=now,
            window_start=datetime(2026, 3, 9, 8, 0, tzinfo=timezone.utc),
            window_end=now,
            delivery_mode="json",
            prioritized_items=(
                DigestEntry(
                    title="Equipe projet Hardware",
                    summary="Annulé : Aujourd'hui, 10:30 | Engineering | Réunion Microsoft Teams",
                    section_name="upcoming_meetings",
                    source_kind="meeting",
                    source_id="mtg-cancelled",
                    score=4.0,
                    sort_at=datetime(2026, 3, 10, 9, 30, tzinfo=timezone.utc),
                    reason_codes=("meeting_cancelled",),
                ),
            ),
        )

        self.assertIn("Annulé : Equipe projet Hardware", payload.delivery_body)
        self.assertIn("Annulé : Equipe projet Hardware", payload.delivery_payload["html_body"])

    def test_renders_item_open_controls_when_source_links_exist(self) -> None:
        renderer = StructuredDigestRenderer(display_timezone="Europe/Paris", digest_language="fr")
        now = datetime(2026, 3, 9, 8, 0, tzinfo=timezone.utc)

        payload = renderer.render(
            run_id="run-3b",
            generated_at=now,
            window_start=datetime(2026, 3, 8, 8, 0, tzinfo=timezone.utc),
            window_end=now,
            delivery_mode="json",
            prioritized_items=(
                DigestEntry(
                    title="Point equipe",
                    summary="Aujourd'hui, 10:00 | Lead | Teams",
                    section_name="upcoming_meetings",
                    source_kind="meeting",
                    source_id="mtg-1",
                    source_url="https://outlook.office.com/calendar/item/mtg-1",
                    score=2.5,
                ),
                DigestEntry(
                    title="Urgent budget review",
                    summary="Critical: Please review before noon.",
                    section_name="critical_topics",
                    source_kind="message",
                    source_id="msg-1",
                    source_url="https://outlook.office.com/mail/msg-1",
                    score=3.0,
                ),
            ),
        )

        self.assertIn("Ouvrir la réunion", payload.delivery_body)
        self.assertIn("Ouvrir dans Outlook", payload.delivery_body)
        self.assertIn("href=\"https://outlook.office.com/calendar/item/mtg-1\"", payload.delivery_payload["html_body"])
        self.assertIn("href=\"https://outlook.office.com/mail/msg-1\"", payload.delivery_payload["html_body"])

    def test_prefers_desktop_open_controls_when_native_link_is_available(self) -> None:
        renderer = StructuredDigestRenderer(display_timezone="Europe/Paris", digest_language="en")
        now = datetime(2026, 3, 9, 8, 0, tzinfo=timezone.utc)

        payload = renderer.render(
            run_id="run-3c",
            generated_at=now,
            window_start=datetime(2026, 3, 8, 8, 0, tzinfo=timezone.utc),
            window_end=now,
            delivery_mode="json",
            prioritized_items=(
                DigestEntry(
                    title="Leadership sync",
                    summary="Today, 10:00 | Lead | Teams",
                    section_name="upcoming_meetings",
                    source_kind="meeting",
                    source_id="mtg-1",
                    source_url="https://outlook.office.com/calendar/item/mtg-1",
                    desktop_source_url="ms-outlook://events/mtg-1",
                    score=2.5,
                ),
            ),
        )

        self.assertIn("Open meeting in Outlook desktop", payload.delivery_body)
        self.assertIn("href=\"ms-outlook://events/mtg-1\"", payload.delivery_payload["html_body"])
        self.assertNotIn("href=\"https://outlook.office.com/calendar/item/mtg-1\"", payload.delivery_payload["html_body"])

    def test_preserves_full_top_summary_copy(self) -> None:
        renderer = StructuredDigestRenderer(display_timezone="Europe/Paris", digest_language="en")
        now = datetime(2026, 3, 9, 8, 0, tzinfo=timezone.utc)

        payload = renderer.render(
            run_id="run-4",
            generated_at=now,
            window_start=datetime(2026, 3, 8, 8, 0, tzinfo=timezone.utc),
            window_end=now,
            delivery_mode="json",
            prioritized_items=(),
            top_summary=(
                "First priority is budget review. "
                "Second priority is confirming the launch timing. "
                "Third note should not appear in the executive summary."
            ),
        )

        self.assertEqual(
            payload.top_summary,
            (
                "First priority is budget review. "
                "Second priority is confirming the launch timing. "
                "Third note should not appear in the executive summary."
            ),
        )
        self.assertIn("Third note should not appear", payload.delivery_body)

    def test_renders_flagged_badge_in_text_and_html(self) -> None:
        renderer = StructuredDigestRenderer(display_timezone="Europe/Paris", digest_language="en")
        now = datetime(2026, 3, 9, 8, 0, tzinfo=timezone.utc)

        payload = renderer.render(
            run_id="run-4b",
            generated_at=now,
            window_start=datetime(2026, 3, 8, 8, 0, tzinfo=timezone.utc),
            window_end=now,
            delivery_mode="json",
            prioritized_items=(
                DigestEntry(
                    title="Budget note",
                    summary="Please keep this in view.",
                    section_name="actions_to_take",
                    source_kind="message",
                    source_id="msg-flagged",
                    score=2.0,
                    reason_codes=("flagged",),
                ),
            ),
        )

        self.assertIn("[Flagged] Budget note", payload.delivery_body)
        self.assertIn(">Flagged<", payload.delivery_payload["html_body"])

    def test_renders_promotional_badge_without_next_step(self) -> None:
        renderer = StructuredDigestRenderer(display_timezone="Europe/Paris", digest_language="fr")
        now = datetime(2026, 3, 11, 8, 0, tzinfo=timezone.utc)

        payload = renderer.render(
            run_id="run-promo",
            generated_at=now,
            window_start=datetime(2026, 3, 10, 8, 0, tzinfo=timezone.utc),
            window_end=now,
            delivery_mode="json",
            prioritized_items=(
                DigestEntry(
                    title="Billets été",
                    summary="Annonce commerciale sur des billets désormais disponibles en ligne.",
                    section_name="watch_items",
                    source_kind="message",
                    source_id="msg-promo",
                    score=0.8,
                    reason_codes=("promotional",),
                    context_metadata={"latest_sender_display_name": "Info"},
                    confidence_score=52,
                    confidence_reason="Le contenu ressemble surtout à un message promotionnel plutôt qu'à une demande opérationnelle concrète.",
                ),
            ),
        )

        self.assertIn("[Promotion] Billets été", payload.delivery_body)
        self.assertIn(">Promotion<", payload.delivery_payload["html_body"])
        self.assertNotIn("À faire:", payload.delivery_body)
        self.assertNotIn("<strong>À faire:</strong>", payload.delivery_payload["html_body"])

    def test_renders_weather_capsule_before_overview(self) -> None:
        renderer = StructuredDigestRenderer(display_timezone="Europe/Paris", digest_language="en")
        now = datetime(2026, 3, 9, 8, 0, tzinfo=timezone.utc)

        payload = renderer.render(
            run_id="run-weather",
            generated_at=now,
            window_start=datetime(2026, 3, 8, 8, 0, tzinfo=timezone.utc),
            window_end=now,
            delivery_mode="json",
            prioritized_items=(),
            top_summary="Review the open priorities first.",
            weather=WeatherSnapshot(
                forecast_date=datetime(2026, 3, 9, tzinfo=timezone.utc).date(),
                weather_code=61,
                temperature_max_c=13.4,
                temperature_min_c=6.1,
                location_name="Paris",
                previous_temperature_max_c=11.0,
            ),
        )

        self.assertIn("Today's weather", payload.delivery_body)
        self.assertIn("Paris: Rain, 13C max / 6C min. Rain likely. Warmer than yesterday.", payload.delivery_body)
        self.assertLess(payload.delivery_body.index("Today's weather"), payload.delivery_body.index("In brief"))
        self.assertIn("Today's weather", payload.delivery_payload["html_body"])
        self.assertIn("Paris: Rain, 13C max / 6C min. Rain likely. Warmer than yesterday.", payload.delivery_payload["html_body"])
        self.assertEqual(payload.delivery_payload["weather"]["location_name"], "Paris")

    def test_localizes_weather_capsule_in_french(self) -> None:
        renderer = StructuredDigestRenderer(display_timezone="Europe/Paris", digest_language="fr")
        now = datetime(2026, 3, 9, 8, 0, tzinfo=timezone.utc)

        payload = renderer.render(
            run_id="run-weather-fr",
            generated_at=now,
            window_start=datetime(2026, 3, 8, 8, 0, tzinfo=timezone.utc),
            window_end=now,
            delivery_mode="json",
            prioritized_items=(),
            weather=WeatherSnapshot(
                forecast_date=datetime(2026, 3, 9, tzinfo=timezone.utc).date(),
                weather_code=3,
                temperature_max_c=9.2,
                temperature_min_c=3.3,
                location_name="Lille",
                previous_temperature_max_c=9.0,
            ),
        )

        self.assertIn("Météo du jour", payload.delivery_body)
        self.assertIn("Lille: Couvert, 9C max / 3C min. Temps sec. Proche d'hier.", payload.delivery_body)

    def test_localizes_footer_quick_actions_in_french(self) -> None:
        renderer = StructuredDigestRenderer(display_timezone="Europe/Paris", digest_language="fr")
        now = datetime(2026, 3, 8, 8, 0, tzinfo=timezone.utc)

        payload = renderer.render(
            run_id="run-5",
            generated_at=now,
            window_start=datetime(2026, 3, 7, 8, 0, tzinfo=timezone.utc),
            window_end=now,
            delivery_mode="json",
            prioritized_items=(),
            command_mailbox="daycaptain@example.com",
        )

        self.assertIn("Actions rapides", payload.delivery_body)
        self.assertIn("Utilisez ces boutons pour redemander ce brief, celui d'aujourd'hui ou celui de la semaine.", payload.delivery_body)
        self.assertIn("Rappeler ce brief", payload.delivery_payload["html_body"])
        self.assertIn("subject=recall-week&amp;body=recall-week", payload.delivery_payload["html_body"])
        self.assertIn("Day Captain © 2026: https://github.com/AlexAgo83/day-captain", payload.delivery_body)
        self.assertIn(">Day Captain © 2026<", payload.delivery_payload["html_body"])
        self.assertIn("https://github.com/AlexAgo83/day-captain", payload.delivery_payload["html_body"])

    def test_renders_processing_duration_below_footer_signature(self) -> None:
        renderer = StructuredDigestRenderer(display_timezone="Europe/Paris", digest_language="fr")
        now = datetime(2026, 3, 8, 8, 0, tzinfo=timezone.utc)

        payload = renderer.render(
            run_id="run-5b",
            generated_at=now,
            window_start=datetime(2026, 3, 7, 8, 0, tzinfo=timezone.utc),
            window_end=now,
            delivery_mode="json",
            prioritized_items=(),
            command_mailbox="daycaptain@example.com",
            generation_duration_seconds=12.3,
        )

        self.assertIn("Day Captain © 2026: https://github.com/AlexAgo83/day-captain", payload.delivery_body)
        self.assertIn("Temps de génération: 12,3 s", payload.delivery_body)
        self.assertLess(
            payload.delivery_body.index("Day Captain © 2026: https://github.com/AlexAgo83/day-captain"),
            payload.delivery_body.index("Temps de génération: 12,3 s"),
        )
        self.assertIn(">Day Captain © 2026<", payload.delivery_payload["html_body"])
        self.assertIn("Temps de génération: 12,3 s", payload.delivery_payload["html_body"])
        self.assertEqual(payload.delivery_payload["generation_duration_seconds"], 12.3)

    def test_omits_meeting_open_action_when_no_source_link_exists(self) -> None:
        renderer = StructuredDigestRenderer(display_timezone="Europe/Paris", digest_language="fr")
        now = datetime(2026, 3, 9, 8, 0, tzinfo=timezone.utc)

        payload = renderer.render(
            run_id="run-5c",
            generated_at=now,
            window_start=datetime(2026, 3, 8, 8, 0, tzinfo=timezone.utc),
            window_end=now,
            delivery_mode="json",
            prioritized_items=(
                DigestEntry(
                    title="Point equipe sans lien",
                    summary="Aujourd'hui, 10:00 | Lead | Teams",
                    section_name="upcoming_meetings",
                    source_kind="meeting",
                    source_id="mtg-no-link",
                    score=2.5,
                ),
            ),
        )

        self.assertNotIn("Ouvrir la réunion", payload.delivery_body)
        self.assertNotIn("Open meeting", payload.delivery_body)
        self.assertNotIn("Point equipe sans lien</a>", payload.delivery_payload["html_body"])

    def test_renders_external_news_capsule_between_weather_and_overview(self) -> None:
        renderer = StructuredDigestRenderer(display_timezone="Europe/Paris", digest_language="en")
        now = datetime(2026, 3, 9, 8, 0, tzinfo=timezone.utc)

        payload = renderer.render(
            run_id="run-news",
            generated_at=now,
            window_start=datetime(2026, 3, 8, 8, 0, tzinfo=timezone.utc),
            window_end=now,
            delivery_mode="json",
            prioritized_items=(),
            top_summary="Review the open priorities first.",
            weather=WeatherSnapshot(
                forecast_date=datetime(2026, 3, 9, tzinfo=timezone.utc).date(),
                weather_code=61,
                temperature_max_c=13.4,
                temperature_min_c=6.1,
                location_name="Paris",
                previous_temperature_max_c=11.0,
            ),
            external_news=(
                ExternalNewsItem(
                    headline="ECB signals slower cuts",
                    summary="Markets are recalibrating rate expectations ahead of the next meeting.",
                    source_name="Financial Times",
                    source_url="https://example.com/ft/ecb",
                ),
            ),
        )

        self.assertIn("External news", payload.delivery_body)
        self.assertIn("Source: Financial Times (https://example.com/ft/ecb)", payload.delivery_body)
        self.assertLess(payload.delivery_body.index("Today's weather"), payload.delivery_body.index("External news"))
        self.assertLess(payload.delivery_body.index("External news"), payload.delivery_body.index("In brief"))
        self.assertIn("Open article", payload.delivery_payload["html_body"])
        self.assertEqual(payload.delivery_payload["external_news"][0]["source_name"], "Financial Times")

    def test_localizes_external_news_capsule_in_french(self) -> None:
        renderer = StructuredDigestRenderer(display_timezone="Europe/Paris", digest_language="fr")
        now = datetime(2026, 3, 9, 8, 0, tzinfo=timezone.utc)

        payload = renderer.render(
            run_id="run-news-fr",
            generated_at=now,
            window_start=datetime(2026, 3, 8, 8, 0, tzinfo=timezone.utc),
            window_end=now,
            delivery_mode="json",
            prioritized_items=(),
            external_news=(
                ExternalNewsItem(
                    headline="Les marchés attendent la BCE",
                    summary="Les investisseurs ajustent leurs scénarios avant la prochaine réunion.",
                    source_name="Les Echos",
                    source_url="https://example.com/echos/bce",
                ),
            ),
        )

        self.assertIn("Actualités externes", payload.delivery_body)
        self.assertIn("Source: Les Echos (https://example.com/echos/bce)", payload.delivery_body)
        self.assertIn("Ouvrir l'article", payload.delivery_payload["html_body"])

    def test_renders_risk_and_continuity_badges_from_typed_card(self) -> None:
        renderer = StructuredDigestRenderer(display_timezone="Europe/Paris", digest_language="en")
        now = datetime(2026, 3, 10, 8, 0, tzinfo=timezone.utc)

        payload = renderer.render(
            run_id="run-card-badges",
            generated_at=now,
            window_start=datetime(2026, 3, 9, 8, 0, tzinfo=timezone.utc),
            window_end=now,
            delivery_mode="json",
            prioritized_items=(
                DigestEntry(
                    title="Urgent invoice update needed",
                    summary="Worth noting: confirm the bank account immediately.",
                    section_name="watch_items",
                    source_kind="message",
                    source_id="msg-risk",
                    score=1.1,
                    card=DigestCard(
                        is_unread=True,
                        risk_level="high",
                        continuity_state="changed",
                    ),
                ),
            ),
        )

        self.assertIn("[Unread] [Suspicious] [Changed]", payload.delivery_body)
        self.assertIn(">Suspicious<", payload.delivery_payload["html_body"])

    def test_renders_recurring_meeting_badge_when_metadata_supports_it(self) -> None:
        renderer = StructuredDigestRenderer(display_timezone="Europe/Paris", digest_language="fr")
        now = datetime(2026, 3, 10, 8, 0, tzinfo=timezone.utc)

        payload = renderer.render(
            run_id="run-recurring",
            generated_at=now,
            window_start=datetime(2026, 3, 9, 8, 0, tzinfo=timezone.utc),
            window_end=now,
            delivery_mode="json",
            prioritized_items=(
                DigestEntry(
                    title="Point équipe",
                    summary="Demain, 10:00 | Morgan Lee | Teams",
                    section_name="upcoming_meetings",
                    source_kind="meeting",
                    source_id="mtg-weekly",
                    score=1.5,
                    context_metadata={"recurrence_label": "Hebdo"},
                ),
            ),
        )

        self.assertIn("[Hebdo] Point équipe", payload.delivery_body)
        self.assertIn(">Hebdo<", payload.delivery_payload["html_body"])

    def test_renders_daily_presence_section_and_meta_lines(self) -> None:
        renderer = StructuredDigestRenderer(display_timezone="Europe/Paris", digest_language="fr")
        now = datetime(2026, 3, 10, 8, 0, tzinfo=timezone.utc)

        payload = renderer.render(
            run_id="run-presence",
            generated_at=now,
            window_start=datetime(2026, 3, 9, 8, 0, tzinfo=timezone.utc),
            window_end=now,
            delivery_mode="json",
            prioritized_items=(
                DigestEntry(
                    title="Site Horizon",
                    summary="Signal de présence pour la journée : Site Horizon",
                    section_name="daily_presence",
                    source_kind="meeting",
                    source_id="presence-1",
                    score=1.2,
                    recommended_action="Utiliser cet élément comme signal de présence ou de lieu pour la journée.",
                    handling_bucket="daily_presence",
                    confidence_score=92,
                    confidence_label="Élevée",
                    confidence_reason="Cet événement agenda sur la journée ressemble explicitement à un signal de lieu ou de présence.",
                ),
            ),
        )

        self.assertIn("Présence du jour", payload.delivery_body)
        self.assertIn("Site Horizon", payload.delivery_body)
        self.assertIn("À faire:", payload.delivery_body)
        self.assertIn("Confiance: 92 / Élevée", payload.delivery_body)
        self.assertIn("Présence du jour", payload.delivery_payload["html_body"])
        self.assertIn("<strong>À faire:</strong>", payload.delivery_payload["html_body"])
        self.assertIn("<strong>Confiance:</strong>", payload.delivery_payload["html_body"])

    def test_daily_presence_section_keeps_only_source_day_items(self) -> None:
        renderer = StructuredDigestRenderer(display_timezone="Europe/Paris", digest_language="fr")
        now = datetime(2026, 3, 10, 8, 0, tzinfo=timezone.utc)

        payload = renderer.render(
            run_id="run-presence-filter",
            generated_at=now,
            window_start=datetime(2026, 3, 9, 8, 0, tzinfo=timezone.utc),
            window_end=now,
            delivery_mode="json",
            meeting_horizon={"mode": "two_day_span", "source_date": "2026-03-10", "target_date": "2026-03-11"},
            prioritized_items=(
                DigestEntry(
                    title="Site Horizon",
                    summary="Signal de présence pour la journée : Site Horizon",
                    section_name="daily_presence",
                    source_kind="meeting",
                    source_id="presence-today",
                    score=1.2,
                    sort_at=datetime(2026, 3, 10, 0, 0, tzinfo=timezone.utc),
                ),
                DigestEntry(
                    title="Site Horizon",
                    summary="Signal de présence pour la journée : Site Horizon",
                    section_name="daily_presence",
                    source_kind="meeting",
                    source_id="presence-tomorrow",
                    score=1.2,
                    sort_at=datetime(2026, 3, 11, 0, 0, tzinfo=timezone.utc),
                ),
            ),
        )

        self.assertIn("presence-today", [item.source_id for item in payload.daily_presence])
        self.assertNotIn("presence-tomorrow", [item.source_id for item in payload.daily_presence])


if __name__ == "__main__":
    unittest.main()

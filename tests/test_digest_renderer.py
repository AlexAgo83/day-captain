from datetime import datetime
from datetime import timezone
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from day_captain.models import DigestEntry
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
        self.assertIn("Window:", payload.delivery_body)
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
        self.assertIn("mailto:daycaptain@example.com?subject=recall", payload.delivery_payload["html_body"])
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
        self.assertIn("Périmètre :", payload.delivery_body)
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

        self.assertIn("- Point equipe - Aujourd'hui, 10:00 | Lead | Teams", payload.delivery_body)
        self.assertIn("Point equipe", payload.delivery_payload["html_body"])
        self.assertIn("Aujourd'hui, 10:00 | Lead | Teams", payload.delivery_payload["html_body"])

    def test_bounds_top_summary_to_brief_copy(self) -> None:
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
            "First priority is budget review. Second priority is confirming the launch timing.",
        )
        self.assertNotIn("Third note should not appear", payload.delivery_body)

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
            command_mailbox="daycaptain@company.com",
        )

        self.assertIn("Actions rapides", payload.delivery_body)
        self.assertIn("Rappeler ce brief", payload.delivery_payload["html_body"])
        self.assertIn("subject=recall-week", payload.delivery_payload["html_body"])


if __name__ == "__main__":
    unittest.main()

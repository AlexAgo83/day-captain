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
        self.assertIn("Prepared for you", payload.delivery_body)
        self.assertIn("Covering updates from", payload.delivery_body)
        self.assertIn("Sat 07 Mar 2026 at 09:00 CET", payload.delivery_body)
        self.assertEqual(payload.delivery_subject, "Your Day Captain brief for Sat 07 Mar")
        self.assertEqual(payload.top_summary, "Budget review is the main priority this morning.")
        self.assertEqual(payload.delivery_payload["top_summary_source"], "llm")
        self.assertIn("graph_message", payload.delivery_payload)
        self.assertEqual(payload.delivery_payload["graph_message"]["subject"], payload.delivery_subject)
        self.assertEqual(payload.delivery_payload["graph_message"]["body"]["contentType"], "HTML")
        self.assertIn("<html>", payload.delivery_payload["html_body"])
        self.assertIn("In brief", payload.delivery_payload["html_body"])
        self.assertIn("No meetings are on deck for today.", payload.delivery_body)

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
        self.assertIn("Préparé pour vous le", payload.delivery_body)
        self.assertIn("Points critiques", payload.delivery_body)
        self.assertIn("Aperçu des réunions de lundi.", payload.delivery_body)
        self.assertEqual(payload.delivery_subject, "Votre brief Day Captain du dim. 08 mars")


if __name__ == "__main__":
    unittest.main()

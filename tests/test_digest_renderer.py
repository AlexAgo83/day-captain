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
        renderer = StructuredDigestRenderer()
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
        )

        self.assertIn("Critical topics", payload.delivery_body)
        self.assertEqual(payload.delivery_subject, "Day Captain digest for 2026-03-07")
        self.assertIn("graph_message", payload.delivery_payload)
        self.assertEqual(payload.delivery_payload["graph_message"]["subject"], payload.delivery_subject)


if __name__ == "__main__":
    unittest.main()

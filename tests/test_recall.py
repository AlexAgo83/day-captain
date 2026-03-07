from datetime import datetime
from datetime import timezone
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from day_captain.models import DigestEntry
from day_captain.models import DigestPayload
from day_captain.models import DigestRunRecord
from day_captain.services import SnapshotRecallProvider


class SnapshotRecallProviderTest(unittest.TestCase):
    def test_rehydrates_delivery_body_when_missing(self) -> None:
        now = datetime(2026, 3, 7, 8, 0, tzinfo=timezone.utc)
        payload = DigestPayload(
            run_id="run-1",
            generated_at=now,
            window_start=datetime(2026, 3, 6, 8, 0, tzinfo=timezone.utc),
            window_end=now,
            delivery_mode="json",
            critical_topics=(
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
        run = DigestRunRecord(
            run_id="run-1",
            run_type="morning_digest",
            status="completed",
            generated_at=now,
            window_start=payload.window_start,
            window_end=payload.window_end,
            delivery_mode="json",
            summary=payload,
        )

        recalled = SnapshotRecallProvider().build_recall(run)

        self.assertIn("Critical topics", recalled.delivery_body)
        self.assertEqual(recalled.critical_topics[0].source_id, "msg-1")


if __name__ == "__main__":
    unittest.main()

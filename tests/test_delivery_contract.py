from datetime import datetime
from datetime import timezone
from pathlib import Path
import sys
import tempfile
import unittest
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from day_captain.adapters.storage import SQLiteStorage
from day_captain.app import StaticCalendarCollector
from day_captain.app import StaticMailCollector
from day_captain.app import StubAuthProvider
from day_captain.app import build_application
from day_captain.config import DayCaptainSettings
from day_captain.models import MessageRecord


class DeliveryContractTest(unittest.TestCase):
    def test_graph_send_mode_exposes_mail_payload_and_triggers_delivery(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            path = str(Path(tmpdir) / "day_captain.sqlite3")
            delivery = mock.Mock()
            app = build_application(
                settings=DayCaptainSettings(
                    sqlite_path=path,
                    delivery_mode="graph_send",
                    graph_send_enabled=True,
                    graph_scopes=("User.Read", "Mail.Read", "Mail.Send"),
                ),
                storage=SQLiteStorage(path),
                auth_provider=StubAuthProvider(),
                digest_delivery=delivery,
                mail_collector=StaticMailCollector(
                    [
                        MessageRecord(
                            graph_message_id="msg-1",
                            thread_id="thread-1",
                            subject="Urgent budget review",
                            from_address="boss@example.com",
                            to_addresses=("alex@example.com",),
                            received_at=datetime(2026, 3, 7, 7, 50, tzinfo=timezone.utc),
                            body_preview="Please review before noon.",
                        ),
                    ]
                ),
                calendar_collector=StaticCalendarCollector(()),
            )

            payload = app.run_morning_digest(now=datetime(2026, 3, 7, 8, 0, tzinfo=timezone.utc), force=True)

            self.assertEqual(payload.delivery_mode, "graph_send")
            self.assertIn("graph_message", payload.delivery_payload)
            self.assertEqual(payload.delivery_payload["graph_message"]["subject"], payload.delivery_subject)
            delivery.deliver_digest.assert_called_once()


if __name__ == "__main__":
    unittest.main()

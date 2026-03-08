from datetime import datetime
from datetime import timezone
from pathlib import Path
import sqlite3
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from day_captain.adapters.storage import SQLiteStorage
from day_captain.models import DigestEntry
from day_captain.models import DigestPayload
from day_captain.models import DigestRunRecord
from day_captain.models import FeedbackRecord
from day_captain.models import MessageRecord
from day_captain.models import UserPreference


class SQLiteStorageTest(unittest.TestCase):
    def test_upsert_messages_is_idempotent(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            path = str(Path(tmpdir) / "day_captain.sqlite3")
            storage = SQLiteStorage(path)
            message = MessageRecord(
                graph_message_id="msg-1",
                thread_id="thread-1",
                internet_message_id="<msg-1@example.com>",
                subject="Urgent budget review",
                from_address="boss@example.com",
                received_at=datetime(2026, 3, 7, 7, 30, tzinfo=timezone.utc),
            )

            storage.upsert_messages((message,))
            storage.upsert_messages((message,))

            with sqlite3.connect(path) as connection:
                count = connection.execute("SELECT COUNT(*) FROM scoped_messages").fetchone()[0]

            self.assertEqual(count, 1)

    def test_save_run_persists_summary_and_digest_items(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            path = str(Path(tmpdir) / "day_captain.sqlite3")
            storage = SQLiteStorage(path)
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
                        summary="Please review before noon.",
                        section_name="critical_topics",
                        source_kind="message",
                        source_id="msg-1",
                        score=2.0,
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

            storage.save_run(run)
            loaded = storage.get_run("run-1")

            self.assertIsNotNone(loaded)
            self.assertEqual(loaded.summary.critical_topics[0].source_id, "msg-1")
            with sqlite3.connect(path) as connection:
                item_count = connection.execute("SELECT COUNT(*) FROM scoped_digest_items").fetchone()[0]

            self.assertEqual(item_count, 1)

    def test_feedback_is_persisted(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            path = str(Path(tmpdir) / "day_captain.sqlite3")
            storage = SQLiteStorage(path)
            feedback = FeedbackRecord(
                feedback_id="feedback-1",
                run_id="run-1",
                source_kind="message",
                source_id="msg-1",
                signal_type="useful",
                signal_value="true",
                recorded_at=datetime(2026, 3, 7, 8, 15, tzinfo=timezone.utc),
            )

            storage.save_feedback(feedback)

            saved = storage.list_feedback("run-1")
            self.assertEqual(len(saved), 1)
            self.assertEqual(saved[0].feedback_id, "feedback-1")

    def test_upsert_preferences_updates_existing_weight(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            path = str(Path(tmpdir) / "day_captain.sqlite3")
            storage = SQLiteStorage(path)
            now = datetime(2026, 3, 7, 8, 15, tzinfo=timezone.utc)

            storage.upsert_preferences(
                (
                    UserPreference(
                        preference_key="sender:boss@example.com",
                        preference_type="sender",
                        weight=1.0,
                        source="seed",
                        updated_at=now,
                    ),
                )
            )
            storage.upsert_preferences(
                (
                    UserPreference(
                        preference_key="sender:boss@example.com",
                        preference_type="sender",
                        weight=2.0,
                        source="feedback",
                        updated_at=now,
                    ),
                )
            )

            loaded = storage.load_preferences()
            self.assertEqual(len(loaded), 1)
            self.assertEqual(loaded[0].weight, 2.0)

    def test_storage_isolates_same_message_id_across_users(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            path = str(Path(tmpdir) / "day_captain.sqlite3")
            storage = SQLiteStorage(path)
            shared_id = "msg-1"

            storage.upsert_messages(
                (
                    MessageRecord(
                        graph_message_id=shared_id,
                        thread_id="thread-a",
                        internet_message_id="<a@example.com>",
                        subject="Digest for Alice",
                        from_address="boss@example.com",
                        received_at=datetime(2026, 3, 7, 7, 30, tzinfo=timezone.utc),
                    ),
                ),
                tenant_id="tenant-1",
                user_id="alice@example.com",
            )
            storage.upsert_messages(
                (
                    MessageRecord(
                        graph_message_id=shared_id,
                        thread_id="thread-b",
                        internet_message_id="<b@example.com>",
                        subject="Digest for Bob",
                        from_address="pm@example.com",
                        received_at=datetime(2026, 3, 7, 7, 35, tzinfo=timezone.utc),
                    ),
                ),
                tenant_id="tenant-1",
                user_id="bob@example.com",
            )

            alice_message = storage.get_message(shared_id, tenant_id="tenant-1", user_id="alice@example.com")
            bob_message = storage.get_message(shared_id, tenant_id="tenant-1", user_id="bob@example.com")

            self.assertEqual(alice_message.subject, "Digest for Alice")
            self.assertEqual(bob_message.subject, "Digest for Bob")


if __name__ == "__main__":
    unittest.main()

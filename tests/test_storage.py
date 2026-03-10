from datetime import datetime
from datetime import timezone
from pathlib import Path
import json
import sqlite3
import sys
import tempfile
import unittest
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from day_captain.adapters.storage import PostgresStorage
from day_captain.adapters.storage import SQLiteStorage
from day_captain.models import DigestEntry
from day_captain.models import DigestPayload
from day_captain.models import DigestRunRecord
from day_captain.models import FeedbackRecord
from day_captain.models import MessageRecord
from day_captain.models import UserPreference
from day_captain.models import WeatherSnapshot
from day_captain.models import to_jsonable


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
                weather=WeatherSnapshot(
                    forecast_date=now.date(),
                    weather_code=61,
                    temperature_max_c=13.4,
                    temperature_min_c=6.1,
                    location_name="Paris",
                    previous_temperature_max_c=11.0,
                ),
                critical_topics=(
                    DigestEntry(
                        title="Urgent budget review",
                        summary="Please review before noon.",
                        section_name="critical_topics",
                        source_kind="message",
                        source_id="msg-1",
                        source_url="https://outlook.office.com/mail/msg-1",
                        desktop_source_url="ms-outlook://mail/msg-1",
                        score=2.0,
                        recommended_action="Review the budget deck and confirm.",
                        handling_bucket="critical_topics",
                        confidence_score=88,
                        confidence_label="High",
                        confidence_reason="The request is explicit.",
                        context_metadata={"message_count": 2},
                        reason_codes=("critical_keyword",),
                        guardrail_applied=True,
                    ),
                ),
                daily_presence=(
                    DigestEntry(
                        title="Site Horizon",
                        summary="Location signal for the day: Site Horizon",
                        section_name="daily_presence",
                        source_kind="meeting",
                        source_id="presence-1",
                        score=1.0,
                        recommended_action="Use this as the day's location or presence signal.",
                        handling_bucket="daily_presence",
                        confidence_score=92,
                        confidence_label="High",
                        confidence_reason="Explicit all-day location entry.",
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
            self.assertEqual(loaded.summary.weather.location_name, "Paris")
            self.assertEqual(loaded.summary.critical_topics[0].source_id, "msg-1")
            self.assertEqual(loaded.summary.critical_topics[0].source_url, "https://outlook.office.com/mail/msg-1")
            self.assertEqual(loaded.summary.critical_topics[0].desktop_source_url, "ms-outlook://mail/msg-1")
            self.assertEqual(loaded.summary.critical_topics[0].recommended_action, "Review the budget deck and confirm.")
            self.assertEqual(loaded.summary.critical_topics[0].confidence_score, 88)
            self.assertEqual(loaded.summary.daily_presence[0].section_name, "daily_presence")
            with sqlite3.connect(path) as connection:
                item_count = connection.execute("SELECT COUNT(*) FROM scoped_digest_items").fetchone()[0]

            self.assertEqual(item_count, 2)

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

    def test_get_latest_completed_run_can_filter_by_run_type(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            path = str(Path(tmpdir) / "day_captain.sqlite3")
            storage = SQLiteStorage(path)
            weekly_time = datetime(2026, 3, 8, 19, 30, tzinfo=timezone.utc)
            morning_time = datetime(2026, 3, 7, 8, 0, tzinfo=timezone.utc)
            weekly_payload = DigestPayload(
                run_id="run-weekly",
                generated_at=weekly_time,
                window_start=datetime(2026, 3, 2, 0, 0, tzinfo=timezone.utc),
                window_end=weekly_time,
                delivery_mode="json",
            )
            morning_payload = DigestPayload(
                run_id="run-morning",
                generated_at=morning_time,
                window_start=datetime(2026, 3, 6, 8, 0, tzinfo=timezone.utc),
                window_end=morning_time,
                delivery_mode="json",
            )
            storage.save_run(
                DigestRunRecord(
                    run_id="run-morning",
                    run_type="morning_digest",
                    status="completed",
                    generated_at=morning_time,
                    window_start=morning_payload.window_start,
                    window_end=morning_payload.window_end,
                    delivery_mode="json",
                    summary=morning_payload,
                )
            )
            storage.save_run(
                DigestRunRecord(
                    run_id="run-weekly",
                    run_type="weekly_digest",
                    status="completed",
                    generated_at=weekly_time,
                    window_start=weekly_payload.window_start,
                    window_end=weekly_payload.window_end,
                    delivery_mode="json",
                    summary=weekly_payload,
                )
            )

            latest_any = storage.get_latest_completed_run()
            latest_morning = storage.get_latest_completed_run(run_type="morning_digest")

            self.assertEqual(latest_any.run_id, "run-weekly")
            self.assertEqual(latest_morning.run_id, "run-morning")

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


class _FakePostgresCursor:
    def __init__(self, rows):
        self._rows = rows

    def fetchall(self):
        return self._rows


class _FakePostgresConnection:
    def __init__(self, rows):
        self._rows = rows

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def execute(self, query, params=()):
        return _FakePostgresCursor(self._rows)


class PostgresStorageTest(unittest.TestCase):
    def test_get_latest_completed_run_for_day_uses_fetched_rows(self) -> None:
        generated_at = datetime(2026, 3, 8, 8, 0, tzinfo=timezone.utc)
        payload = DigestPayload(
            run_id="run-1",
            generated_at=generated_at,
            window_start=datetime(2026, 3, 7, 8, 0, tzinfo=timezone.utc),
            window_end=generated_at,
            delivery_mode="json",
            tenant_id="common",
            user_id="alice@example.com",
        )
        row = {
            "tenant_id": "common",
            "user_id": "alice@example.com",
            "run_id": "run-1",
            "run_type": "morning_digest",
            "status": "completed",
            "generated_at": generated_at.isoformat(),
            "window_start": payload.window_start.isoformat(),
            "window_end": payload.window_end.isoformat(),
            "delivery_mode": "json",
            "summary_json": json.dumps(to_jsonable(payload)),
        }
        storage = PostgresStorage.__new__(PostgresStorage)
        storage.default_tenant_id = "common"
        storage.default_user_id = ""
        storage._scope = PostgresStorage._scope.__get__(storage, PostgresStorage)
        storage._row_to_run = PostgresStorage._row_to_run.__get__(storage, PostgresStorage)
        storage._connect = mock.Mock(return_value=_FakePostgresConnection([row]))

        run = storage.get_latest_completed_run_for_day(
            generated_at.date(),
            tenant_id="common",
            user_id="alice@example.com",
            display_timezone="UTC",
        )

        self.assertIsNotNone(run)
        self.assertEqual(run.run_id, "run-1")


if __name__ == "__main__":
    unittest.main()

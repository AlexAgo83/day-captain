from datetime import datetime
from datetime import timedelta
from datetime import timezone
from pathlib import Path
import sys
import unittest
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from day_captain.app import InMemoryStorage
from day_captain.app import StaticCalendarCollector
from day_captain.app import StaticMailCollector
from day_captain.app import StubAuthProvider
from day_captain.app import build_application
from day_captain.adapters.graph import GraphApiError
from day_captain.config import DayCaptainSettings
from day_captain.models import MeetingRecord
from day_captain.models import MessageRecord
from day_captain.models import UserPreference
from day_captain.models import WeatherSnapshot


class RecordingDigestDelivery:
    def __init__(self) -> None:
        self.calls = []

    def deliver_digest(self, auth_context, payload) -> None:
        self.calls.append((auth_context, payload))


class RaisingDigestDelivery:
    def __init__(self, *exceptions) -> None:
        self.calls = []
        self._exceptions = list(exceptions)

    def deliver_digest(self, auth_context, payload) -> None:
        self.calls.append((auth_context, payload))
        if self._exceptions:
            exc = self._exceptions.pop(0)
            if exc is not None:
                raise exc


class FailOnCompletedRunSaveStorage(InMemoryStorage):
    def __init__(self) -> None:
        super().__init__()
        self._completed_save_attempts = 0

    def save_run(self, run) -> None:
        if run.status == "completed":
            self._completed_save_attempts += 1
            if self._completed_save_attempts >= 1:
                raise RuntimeError("simulated completion save failure")
        super().save_run(run)


class StubWeatherProvider:
    def __init__(self, snapshot=None, error=None) -> None:
        self.snapshot = snapshot
        self.error = error
        self.calls = []

    def get_weather(self, current_time, display_timezone):
        self.calls.append((current_time, display_timezone))
        if self.error is not None:
            raise self.error
        return self.snapshot


class DayCaptainApplicationTest(unittest.TestCase):
    def test_morning_digest_returns_sections_and_persists_run(self) -> None:
        now = datetime(2026, 3, 9, 8, 0, tzinfo=timezone.utc)
        storage = InMemoryStorage(
            preferences=[
                UserPreference(
                    preference_key="sender:boss@example.com",
                    preference_type="sender",
                    weight=2.0,
                    source="seed",
                    updated_at=now,
                )
            ]
        )
        app = build_application(
            settings=DayCaptainSettings(),
            storage=storage,
            mail_collector=StaticMailCollector(
                [
                    MessageRecord(
                        graph_message_id="msg-1",
                        thread_id="thread-1",
                        subject="Urgent budget review",
                        from_address="boss@example.com",
                        received_at=datetime(2026, 3, 9, 7, 30, tzinfo=timezone.utc),
                        body_preview="Please review before noon.",
                    ),
                    MessageRecord(
                        graph_message_id="msg-2",
                        thread_id="thread-2",
                        subject="Action needed on roadmap",
                        from_address="pm@example.com",
                        received_at=datetime(2026, 3, 9, 7, 45, tzinfo=timezone.utc),
                        body_preview="Need your input for planning.",
                    ),
                ]
            ),
            calendar_collector=StaticCalendarCollector(
                [
                    MeetingRecord(
                        graph_event_id="mtg-1",
                        subject="Weekly leadership sync",
                        start_at=datetime(2026, 3, 9, 10, 0, tzinfo=timezone.utc),
                        end_at=datetime(2026, 3, 9, 10, 30, tzinfo=timezone.utc),
                        organizer_address="ceo@example.com",
                    )
                ]
            ),
        )

        payload = app.run_morning_digest(now=now)

        self.assertEqual(payload.delivery_mode, "json")
        self.assertTrue(payload.top_summary)
        self.assertEqual(payload.delivery_payload["top_summary_source"], "deterministic")
        self.assertEqual(len(payload.critical_topics), 1)
        self.assertEqual(payload.critical_topics[0].source_id, "msg-1")
        self.assertEqual(len(payload.actions_to_take), 1)
        self.assertEqual(len(payload.upcoming_meetings), 1)
        self.assertIsNotNone(storage.get_latest_completed_run())

    def test_morning_digest_applies_digest_wording_engine(self) -> None:
        now = datetime(2026, 3, 7, 8, 0, tzinfo=timezone.utc)
        storage = InMemoryStorage()

        app = build_application(
            settings=DayCaptainSettings(),
            storage=storage,
            digest_wording_engine=mock.Mock(
                rewrite=lambda items: tuple(
                    type(item)(
                        title=item.title,
                        summary="Rewritten summary",
                        section_name=item.section_name,
                        source_kind=item.source_kind,
                        source_id=item.source_id,
                        score=item.score,
                        reason_codes=item.reason_codes,
                        guardrail_applied=item.guardrail_applied,
                    )
                    for item in items
                )
            ),
            mail_collector=StaticMailCollector(
                [
                    MessageRecord(
                        graph_message_id="msg-1",
                        thread_id="thread-1",
                        subject="Urgent budget review",
                        from_address="boss@example.com",
                        received_at=datetime(2026, 3, 7, 7, 30, tzinfo=timezone.utc),
                        body_preview="Please review before noon.",
                    ),
                ]
            ),
            calendar_collector=StaticCalendarCollector(()),
        )

        payload = app.run_morning_digest(now=now)

        self.assertEqual(payload.critical_topics[0].summary, "Rewritten summary")
        self.assertTrue(payload.top_summary)

    def test_recall_returns_latest_run_for_day(self) -> None:
        now = datetime(2026, 3, 7, 8, 0, tzinfo=timezone.utc)
        storage = InMemoryStorage()
        app = build_application(settings=DayCaptainSettings(), storage=storage)

        created = app.run_morning_digest(now=now)
        recalled = app.recall_digest(day=now.date())

        self.assertEqual(recalled.run_id, created.run_id)

    def test_recall_returns_run_by_id_without_explicit_target_user(self) -> None:
        now = datetime(2026, 3, 7, 8, 0, tzinfo=timezone.utc)
        storage = InMemoryStorage()
        app = build_application(settings=DayCaptainSettings(), storage=storage)

        created = app.run_morning_digest(now=now)

        recalled = app.recall_digest(run_id=created.run_id)

        self.assertEqual(recalled.run_id, created.run_id)

    def test_recall_uses_display_timezone_for_day_lookup(self) -> None:
        now = datetime(2026, 3, 7, 23, 30, tzinfo=timezone.utc)
        storage = InMemoryStorage()
        app = build_application(
            settings=DayCaptainSettings(display_timezone="Europe/Paris"),
            storage=storage,
        )

        created = app.run_morning_digest(now=now, force=True)

        recalled = app.recall_digest(day=datetime(2026, 3, 8, tzinfo=timezone.utc).date())

        self.assertEqual(recalled.run_id, created.run_id)

    def test_weekend_first_run_uses_friday_start_in_display_timezone(self) -> None:
        now = datetime(2026, 3, 8, 10, 0, tzinfo=timezone.utc)
        storage = InMemoryStorage()
        app = build_application(
            settings=DayCaptainSettings(display_timezone="Europe/Paris"),
            storage=storage,
            mail_collector=StaticMailCollector(()),
            calendar_collector=StaticCalendarCollector(()),
        )

        payload = app.run_morning_digest(now=now, force=False)

        self.assertEqual(payload.window_start, datetime(2026, 3, 5, 23, 0, tzinfo=timezone.utc))

    def test_monday_first_run_uses_friday_start_in_display_timezone(self) -> None:
        now = datetime(2026, 3, 9, 10, 0, tzinfo=timezone.utc)
        storage = InMemoryStorage()
        app = build_application(
            settings=DayCaptainSettings(display_timezone="Europe/Paris"),
            storage=storage,
            mail_collector=StaticMailCollector(()),
            calendar_collector=StaticCalendarCollector(()),
        )

        payload = app.run_morning_digest(now=now, force=False)

        self.assertEqual(payload.window_start, datetime(2026, 3, 5, 23, 0, tzinfo=timezone.utc))

    def test_non_monday_weekday_first_run_keeps_default_lookback(self) -> None:
        now = datetime(2026, 3, 10, 10, 0, tzinfo=timezone.utc)
        storage = InMemoryStorage()
        app = build_application(
            settings=DayCaptainSettings(display_timezone="Europe/Paris"),
            storage=storage,
            mail_collector=StaticMailCollector(()),
            calendar_collector=StaticCalendarCollector(()),
        )

        payload = app.run_morning_digest(now=now, force=False)

        self.assertEqual(payload.window_start, now - timedelta(hours=24))

    def test_morning_digest_includes_weather_capsule_when_provider_returns_snapshot(self) -> None:
        now = datetime(2026, 3, 9, 8, 0, tzinfo=timezone.utc)
        storage = InMemoryStorage()
        weather_provider = StubWeatherProvider(
            snapshot=WeatherSnapshot(
                forecast_date=now.date(),
                weather_code=61,
                temperature_max_c=13.4,
                temperature_min_c=6.1,
                location_name="Paris",
                previous_temperature_max_c=11.0,
            )
        )
        app = build_application(
            settings=DayCaptainSettings(display_timezone="Europe/Paris"),
            storage=storage,
            mail_collector=StaticMailCollector(()),
            calendar_collector=StaticCalendarCollector(()),
            weather_provider=weather_provider,
        )

        payload = app.run_morning_digest(now=now, force=True)

        self.assertIsNotNone(payload.weather)
        self.assertIn("Today's weather", payload.delivery_body)
        self.assertEqual(weather_provider.calls[0][1], "Europe/Paris")

    def test_morning_digest_ignores_weather_provider_failures(self) -> None:
        now = datetime(2026, 3, 9, 8, 0, tzinfo=timezone.utc)
        app = build_application(
            settings=DayCaptainSettings(display_timezone="Europe/Paris"),
            storage=InMemoryStorage(),
            mail_collector=StaticMailCollector(()),
            calendar_collector=StaticCalendarCollector(()),
            weather_provider=StubWeatherProvider(error=ValueError("bad weather")),
        )

        payload = app.run_morning_digest(now=now, force=True)

        self.assertIsNone(payload.weather)
        self.assertNotIn("Today's weather", payload.delivery_body)

    def test_weekend_repeat_run_stays_incremental(self) -> None:
        first_now = datetime(2026, 3, 8, 10, 0, tzinfo=timezone.utc)
        second_now = datetime(2026, 3, 8, 12, 0, tzinfo=timezone.utc)
        storage = InMemoryStorage()
        app = build_application(
            settings=DayCaptainSettings(display_timezone="Europe/Paris"),
            storage=storage,
            mail_collector=StaticMailCollector(()),
            calendar_collector=StaticCalendarCollector(()),
        )

        first_payload = app.run_morning_digest(now=first_now)
        second_payload = app.run_morning_digest(now=second_now)

        self.assertEqual(second_payload.window_start, first_payload.window_end + timedelta(microseconds=1))

    def test_weekly_digest_uses_start_of_local_week(self) -> None:
        now = datetime(2026, 3, 8, 19, 30, tzinfo=timezone.utc)
        storage = InMemoryStorage()
        app = build_application(
            settings=DayCaptainSettings(display_timezone="Europe/Paris"),
            storage=storage,
            mail_collector=StaticMailCollector(()),
            calendar_collector=StaticCalendarCollector(()),
        )

        payload = app.run_weekly_digest(now=now)

        self.assertEqual(payload.window_start, datetime(2026, 3, 1, 23, 0, tzinfo=timezone.utc))
        self.assertEqual(payload.delivery_mode, "json")

    def test_consecutive_runs_do_not_duplicate_boundary_message(self) -> None:
        first_now = datetime(2026, 3, 7, 8, 0, tzinfo=timezone.utc)
        second_now = datetime(2026, 3, 7, 9, 0, tzinfo=timezone.utc)
        boundary_message = MessageRecord(
            graph_message_id="msg-boundary",
            thread_id="thread-boundary",
            subject="Boundary item",
            from_address="boss@example.com",
            received_at=first_now,
            body_preview="Should only appear once.",
        )
        storage = InMemoryStorage()
        app = build_application(
            settings=DayCaptainSettings(),
            storage=storage,
            mail_collector=StaticMailCollector((boundary_message,)),
            calendar_collector=StaticCalendarCollector(()),
        )

        first_payload = app.run_morning_digest(now=first_now, force=True)
        second_payload = app.run_morning_digest(now=second_now)

        self.assertEqual(first_payload.critical_topics[0].source_id, "msg-boundary")
        self.assertFalse(
            any(item.source_id == "msg-boundary" for item in second_payload.critical_topics + second_payload.actions_to_take)
        )

    def test_record_feedback_saves_signal(self) -> None:
        now = datetime(2026, 3, 7, 8, 0, tzinfo=timezone.utc)
        storage = InMemoryStorage()
        app = build_application(settings=DayCaptainSettings(), storage=storage)
        run = app.run_morning_digest(now=now)

        feedback = app.record_feedback(
            run_id=run.run_id,
            source_kind="message",
            source_id="msg-1",
            signal_type="useful",
            signal_value="true",
            recorded_at=now,
        )

        self.assertEqual(feedback.run_id, run.run_id)
        self.assertEqual(len(storage.list_feedback(run.run_id)), 1)

    def test_recall_by_run_id_requires_explicit_target_in_multi_user_setup(self) -> None:
        now = datetime(2026, 3, 7, 8, 0, tzinfo=timezone.utc)
        storage = InMemoryStorage()
        settings = DayCaptainSettings(target_users=("alice@example.com", "bob@example.com"))
        app = build_application(settings=settings, storage=storage)

        bob_run = app.run_morning_digest(now=now, target_user_id="bob@example.com")

        with self.assertRaisesRegex(ValueError, "target_user_id is required for recall-digest"):
            app.recall_digest(run_id=bob_run.run_id)

    def test_record_feedback_requires_explicit_target_in_multi_user_setup(self) -> None:
        now = datetime(2026, 3, 7, 8, 0, tzinfo=timezone.utc)
        storage = InMemoryStorage()
        settings = DayCaptainSettings(target_users=("alice@example.com", "bob@example.com"))
        app = build_application(settings=settings, storage=storage)

        bob_run = app.run_morning_digest(now=now, target_user_id="bob@example.com")

        with self.assertRaisesRegex(ValueError, "target_user_id is required for record-feedback"):
            app.record_feedback(
                run_id=bob_run.run_id,
                source_kind="message",
                source_id="msg-1",
                signal_type="useful",
                signal_value="true",
                recorded_at=now,
            )

    def test_pending_delivery_blocks_followup_morning_digest_retry(self) -> None:
        now = datetime(2026, 3, 7, 8, 0, tzinfo=timezone.utc)
        storage = FailOnCompletedRunSaveStorage()
        delivery = RecordingDigestDelivery()
        app = build_application(
            settings=DayCaptainSettings(
                delivery_mode="graph_send",
                graph_send_enabled=True,
                graph_scopes=("Mail.Read", "Calendars.Read", "Mail.Send"),
            ),
            storage=storage,
            digest_delivery=delivery,
            mail_collector=StaticMailCollector(()),
            calendar_collector=StaticCalendarCollector(()),
        )

        with self.assertRaisesRegex(RuntimeError, "simulated completion save failure"):
            app.run_morning_digest(now=now, force=True)

        self.assertEqual(len(delivery.calls), 1)
        latest_run = storage.get_latest_run(user_id="stub-user")
        self.assertIsNotNone(latest_run)
        self.assertEqual(latest_run.status, "delivery_pending")
        with self.assertRaisesRegex(RuntimeError, "awaiting delivery reconciliation"):
            app.run_morning_digest(now=now.replace(hour=9))
        self.assertEqual(len(delivery.calls), 1)

    def test_pending_email_command_replay_does_not_send_duplicate_reply(self) -> None:
        now = datetime(2026, 3, 9, 8, 0, tzinfo=timezone.utc)
        storage = FailOnCompletedRunSaveStorage()
        delivery = RecordingDigestDelivery()
        app = build_application(
            settings=DayCaptainSettings(
                delivery_mode="graph_send",
                graph_send_enabled=True,
                graph_scopes=("Mail.Read", "Calendars.Read", "Mail.Send"),
                target_users=("alice@example.com",),
                email_command_allowed_senders=("alice@example.com",),
            ),
            storage=storage,
            digest_delivery=delivery,
            mail_collector=StaticMailCollector(()),
            calendar_collector=StaticCalendarCollector(()),
        )

        with self.assertRaisesRegex(RuntimeError, "simulated completion save failure"):
            app.process_email_command_recall(
                command_message_id="cmd-1",
                sender_address="alice@example.com",
                command_text="recall-week",
                now=now,
            )

        self.assertEqual(len(delivery.calls), 1)
        existing = storage.get_email_command("cmd-1", tenant_id="common")
        self.assertIsNotNone(existing)
        with self.assertRaisesRegex(RuntimeError, "awaiting delivery reconciliation"):
            app.process_email_command_recall(
                command_message_id="cmd-1",
                sender_address="alice@example.com",
                command_text="recall-week",
                now=now,
            )
        self.assertEqual(len(delivery.calls), 1)

    def test_pre_send_graph_api_failure_marks_run_failed_and_allows_retry(self) -> None:
        now = datetime(2026, 3, 7, 8, 0, tzinfo=timezone.utc)
        storage = InMemoryStorage()
        delivery = RaisingDigestDelivery(GraphApiError("Graph request failed with 403: denied"), None)
        app = build_application(
            settings=DayCaptainSettings(
                delivery_mode="graph_send",
                graph_send_enabled=True,
                graph_scopes=("Mail.Read", "Calendars.Read", "Mail.Send"),
            ),
            storage=storage,
            digest_delivery=delivery,
            mail_collector=StaticMailCollector(()),
            calendar_collector=StaticCalendarCollector(()),
        )

        with self.assertRaisesRegex(GraphApiError, "403"):
            app.run_morning_digest(now=now, force=True)

        latest_run = storage.get_latest_run(user_id="stub-user")
        self.assertIsNotNone(latest_run)
        self.assertEqual(latest_run.status, "delivery_failed")

        second = app.run_morning_digest(now=now.replace(hour=9), force=True)

        self.assertEqual(second.delivery_mode, "graph_send")
        self.assertEqual(len(delivery.calls), 2)

    def test_uncertain_delivery_failure_stays_pending_and_blocks_retry(self) -> None:
        now = datetime(2026, 3, 7, 8, 0, tzinfo=timezone.utc)
        storage = InMemoryStorage()
        delivery = RaisingDigestDelivery(RuntimeError("network uncertain"))
        app = build_application(
            settings=DayCaptainSettings(
                delivery_mode="graph_send",
                graph_send_enabled=True,
                graph_scopes=("Mail.Read", "Calendars.Read", "Mail.Send"),
            ),
            storage=storage,
            digest_delivery=delivery,
            mail_collector=StaticMailCollector(()),
            calendar_collector=StaticCalendarCollector(()),
        )

        with self.assertRaisesRegex(RuntimeError, "network uncertain"):
            app.run_morning_digest(now=now, force=True)

        latest_run = storage.get_latest_run(user_id="stub-user")
        self.assertIsNotNone(latest_run)
        self.assertEqual(latest_run.status, "delivery_pending")

        with self.assertRaisesRegex(RuntimeError, "awaiting delivery reconciliation"):
            app.run_morning_digest(now=now.replace(hour=9))

    def test_email_command_pre_send_failure_allows_same_command_retry(self) -> None:
        now = datetime(2026, 3, 9, 8, 0, tzinfo=timezone.utc)
        storage = InMemoryStorage()
        delivery = RaisingDigestDelivery(GraphApiError("Graph request failed with 403: denied"), None)
        app = build_application(
            settings=DayCaptainSettings(
                delivery_mode="graph_send",
                graph_send_enabled=True,
                graph_scopes=("Mail.Read", "Calendars.Read", "Mail.Send"),
                target_users=("alice@example.com",),
                email_command_allowed_senders=("alice@example.com",),
            ),
            storage=storage,
            digest_delivery=delivery,
            mail_collector=StaticMailCollector(()),
            calendar_collector=StaticCalendarCollector(()),
        )

        with self.assertRaisesRegex(GraphApiError, "403"):
            app.process_email_command_recall(
                command_message_id="cmd-retry",
                sender_address="alice@example.com",
                command_text="recall-week",
                now=now,
            )

        failed_record = storage.get_email_command("cmd-retry", tenant_id="common")
        self.assertIsNotNone(failed_record)
        failed_run = storage.get_run(failed_record.response_run_id, tenant_id="common", user_id="alice@example.com")
        self.assertIsNotNone(failed_run)
        self.assertEqual(failed_run.status, "delivery_failed")

        recovered = app.process_email_command_recall(
            command_message_id="cmd-retry",
            sender_address="alice@example.com",
            command_text="recall-week",
            now=now,
        )

        self.assertFalse(recovered.deduplicated)
        self.assertEqual(len(delivery.calls), 2)
        updated_record = storage.get_email_command("cmd-retry", tenant_id="common")
        self.assertEqual(updated_record.response_run_id, recovered.payload.run_id)

    def test_build_application_uses_postgres_storage_when_database_url_is_configured(self) -> None:
        settings = DayCaptainSettings(
            database_url="postgresql://user:pass@localhost:5432/day_captain",
        )

        fake_storage = InMemoryStorage()
        with mock.patch("day_captain.app.PostgresStorage", return_value=fake_storage) as postgres_storage:
            app = build_application(settings=settings)

        postgres_storage.assert_called_once_with(
            "postgresql://user:pass@localhost:5432/day_captain?sslmode=prefer",
            default_tenant_id="common",
            default_user_id="",
        )
        self.assertIs(app.storage, fake_storage)

    def test_build_application_uses_database_token_cache_in_hosted_mode(self) -> None:
        settings = DayCaptainSettings(
            environment="production",
            database_url="postgresql://user:pass@localhost:5432/day_captain",
            job_secret="secret",
            graph_client_id="client-id",
            graph_refresh_token="refresh-token",
        )

        fake_storage = InMemoryStorage()
        fake_cache = mock.Mock()
        fake_cache.load.return_value = None
        with mock.patch("day_captain.app.PostgresStorage", return_value=fake_storage), mock.patch(
            "day_captain.app.DatabaseTokenCache", return_value=fake_cache
        ) as database_token_cache:
            build_application(settings=settings)

        database_token_cache.assert_called_once_with(
            "postgresql://user:pass@localhost:5432/day_captain?sslmode=prefer"
        )
        fake_cache.save.assert_called_once()

    def test_build_application_selects_app_only_provider_when_configured(self) -> None:
        settings = DayCaptainSettings(
            environment="production",
            database_url="postgresql://user:pass@localhost:5432/day_captain",
            job_secret="secret",
            graph_auth_mode="app_only",
            graph_client_id="client-id",
            graph_client_secret="client-secret",
            graph_user_id="alex@example.com",
            graph_sender_user_id="daycaptain@example.com",
            graph_scopes=("Mail.Read", "Calendars.Read", "Mail.Send"),
        )

        fake_storage = InMemoryStorage()
        with mock.patch("day_captain.app.PostgresStorage", return_value=fake_storage), mock.patch(
            "day_captain.app.GraphAppOnlyAuthProvider"
        ) as app_only_provider:
            app = build_application(settings=settings)

        app_only_provider.assert_called_once()
        self.assertEqual(app_only_provider.call_args.kwargs["sender_user_id"], "daycaptain@example.com")
        self.assertEqual(app.auth_provider, app_only_provider.return_value)

    def test_morning_digest_requires_explicit_target_when_multiple_users_are_configured(self) -> None:
        app = build_application(
            settings=DayCaptainSettings(
                target_users=("alice@example.com", "bob@example.com"),
            ),
            storage=InMemoryStorage(),
            auth_provider=StubAuthProvider(),
            mail_collector=StaticMailCollector(()),
            calendar_collector=StaticCalendarCollector(()),
        )

        with self.assertRaises(ValueError):
            app.run_morning_digest(now=datetime(2026, 3, 9, 8, 0, tzinfo=timezone.utc))

    def test_morning_digest_is_isolated_per_target_user(self) -> None:
        now = datetime(2026, 3, 9, 8, 0, tzinfo=timezone.utc)
        storage = InMemoryStorage()
        app = build_application(
            settings=DayCaptainSettings(
                target_users=("alice@example.com", "bob@example.com"),
            ),
            storage=storage,
            auth_provider=StubAuthProvider(),
            mail_collector=StaticMailCollector(
                [
                    MessageRecord(
                        graph_message_id="msg-1",
                        thread_id="thread-1",
                        subject="Urgent budget review",
                        from_address="boss@example.com",
                        received_at=datetime(2026, 3, 9, 7, 30, tzinfo=timezone.utc),
                        body_preview="Please review before noon.",
                    ),
                ]
            ),
            calendar_collector=StaticCalendarCollector(()),
        )

        alice_run = app.run_morning_digest(now=now, target_user_id="alice@example.com")
        bob_run = app.run_morning_digest(now=now, target_user_id="bob@example.com", force=True)

        self.assertEqual(alice_run.user_id, "alice@example.com")
        self.assertEqual(bob_run.user_id, "bob@example.com")
        self.assertIsNotNone(
            storage.get_latest_completed_run(tenant_id="common", user_id="alice@example.com")
        )
        self.assertIsNotNone(
            storage.get_latest_completed_run(tenant_id="common", user_id="bob@example.com")
        )

    def test_recall_is_isolated_per_target_user(self) -> None:
        now = datetime(2026, 3, 9, 8, 0, tzinfo=timezone.utc)
        storage = InMemoryStorage()
        app = build_application(
            settings=DayCaptainSettings(
                target_users=("alice@example.com", "bob@example.com"),
            ),
            storage=storage,
            auth_provider=StubAuthProvider(),
            mail_collector=StaticMailCollector(
                [
                    MessageRecord(
                        graph_message_id="msg-1",
                        thread_id="thread-1",
                        subject="Urgent budget review",
                        from_address="boss@example.com",
                        received_at=datetime(2026, 3, 9, 7, 30, tzinfo=timezone.utc),
                        body_preview="Please review before noon.",
                    ),
                ]
            ),
            calendar_collector=StaticCalendarCollector(()),
        )

        alice_run = app.run_morning_digest(now=now, target_user_id="alice@example.com", force=True)
        bob_run = app.run_morning_digest(now=now, target_user_id="bob@example.com", force=True)

        recalled_alice = app.recall_digest(day=now.date(), target_user_id="alice@example.com")
        recalled_bob = app.recall_digest(day=now.date(), target_user_id="bob@example.com")

        self.assertEqual(recalled_alice.run_id, alice_run.run_id)
        self.assertEqual(recalled_bob.run_id, bob_run.run_id)

    def test_build_application_uses_llm_provider_when_configured(self) -> None:
        settings = DayCaptainSettings(
            llm_provider="openai",
            llm_api_key="sk-test",
            llm_model="gpt-5-mini",
            llm_shortlist_limit=3,
            llm_enabled_sections=("critical_topics",),
            llm_style_prompt="Write like my chief of staff.",
            display_timezone="Europe/Paris",
        )

        with mock.patch("day_captain.app.OpenAICompatibleDigestWordingProvider") as provider_cls:
            app = build_application(settings=settings)

        provider_cls.assert_called_once_with(
            api_key="sk-test",
            model="gpt-5-mini",
            base_url="https://api.openai.com/v1",
            timeout_seconds=30,
            max_output_tokens=300,
            temperature=0.2,
            language="en",
            style_prompt="Write like my chief of staff.",
        )
        self.assertEqual(app.digest_wording_engine.shortlist_limit, 3)
        self.assertEqual(app.digest_wording_engine.enabled_sections, ("critical_topics",))
        self.assertEqual(type(app.digest_overview_engine).__name__, "LlmDigestOverviewEngine")
        self.assertEqual(app.digest_renderer.display_timezone, "Europe/Paris")
        self.assertEqual(app.digest_renderer.digest_language, "en")
        self.assertEqual(app.scoring_engine.display_timezone, "Europe/Paris")

    def test_morning_digest_applies_digest_overview_engine(self) -> None:
        now = datetime(2026, 3, 7, 8, 0, tzinfo=timezone.utc)
        storage = InMemoryStorage()
        app = build_application(
            settings=DayCaptainSettings(),
            storage=storage,
            digest_overview_engine=mock.Mock(
                summarize=lambda payload: type("Overview", (), {"summary": "Short top summary.", "source": "llm"})()
            ),
            mail_collector=StaticMailCollector(
                [
                    MessageRecord(
                        graph_message_id="msg-1",
                        thread_id="thread-1",
                        subject="Urgent budget review",
                        from_address="boss@example.com",
                        received_at=datetime(2026, 3, 7, 7, 30, tzinfo=timezone.utc),
                        body_preview="Please review before noon.",
                    ),
                ]
            ),
            calendar_collector=StaticCalendarCollector(()),
        )

        payload = app.run_morning_digest(now=now)

        self.assertEqual(payload.top_summary, "Short top summary.")
        self.assertEqual(payload.delivery_payload["top_summary_source"], "llm")

    def test_weekend_run_falls_back_to_monday_meetings(self) -> None:
        now = datetime(2026, 3, 7, 8, 0, tzinfo=timezone.utc)
        app = build_application(
            settings=DayCaptainSettings(display_timezone="Europe/Paris"),
            storage=InMemoryStorage(),
            auth_provider=StubAuthProvider(),
            mail_collector=StaticMailCollector(()),
            calendar_collector=StaticCalendarCollector(
                (
                    MeetingRecord(
                        graph_event_id="mtg-1",
                        subject="Monday planning",
                        start_at=datetime(2026, 3, 9, 9, 0, tzinfo=timezone.utc),
                        end_at=datetime(2026, 3, 9, 9, 30, tzinfo=timezone.utc),
                        organizer_address="pm@example.com",
                    ),
                )
            ),
        )

        payload = app.run_morning_digest(now=now, force=True)

        self.assertEqual(len(payload.upcoming_meetings), 1)
        self.assertEqual(payload.delivery_payload["meeting_horizon"]["mode"], "weekend_monday")
        self.assertIn("looking ahead to monday.", payload.delivery_body.lower())

    def test_empty_same_day_falls_back_to_next_day_meetings(self) -> None:
        now = datetime(2026, 3, 9, 16, 0, tzinfo=timezone.utc)
        app = build_application(
            settings=DayCaptainSettings(display_timezone="Europe/Paris"),
            storage=InMemoryStorage(),
            auth_provider=StubAuthProvider(),
            mail_collector=StaticMailCollector(()),
            calendar_collector=StaticCalendarCollector(
                (
                    MeetingRecord(
                        graph_event_id="mtg-2",
                        subject="Tomorrow sync",
                        start_at=datetime(2026, 3, 10, 9, 0, tzinfo=timezone.utc),
                        end_at=datetime(2026, 3, 10, 9, 30, tzinfo=timezone.utc),
                        organizer_address="lead@example.com",
                    ),
                )
            ),
        )

        payload = app.run_morning_digest(now=now, force=True)

        self.assertEqual(len(payload.upcoming_meetings), 1)
        self.assertEqual(payload.delivery_payload["meeting_horizon"]["mode"], "next_day")
        self.assertIn("here is tomorrow", payload.delivery_body.lower())

    def test_graph_send_requires_graph_send_enabled(self) -> None:
        now = datetime(2026, 3, 7, 8, 0, tzinfo=timezone.utc)
        app = build_application(
            settings=DayCaptainSettings(
                delivery_mode="graph_send",
                graph_send_enabled=False,
                graph_scopes=("User.Read", "Mail.Read", "Mail.Send"),
            ),
            storage=InMemoryStorage(),
            auth_provider=StubAuthProvider(),
            mail_collector=StaticMailCollector(()),
            calendar_collector=StaticCalendarCollector(()),
        )

        with self.assertRaises(ValueError):
            app.run_morning_digest(now=now, force=True)

    def test_graph_send_requires_mail_send_scope(self) -> None:
        now = datetime(2026, 3, 7, 8, 0, tzinfo=timezone.utc)
        app = build_application(
            settings=DayCaptainSettings(
                delivery_mode="graph_send",
                graph_send_enabled=True,
                graph_scopes=("User.Read", "Mail.Read"),
            ),
            storage=InMemoryStorage(),
            auth_provider=StubAuthProvider(),
            mail_collector=StaticMailCollector(()),
            calendar_collector=StaticCalendarCollector(()),
        )

        with self.assertRaises(ValueError):
            app.run_morning_digest(now=now, force=True)

    def test_graph_send_rejects_dedicated_sender_without_app_only_auth(self) -> None:
        now = datetime(2026, 3, 7, 8, 0, tzinfo=timezone.utc)
        app = build_application(
            settings=DayCaptainSettings(
                delivery_mode="graph_send",
                graph_send_enabled=True,
                graph_sender_user_id="daycaptain@example.com",
                graph_scopes=("User.Read", "Mail.Read", "Mail.Send"),
            ),
            storage=InMemoryStorage(),
            auth_provider=StubAuthProvider(),
            mail_collector=StaticMailCollector(()),
            calendar_collector=StaticCalendarCollector(()),
        )

        with self.assertRaises(ValueError):
            app.run_morning_digest(now=now, force=True)

    def test_email_command_recall_generates_today_digest_and_deduplicates(self) -> None:
        now = datetime(2026, 3, 11, 10, 0, tzinfo=timezone.utc)
        delivery = mock.Mock()
        app = build_application(
            settings=DayCaptainSettings(
                graph_send_enabled=True,
                graph_scopes=("User.Read", "Mail.Read", "Mail.Send"),
                target_users=("alice@example.com",),
            ),
            storage=InMemoryStorage(),
            auth_provider=StubAuthProvider(),
            digest_delivery=delivery,
            mail_collector=StaticMailCollector(
                [
                    MessageRecord(
                        graph_message_id="msg-1",
                        thread_id="thread-1",
                        subject="Today item",
                        from_address="boss@example.com",
                        received_at=datetime(2026, 3, 11, 8, 0, tzinfo=timezone.utc),
                        body_preview="Needs action.",
                    ),
                ]
            ),
            calendar_collector=StaticCalendarCollector(()),
        )

        first = app.process_email_command_recall(
            command_message_id="cmd-1",
            sender_address="alice@example.com",
            subject="recall",
            now=now,
        )
        second = app.process_email_command_recall(
            command_message_id="cmd-1",
            sender_address="alice@example.com",
            subject="recall",
            now=now,
        )

        self.assertFalse(first.deduplicated)
        self.assertTrue(second.deduplicated)
        self.assertEqual(first.payload.run_id, second.payload.run_id)
        delivery.deliver_digest.assert_called_once()

    def test_email_command_recall_week_uses_start_of_local_week(self) -> None:
        now = datetime(2026, 3, 11, 10, 0, tzinfo=timezone.utc)
        delivery = mock.Mock()
        app = build_application(
            settings=DayCaptainSettings(
                display_timezone="Europe/Paris",
                graph_send_enabled=True,
                graph_scopes=("User.Read", "Mail.Read", "Mail.Send"),
                target_users=("alice@example.com",),
            ),
            storage=InMemoryStorage(),
            auth_provider=StubAuthProvider(),
            digest_delivery=delivery,
            mail_collector=StaticMailCollector(()),
            calendar_collector=StaticCalendarCollector(()),
        )

        result = app.process_email_command_recall(
            command_message_id="cmd-week",
            sender_address="alice@example.com",
            subject="recall-week",
            now=now,
        )

        self.assertEqual(result.payload.window_start, datetime(2026, 3, 8, 23, 0, tzinfo=timezone.utc))
        delivery.deliver_digest.assert_called_once()

    def test_email_command_recall_allows_single_target_via_explicit_allowlist(self) -> None:
        now = datetime(2026, 3, 11, 10, 0, tzinfo=timezone.utc)
        delivery = mock.Mock()
        app = build_application(
            settings=DayCaptainSettings(
                graph_send_enabled=True,
                graph_scopes=("User.Read", "Mail.Read", "Mail.Send"),
                target_users=("alice@example.com",),
                email_command_allowed_senders=("assistant@example.com",),
            ),
            storage=InMemoryStorage(),
            auth_provider=StubAuthProvider(),
            digest_delivery=delivery,
            mail_collector=StaticMailCollector(()),
            calendar_collector=StaticCalendarCollector(()),
        )

        result = app.process_email_command_recall(
            command_message_id="cmd-allow",
            sender_address="assistant@example.com",
            subject="recall-today",
            now=now,
        )

        self.assertEqual(result.target_user_id, "alice@example.com")


if __name__ == "__main__":
    unittest.main()

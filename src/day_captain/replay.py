"""Identity-free deterministic digest replay."""

from datetime import datetime, timedelta, timezone
from typing import Sequence

from day_captain.app import InMemoryStorage, StaticCalendarCollector, StaticMailCollector, build_application
from day_captain.config import DayCaptainSettings
from day_captain.models import DigestPayload, MeetingRecord, MessageRecord


def run_synthetic_replay() -> Sequence[DigestPayload]:
    now = datetime(2026, 7, 13, 8, 0, tzinfo=timezone.utc)
    messages = (
        MessageRecord("auth-1", "auth-thread", "Your one-time code", "identity@example.test", received_at=now, body_preview="Verification code 123456."),
        MessageRecord("noise-1", "noise-thread", "Weekly entertainment newsletter", "news@example.test", received_at=now, body_preview="Manage preferences and unsubscribe."),
        MessageRecord("action-1", "action-thread", "Roadmap decision", "lead@example.test", to_addresses=("user@example.test",), user_id="user@example.test", received_at=now, body_preview="Please confirm the selected option before noon."),
        MessageRecord("alert-1", "alert-thread", "Payment failed", "noreply@example.test", to_addresses=("user@example.test",), user_id="user@example.test", received_at=now, body_preview="Payment failed; service suspension is pending."),
    )
    meetings = (
        MeetingRecord("meeting-1", "Customer review", now + timedelta(hours=1), now + timedelta(hours=2), "customer@example.test"),
        MeetingRecord("meeting-2", "Project review", now + timedelta(hours=1, minutes=30), now + timedelta(hours=2, minutes=30), "lead@example.test"),
    )
    storage = InMemoryStorage()
    app = build_application(
        settings=DayCaptainSettings(graph_user_id="user@example.test"),
        storage=storage,
        mail_collector=StaticMailCollector(messages),
        calendar_collector=StaticCalendarCollector(meetings),
    )
    first = app.run_morning_digest(now=now, delivery_mode="json", force=True)
    second = app.run_morning_digest(now=now + timedelta(hours=1), delivery_mode="json", force=True)
    return (first, second)

"""Domain models for Day Captain."""

from dataclasses import asdict
from dataclasses import dataclass
from dataclasses import field
from datetime import date
from datetime import datetime
from typing import Any
from typing import Sequence


@dataclass(frozen=True)
class AuthContext:
    access_token: str
    granted_scopes: Sequence[str]
    user_id: str


@dataclass(frozen=True)
class UserPreference:
    preference_key: str
    preference_type: str
    weight: float
    source: str
    updated_at: datetime


@dataclass(frozen=True)
class MessageRecord:
    graph_message_id: str
    thread_id: str
    subject: str
    from_address: str
    to_addresses: Sequence[str] = field(default_factory=tuple)
    cc_addresses: Sequence[str] = field(default_factory=tuple)
    received_at: datetime = field(default_factory=datetime.utcnow)
    body_preview: str = ""
    categories: Sequence[str] = field(default_factory=tuple)
    is_unread: bool = True
    has_attachments: bool = False


@dataclass(frozen=True)
class MeetingRecord:
    graph_event_id: str
    subject: str
    start_at: datetime
    end_at: datetime
    organizer_address: str
    attendees: Sequence[str] = field(default_factory=tuple)
    location: str = ""
    join_url: str = ""
    body_preview: str = ""
    is_online_meeting: bool = True


@dataclass(frozen=True)
class DigestEntry:
    title: str
    summary: str
    source_kind: str
    source_id: str
    score: float
    reason_codes: Sequence[str] = field(default_factory=tuple)
    guardrail_applied: bool = False


@dataclass(frozen=True)
class DigestPayload:
    run_id: str
    generated_at: datetime
    window_start: datetime
    window_end: datetime
    delivery_mode: str
    critical_topics: Sequence[DigestEntry] = field(default_factory=tuple)
    actions_to_take: Sequence[DigestEntry] = field(default_factory=tuple)
    watch_items: Sequence[DigestEntry] = field(default_factory=tuple)
    upcoming_meetings: Sequence[DigestEntry] = field(default_factory=tuple)


@dataclass(frozen=True)
class DigestRunRecord:
    run_id: str
    run_type: str
    status: str
    generated_at: datetime
    window_start: datetime
    window_end: datetime
    delivery_mode: str
    summary: DigestPayload


@dataclass(frozen=True)
class FeedbackRecord:
    feedback_id: str
    run_id: str
    source_kind: str
    source_id: str
    signal_type: str
    signal_value: str
    recorded_at: datetime


def _serialize(value: Any) -> Any:
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, date):
        return value.isoformat()
    if isinstance(value, dict):
        return {key: _serialize(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_serialize(item) for item in value]
    return value


def to_jsonable(value: Any) -> Any:
    if hasattr(value, "__dataclass_fields__"):
        return _serialize(asdict(value))
    if isinstance(value, dict):
        return {key: to_jsonable(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [to_jsonable(item) for item in value]
    return _serialize(value)

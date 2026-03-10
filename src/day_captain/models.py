"""Domain models for Day Captain."""

from dataclasses import asdict
from dataclasses import dataclass
from dataclasses import field
from datetime import date
from datetime import datetime
from typing import Any
from typing import Mapping
from typing import Optional
from typing import Sequence


@dataclass(frozen=True)
class AuthContext:
    access_token: str
    granted_scopes: Sequence[str]
    user_id: str
    tenant_id: str = ""
    auth_mode: str = "delegated"
    graph_root_path: str = "/me"
    sender_user_id: str = ""
    sender_graph_root_path: str = "/me"


@dataclass(frozen=True)
class AuthTokenBundle:
    access_token: str
    refresh_token: str
    expires_at: datetime
    scopes: Sequence[str]
    token_type: str = "Bearer"
    user_id: str = ""


@dataclass(frozen=True)
class DeviceCodeSession:
    device_code: str
    user_code: str
    verification_uri: str
    expires_in: int
    interval: int
    message: str


@dataclass(frozen=True)
class UserPreference:
    preference_key: str
    preference_type: str
    weight: float
    source: str
    updated_at: datetime
    tenant_id: str = ""
    user_id: str = ""


@dataclass(frozen=True)
class MessageRecord:
    graph_message_id: str
    thread_id: str
    subject: str
    from_address: str
    internet_message_id: str = ""
    to_addresses: Sequence[str] = field(default_factory=tuple)
    cc_addresses: Sequence[str] = field(default_factory=tuple)
    received_at: datetime = field(default_factory=datetime.utcnow)
    body_preview: str = ""
    categories: Sequence[str] = field(default_factory=tuple)
    is_unread: bool = True
    has_attachments: bool = False
    raw_payload: Mapping[str, Any] = field(default_factory=dict)
    tenant_id: str = ""
    user_id: str = ""


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
    raw_payload: Mapping[str, Any] = field(default_factory=dict)
    tenant_id: str = ""
    user_id: str = ""


@dataclass(frozen=True)
class DigestEntry:
    title: str
    summary: str
    section_name: str
    source_kind: str
    source_id: str
    score: float
    recommended_action: str = ""
    handling_bucket: str = ""
    confidence_score: int = 0
    confidence_label: str = ""
    confidence_reason: str = ""
    context_metadata: Mapping[str, Any] = field(default_factory=dict)
    source_url: str = ""
    desktop_source_url: str = ""
    sort_at: Optional[datetime] = None
    reason_codes: Sequence[str] = field(default_factory=tuple)
    guardrail_applied: bool = False


@dataclass(frozen=True)
class WeatherSnapshot:
    forecast_date: date
    weather_code: int
    temperature_max_c: float
    temperature_min_c: float
    location_name: str = ""
    previous_temperature_max_c: Optional[float] = None


@dataclass(frozen=True)
class DigestPayload:
    run_id: str
    generated_at: datetime
    window_start: datetime
    window_end: datetime
    delivery_mode: str
    tenant_id: str = ""
    user_id: str = ""
    delivery_subject: str = ""
    delivery_body: str = ""
    top_summary: str = ""
    weather: Optional[WeatherSnapshot] = None
    delivery_payload: Mapping[str, Any] = field(default_factory=dict)
    critical_topics: Sequence[DigestEntry] = field(default_factory=tuple)
    actions_to_take: Sequence[DigestEntry] = field(default_factory=tuple)
    watch_items: Sequence[DigestEntry] = field(default_factory=tuple)
    daily_presence: Sequence[DigestEntry] = field(default_factory=tuple)
    upcoming_meetings: Sequence[DigestEntry] = field(default_factory=tuple)


@dataclass(frozen=True)
class DigestOverview:
    summary: str = ""
    source: str = "none"


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
    tenant_id: str = ""
    user_id: str = ""


@dataclass(frozen=True)
class FeedbackRecord:
    feedback_id: str
    run_id: str
    source_kind: str
    source_id: str
    signal_type: str
    signal_value: str
    recorded_at: datetime
    tenant_id: str = ""
    user_id: str = ""


@dataclass(frozen=True)
class EmailCommandRecord:
    command_message_id: str
    normalized_command: str
    sender_address: str
    processed_at: datetime
    response_run_id: str
    tenant_id: str = ""
    user_id: str = ""


@dataclass(frozen=True)
class EmailCommandResult:
    command_message_id: str
    command_name: str
    target_user_id: str
    payload: DigestPayload
    deduplicated: bool = False


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


def parse_datetime(value: str) -> datetime:
    normalized = value.replace("Z", "+00:00")
    return datetime.fromisoformat(normalized)


def digest_entry_from_dict(payload: Mapping[str, Any]) -> DigestEntry:
    return DigestEntry(
        title=str(payload.get("title") or ""),
        summary=str(payload.get("summary") or ""),
        section_name=str(payload.get("section_name") or "watch_items"),
        source_kind=str(payload.get("source_kind") or ""),
        source_id=str(payload.get("source_id") or ""),
        score=float(payload.get("score") or 0.0),
        recommended_action=str(payload.get("recommended_action") or ""),
        handling_bucket=str(payload.get("handling_bucket") or ""),
        confidence_score=int(payload.get("confidence_score") or 0),
        confidence_label=str(payload.get("confidence_label") or ""),
        confidence_reason=str(payload.get("confidence_reason") or ""),
        context_metadata=dict(payload.get("context_metadata") or {}),
        source_url=str(payload.get("source_url") or ""),
        desktop_source_url=str(payload.get("desktop_source_url") or ""),
        sort_at=parse_datetime(str(payload.get("sort_at"))) if payload.get("sort_at") else None,
        reason_codes=tuple(str(item) for item in payload.get("reason_codes") or ()),
        guardrail_applied=bool(payload.get("guardrail_applied")),
    )


def weather_snapshot_from_dict(payload: Mapping[str, Any]) -> WeatherSnapshot:
    previous_temperature_raw = payload.get("previous_temperature_max_c")
    previous_temperature = None if previous_temperature_raw in (None, "") else float(previous_temperature_raw)
    return WeatherSnapshot(
        forecast_date=date.fromisoformat(str(payload.get("forecast_date"))),
        weather_code=int(payload.get("weather_code") or 0),
        temperature_max_c=float(payload.get("temperature_max_c") or 0.0),
        temperature_min_c=float(payload.get("temperature_min_c") or 0.0),
        location_name=str(payload.get("location_name") or ""),
        previous_temperature_max_c=previous_temperature,
    )


def digest_payload_from_dict(payload: Mapping[str, Any]) -> DigestPayload:
    return DigestPayload(
        run_id=str(payload.get("run_id") or ""),
        generated_at=parse_datetime(str(payload.get("generated_at"))),
        window_start=parse_datetime(str(payload.get("window_start"))),
        window_end=parse_datetime(str(payload.get("window_end"))),
        delivery_mode=str(payload.get("delivery_mode") or "json"),
        tenant_id=str(payload.get("tenant_id") or ""),
        user_id=str(payload.get("user_id") or ""),
        delivery_subject=str(payload.get("delivery_subject") or ""),
        delivery_body=str(payload.get("delivery_body") or ""),
        top_summary=str(payload.get("top_summary") or ""),
        weather=weather_snapshot_from_dict(payload["weather"]) if payload.get("weather") else None,
        delivery_payload=dict(payload.get("delivery_payload") or {}),
        critical_topics=tuple(
            digest_entry_from_dict(item) for item in payload.get("critical_topics") or ()
        ),
        actions_to_take=tuple(
            digest_entry_from_dict(item) for item in payload.get("actions_to_take") or ()
        ),
        watch_items=tuple(
            digest_entry_from_dict(item) for item in payload.get("watch_items") or ()
        ),
        daily_presence=tuple(
            digest_entry_from_dict(item) for item in payload.get("daily_presence") or ()
        ),
        upcoming_meetings=tuple(
            digest_entry_from_dict(item) for item in payload.get("upcoming_meetings") or ()
        ),
    )

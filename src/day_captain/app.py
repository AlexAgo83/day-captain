"""Application bootstrap and stub adapters for Day Captain."""

from datetime import date
from datetime import datetime
from datetime import timedelta
from datetime import timezone
import uuid
from typing import Dict
from typing import Iterable
from typing import Optional
from typing import Sequence

from day_captain.adapters.graph import GraphApiClient
from day_captain.adapters.graph import GraphCalendarCollector
from day_captain.adapters.graph import GraphDelegatedAuthProvider
from day_captain.adapters.graph import GraphMailCollector
from day_captain.adapters.storage import SQLiteStorage
from day_captain.config import DayCaptainSettings
from day_captain.models import AuthContext
from day_captain.models import DigestEntry
from day_captain.models import DigestPayload
from day_captain.models import DigestRunRecord
from day_captain.models import FeedbackRecord
from day_captain.models import MeetingRecord
from day_captain.models import MessageRecord
from day_captain.models import UserPreference
from day_captain.ports import AuthProvider
from day_captain.ports import CalendarCollector
from day_captain.ports import DigestRenderer
from day_captain.ports import FeedbackProcessor
from day_captain.ports import MailCollector
from day_captain.ports import RecallProvider
from day_captain.ports import ScoringEngine
from day_captain.ports import Storage


SECTION_NAMES = (
    "critical_topics",
    "actions_to_take",
    "watch_items",
    "upcoming_meetings",
)


def _coerce_datetime(value: Optional[datetime]) -> datetime:
    if value is None:
        return datetime.now(timezone.utc)
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value


def _end_of_day(value: datetime) -> datetime:
    return value.replace(hour=23, minute=59, second=59, microsecond=0)


def _infer_message_reason_codes(message: MessageRecord, preference_weight: float) -> Sequence[str]:
    reasons = ["mail_signal"]
    subject = message.subject.lower()
    if "urgent" in subject or "critical" in subject:
        reasons.append("critical_keyword")
    if "action" in subject or "todo" in subject:
        reasons.append("action_keyword")
    if preference_weight > 0:
        reasons.append("preference_boost")
    if message.has_attachments:
        reasons.append("attachment_present")
    return tuple(reasons)


class StubAuthProvider:
    def authenticate(self, scopes: Sequence[str]) -> AuthContext:
        return AuthContext(
            access_token="stub-access-token",
            granted_scopes=tuple(scopes),
            user_id="stub-user",
        )


class StaticMailCollector:
    def __init__(self, messages: Optional[Iterable[MessageRecord]] = None) -> None:
        self._messages = list(messages or [])

    def collect_messages(
        self,
        auth_context: AuthContext,
        window_start: datetime,
        window_end: datetime,
    ) -> Sequence[MessageRecord]:
        return tuple(
            message
            for message in self._messages
            if window_start <= _coerce_datetime(message.received_at) <= window_end
        )


class StaticCalendarCollector:
    def __init__(self, meetings: Optional[Iterable[MeetingRecord]] = None) -> None:
        self._meetings = list(meetings or [])

    def collect_meetings(
        self,
        auth_context: AuthContext,
        window_start: datetime,
        window_end: datetime,
    ) -> Sequence[MeetingRecord]:
        return tuple(
            meeting
            for meeting in self._meetings
            if window_start <= _coerce_datetime(meeting.start_at) <= window_end
        )


class InMemoryStorage:
    def __init__(
        self,
        preferences: Optional[Iterable[UserPreference]] = None,
    ) -> None:
        self._messages: Dict[str, MessageRecord] = {}
        self._meetings: Dict[str, MeetingRecord] = {}
        self._runs: Dict[str, DigestRunRecord] = {}
        self._feedback: Dict[str, FeedbackRecord] = {}
        self._preferences = list(preferences or [])

    def load_preferences(self) -> Sequence[UserPreference]:
        return tuple(self._preferences)

    def upsert_messages(self, messages: Sequence[MessageRecord]) -> None:
        for message in messages:
            self._messages[message.graph_message_id] = message

    def upsert_meetings(self, meetings: Sequence[MeetingRecord]) -> None:
        for meeting in meetings:
            self._meetings[meeting.graph_event_id] = meeting

    def save_run(self, run: DigestRunRecord) -> None:
        self._runs[run.run_id] = run

    def get_run(self, run_id: str) -> Optional[DigestRunRecord]:
        return self._runs.get(run_id)

    def get_latest_completed_run(self) -> Optional[DigestRunRecord]:
        completed = [run for run in self._runs.values() if run.status == "completed"]
        if not completed:
            return None
        return sorted(completed, key=lambda item: item.generated_at)[-1]

    def get_latest_completed_run_for_day(self, target_day: date) -> Optional[DigestRunRecord]:
        completed = [
            run
            for run in self._runs.values()
            if run.status == "completed" and run.generated_at.date() == target_day
        ]
        if not completed:
            return None
        return sorted(completed, key=lambda item: item.generated_at)[-1]

    def save_feedback(self, feedback: FeedbackRecord) -> None:
        self._feedback[feedback.feedback_id] = feedback

    def list_feedback(self, run_id: Optional[str] = None) -> Sequence[FeedbackRecord]:
        if run_id is None:
            return tuple(self._feedback.values())
        return tuple(item for item in self._feedback.values() if item.run_id == run_id)


class StubScoringEngine:
    def prioritize(
        self,
        messages: Sequence[MessageRecord],
        meetings: Sequence[MeetingRecord],
        preferences: Sequence[UserPreference],
    ) -> Sequence[DigestEntry]:
        preference_weights = {
            preference.preference_key: preference.weight for preference in preferences
        }
        prioritized = []
        for message in messages:
            sender_key = "sender:{0}".format(message.from_address.lower())
            preference_weight = preference_weights.get(sender_key, 0.0)
            subject = message.subject.lower()
            if "urgent" in subject or "critical" in subject:
                section = "critical_topics"
            elif "action" in subject or "todo" in subject:
                section = "actions_to_take"
            else:
                section = "watch_items"
            score = 1.0 + preference_weight
            if section == "critical_topics":
                score += 1.0
            prioritized.append(
                DigestEntry(
                    title=message.subject,
                    summary=message.body_preview or "New message from {0}".format(message.from_address),
                    source_kind="message",
                    source_id=message.graph_message_id,
                    score=score,
                    reason_codes=_infer_message_reason_codes(message, preference_weight),
                    guardrail_applied=section == "critical_topics",
                )
            )
        for meeting in meetings:
            prioritized.append(
                DigestEntry(
                    title=meeting.subject,
                    summary="Meeting at {0}".format(meeting.start_at.isoformat()),
                    source_kind="meeting",
                    source_id=meeting.graph_event_id,
                    score=1.0,
                    reason_codes=("meeting_context",),
                    guardrail_applied=False,
                )
            )
        return tuple(
            sorted(
                prioritized,
                key=lambda item: (-item.score, item.title.lower()),
            )
        )


class StubDigestRenderer:
    def render(
        self,
        run_id: str,
        generated_at: datetime,
        window_start: datetime,
        window_end: datetime,
        delivery_mode: str,
        prioritized_items: Sequence[DigestEntry],
    ) -> DigestPayload:
        sections = {name: [] for name in SECTION_NAMES}
        for item in prioritized_items:
            target_section = "watch_items"
            if item.source_kind == "meeting":
                target_section = "upcoming_meetings"
            elif item.guardrail_applied:
                target_section = "critical_topics"
            elif "action_keyword" in item.reason_codes:
                target_section = "actions_to_take"
            sections[target_section].append(item)
        return DigestPayload(
            run_id=run_id,
            generated_at=generated_at,
            window_start=window_start,
            window_end=window_end,
            delivery_mode=delivery_mode,
            critical_topics=tuple(sections["critical_topics"]),
            actions_to_take=tuple(sections["actions_to_take"]),
            watch_items=tuple(sections["watch_items"]),
            upcoming_meetings=tuple(sections["upcoming_meetings"]),
        )


class DefaultRecallProvider:
    def build_recall(self, run: DigestRunRecord) -> DigestPayload:
        return run.summary


class DefaultFeedbackProcessor:
    def process_feedback(self, storage: Storage, feedback: FeedbackRecord) -> None:
        storage.save_feedback(feedback)


class DayCaptainApplication:
    def __init__(
        self,
        settings: DayCaptainSettings,
        auth_provider: AuthProvider,
        mail_collector: MailCollector,
        calendar_collector: CalendarCollector,
        storage: Storage,
        scoring_engine: ScoringEngine,
        digest_renderer: DigestRenderer,
        recall_provider: RecallProvider,
        feedback_processor: FeedbackProcessor,
    ) -> None:
        self.settings = settings
        self.auth_provider = auth_provider
        self.mail_collector = mail_collector
        self.calendar_collector = calendar_collector
        self.storage = storage
        self.scoring_engine = scoring_engine
        self.digest_renderer = digest_renderer
        self.recall_provider = recall_provider
        self.feedback_processor = feedback_processor

    def run_morning_digest(
        self,
        now: Optional[datetime] = None,
        delivery_mode: Optional[str] = None,
        force: bool = False,
    ) -> DigestPayload:
        current_time = _coerce_datetime(now)
        previous_run = None if force else self.storage.get_latest_completed_run()
        window_start = (
            previous_run.window_end
            if previous_run is not None
            else current_time - timedelta(hours=self.settings.default_lookback_hours)
        )
        window_end = current_time
        meetings_end = _end_of_day(current_time)
        auth_context = self.auth_provider.authenticate(self.settings.graph_scopes)
        messages = self.mail_collector.collect_messages(auth_context, window_start, window_end)
        meetings = self.calendar_collector.collect_meetings(auth_context, current_time, meetings_end)
        self.storage.upsert_messages(messages)
        self.storage.upsert_meetings(meetings)
        preferences = self.storage.load_preferences()
        prioritized_items = self.scoring_engine.prioritize(messages, meetings, preferences)
        selected_delivery_mode = delivery_mode or self.settings.delivery_mode
        run_id = uuid.uuid4().hex
        payload = self.digest_renderer.render(
            run_id=run_id,
            generated_at=current_time,
            window_start=window_start,
            window_end=window_end,
            delivery_mode=selected_delivery_mode,
            prioritized_items=prioritized_items,
        )
        self.storage.save_run(
            DigestRunRecord(
                run_id=run_id,
                run_type="morning_digest",
                status="completed",
                generated_at=current_time,
                window_start=window_start,
                window_end=window_end,
                delivery_mode=selected_delivery_mode,
                summary=payload,
            )
        )
        return payload

    def recall_digest(
        self,
        run_id: Optional[str] = None,
        day: Optional[date] = None,
    ) -> DigestPayload:
        if run_id:
            run = self.storage.get_run(run_id)
        else:
            target_day = day or datetime.now(timezone.utc).date()
            run = self.storage.get_latest_completed_run_for_day(target_day)
        if run is None:
            raise LookupError("No completed digest run found for recall.")
        return self.recall_provider.build_recall(run)

    def record_feedback(
        self,
        run_id: str,
        source_kind: str,
        source_id: str,
        signal_type: str,
        signal_value: str,
        recorded_at: Optional[datetime] = None,
    ) -> FeedbackRecord:
        feedback = FeedbackRecord(
            feedback_id=uuid.uuid4().hex,
            run_id=run_id,
            source_kind=source_kind,
            source_id=source_id,
            signal_type=signal_type,
            signal_value=signal_value,
            recorded_at=_coerce_datetime(recorded_at),
        )
        self.feedback_processor.process_feedback(self.storage, feedback)
        return feedback


def build_application(
    settings: Optional[DayCaptainSettings] = None,
    storage: Optional[Storage] = None,
    auth_provider: Optional[AuthProvider] = None,
    mail_collector: Optional[MailCollector] = None,
    calendar_collector: Optional[CalendarCollector] = None,
    scoring_engine: Optional[ScoringEngine] = None,
    digest_renderer: Optional[DigestRenderer] = None,
    recall_provider: Optional[RecallProvider] = None,
    feedback_processor: Optional[FeedbackProcessor] = None,
) -> DayCaptainApplication:
    resolved_settings = settings or DayCaptainSettings.from_env()
    graph_client = GraphApiClient(
        base_url=resolved_settings.graph_base_url,
        timeout_seconds=resolved_settings.graph_timeout_seconds,
    )
    resolved_storage = storage or SQLiteStorage(resolved_settings.sqlite_path)
    if auth_provider is not None:
        resolved_auth_provider = auth_provider
    elif resolved_settings.graph_access_token:
        resolved_auth_provider = GraphDelegatedAuthProvider(
            access_token=resolved_settings.graph_access_token,
            api_client=graph_client,
            user_id=resolved_settings.graph_user_id,
        )
    else:
        resolved_auth_provider = StubAuthProvider()

    if mail_collector is not None:
        resolved_mail_collector = mail_collector
    elif resolved_settings.graph_access_token:
        resolved_mail_collector = GraphMailCollector(graph_client)
    else:
        resolved_mail_collector = StaticMailCollector()

    if calendar_collector is not None:
        resolved_calendar_collector = calendar_collector
    elif resolved_settings.graph_access_token:
        resolved_calendar_collector = GraphCalendarCollector(graph_client)
    else:
        resolved_calendar_collector = StaticCalendarCollector()

    return DayCaptainApplication(
        settings=resolved_settings,
        auth_provider=resolved_auth_provider,
        mail_collector=resolved_mail_collector,
        calendar_collector=resolved_calendar_collector,
        storage=resolved_storage,
        scoring_engine=scoring_engine or StubScoringEngine(),
        digest_renderer=digest_renderer or StubDigestRenderer(),
        recall_provider=recall_provider or DefaultRecallProvider(),
        feedback_processor=feedback_processor or DefaultFeedbackProcessor(),
    )

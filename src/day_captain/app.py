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
from zoneinfo import ZoneInfo

from day_captain.adapters.auth import DeviceCodeAuthenticator
from day_captain.adapters.auth import DatabaseTokenCache
from day_captain.adapters.auth import FileTokenCache
from day_captain.adapters.graph import GraphApiClient
from day_captain.adapters.graph import GraphCalendarCollector
from day_captain.adapters.graph import GraphDelegatedAuthProvider
from day_captain.adapters.graph import GraphDigestDelivery
from day_captain.adapters.graph import GraphMailCollector
from day_captain.adapters.llm import OpenAICompatibleDigestWordingProvider
from day_captain.adapters.storage import PostgresStorage
from day_captain.adapters.storage import SQLiteStorage
from day_captain.config import DayCaptainSettings
from day_captain.models import AuthContext
from day_captain.models import AuthTokenBundle
from day_captain.models import DigestEntry
from day_captain.models import DigestPayload
from day_captain.models import DigestRunRecord
from day_captain.models import FeedbackRecord
from day_captain.models import MeetingRecord
from day_captain.models import MessageRecord
from day_captain.models import UserPreference
from day_captain.ports import AuthProvider
from day_captain.ports import CalendarCollector
from day_captain.ports import DigestDelivery
from day_captain.ports import DigestOverviewEngine
from day_captain.ports import DigestRenderer
from day_captain.ports import DigestWordingEngine
from day_captain.ports import FeedbackProcessor
from day_captain.ports import MailCollector
from day_captain.ports import RecallProvider
from day_captain.ports import ScoringEngine
from day_captain.ports import Storage
from day_captain.services import DeterministicScoringEngine
from day_captain.services import DeterministicDigestOverviewEngine
from day_captain.services import IdentityDigestWordingEngine
from day_captain.services import LlmDigestOverviewEngine
from day_captain.services import LlmDigestWordingEngine
from day_captain.services import PreferenceFeedbackProcessor
from day_captain.services import SECTION_NAMES
from day_captain.services import SnapshotRecallProvider
from day_captain.services import StructuredDigestRenderer


def _coerce_datetime(value: Optional[datetime]) -> datetime:
    if value is None:
        return datetime.now(timezone.utc)
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value


def _end_of_day(value: datetime) -> datetime:
    return value.replace(hour=23, minute=59, second=59, microsecond=0)


def _display_zone(name: str):
    try:
        return ZoneInfo(name)
    except Exception:
        return timezone.utc


def _end_of_local_day(value: datetime, zone) -> datetime:
    local = value.astimezone(zone)
    return local.replace(hour=23, minute=59, second=59, microsecond=0).astimezone(timezone.utc)


def _full_local_day_window(target_day: date, zone) -> tuple:
    local_start = datetime(
        target_day.year,
        target_day.month,
        target_day.day,
        0,
        0,
        0,
        tzinfo=zone,
    )
    local_end = local_start + timedelta(days=1) - timedelta(seconds=1)
    return local_start.astimezone(timezone.utc), local_end.astimezone(timezone.utc)


def _seed_token_cache_from_settings(cache, settings: DayCaptainSettings) -> None:
    if not settings.graph_refresh_token:
        return
    cached = cache.load()
    if cached is not None:
        return
    expires_at = datetime.now(timezone.utc)
    if settings.graph_access_token:
        expires_at = expires_at + timedelta(minutes=55)
    seed_bundle = AuthTokenBundle(
        access_token=settings.graph_access_token,
        refresh_token=settings.graph_refresh_token,
        expires_at=expires_at,
        scopes=settings.graph_scopes,
        user_id=settings.graph_user_id,
    )
    cache.save(seed_bundle)


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

    def upsert_preferences(self, preferences: Sequence[UserPreference]) -> None:
        by_key = {(item.preference_key, item.preference_type): item for item in self._preferences}
        for preference in preferences:
            by_key[(preference.preference_key, preference.preference_type)] = preference
        self._preferences = list(by_key.values())

    def upsert_messages(self, messages: Sequence[MessageRecord]) -> None:
        for message in messages:
            self._messages[message.graph_message_id] = message

    def upsert_meetings(self, meetings: Sequence[MeetingRecord]) -> None:
        for meeting in meetings:
            self._meetings[meeting.graph_event_id] = meeting

    def get_message(self, graph_message_id: str) -> Optional[MessageRecord]:
        return self._messages.get(graph_message_id)

    def get_meeting(self, graph_event_id: str) -> Optional[MeetingRecord]:
        return self._meetings.get(graph_event_id)

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
    def __init__(self, digest_language: str = "en", display_timezone: str = "UTC") -> None:
        self.digest_language = digest_language
        self.display_timezone = display_timezone

    def prioritize(
        self,
        messages: Sequence[MessageRecord],
        meetings: Sequence[MeetingRecord],
        preferences: Sequence[UserPreference],
        reference_time: Optional[datetime] = None,
    ) -> Sequence[DigestEntry]:
        return DeterministicScoringEngine(
            digest_language=self.digest_language,
            display_timezone=self.display_timezone,
        ).prioritize(
            messages,
            meetings,
            preferences,
            reference_time=reference_time,
        )


class StubDigestRenderer:
    def __init__(self, display_timezone: str = "UTC", digest_language: str = "en") -> None:
        self.display_timezone = display_timezone
        self.digest_language = digest_language

    def render(
        self,
        run_id: str,
        generated_at: datetime,
        window_start: datetime,
        window_end: datetime,
        delivery_mode: str,
        prioritized_items: Sequence[DigestEntry],
        top_summary: str = "",
        top_summary_source: str = "none",
        meeting_horizon: Optional[Dict[str, str]] = None,
    ) -> DigestPayload:
        return StructuredDigestRenderer(
            display_timezone=self.display_timezone,
            digest_language=self.digest_language,
        ).render(
            run_id=run_id,
            generated_at=generated_at,
            window_start=window_start,
            window_end=window_end,
            delivery_mode=delivery_mode,
            prioritized_items=prioritized_items,
            top_summary=top_summary,
            top_summary_source=top_summary_source,
            meeting_horizon=meeting_horizon,
        )


class DefaultRecallProvider:
    def build_recall(self, run: DigestRunRecord) -> DigestPayload:
        return SnapshotRecallProvider().build_recall(run)


class DefaultFeedbackProcessor:
    def process_feedback(self, storage: Storage, feedback: FeedbackRecord) -> None:
        PreferenceFeedbackProcessor().process_feedback(storage, feedback)


class NoopDigestDelivery:
    def deliver_digest(self, auth_context: AuthContext, payload: DigestPayload) -> None:
        return None


def _build_llm_provider(settings: DayCaptainSettings):
    if not settings.llm_is_enabled():
        return None
    provider_name = settings.llm_provider.strip().lower()
    if provider_name not in {"openai", "openai_compatible"}:
        return None
    if not settings.llm_api_key or not settings.llm_model:
        return None
    return OpenAICompatibleDigestWordingProvider(
        api_key=settings.llm_api_key,
        model=settings.llm_model,
        base_url=settings.llm_base_url,
        timeout_seconds=settings.llm_timeout_seconds,
        max_output_tokens=settings.llm_max_output_tokens,
        temperature=settings.llm_temperature,
        language=settings.resolved_llm_language(),
        style_prompt=settings.llm_style_prompt,
    )


def _default_digest_wording_engine(
    settings: DayCaptainSettings,
    provider=None,
) -> DigestWordingEngine:
    provider = provider if provider is not None else _build_llm_provider(settings)
    if provider is None:
        return IdentityDigestWordingEngine()
    return LlmDigestWordingEngine(
        provider=provider,
        shortlist_limit=settings.llm_shortlist_limit,
        enabled_sections=settings.llm_enabled_sections,
    )


def _default_digest_overview_engine(
    settings: DayCaptainSettings,
    provider=None,
) -> DigestOverviewEngine:
    provider = provider if provider is not None else _build_llm_provider(settings)
    if provider is None:
        return DeterministicDigestOverviewEngine()
    return LlmDigestOverviewEngine(provider=provider)


def _validate_graph_send_prerequisites(settings: DayCaptainSettings, auth_context: AuthContext) -> None:
    if not settings.graph_send_enabled:
        raise ValueError("graph_send delivery requires DAY_CAPTAIN_GRAPH_SEND_ENABLED=true.")
    if "Mail.Send" not in auth_context.granted_scopes:
        raise ValueError("graph_send delivery requires Mail.Send in DAY_CAPTAIN_GRAPH_SCOPES and delegated auth.")


class DayCaptainApplication:
    def __init__(
        self,
        settings: DayCaptainSettings,
        auth_provider: AuthProvider,
        mail_collector: MailCollector,
        calendar_collector: CalendarCollector,
        storage: Storage,
        scoring_engine: ScoringEngine,
        digest_wording_engine: DigestWordingEngine,
        digest_overview_engine: DigestOverviewEngine,
        digest_renderer: DigestRenderer,
        digest_delivery: DigestDelivery,
        recall_provider: RecallProvider,
        feedback_processor: FeedbackProcessor,
    ) -> None:
        self.settings = settings
        self.auth_provider = auth_provider
        self.mail_collector = mail_collector
        self.calendar_collector = calendar_collector
        self.storage = storage
        self.scoring_engine = scoring_engine
        self.digest_wording_engine = digest_wording_engine
        self.digest_overview_engine = digest_overview_engine
        self.digest_renderer = digest_renderer
        self.digest_delivery = digest_delivery
        self.recall_provider = recall_provider
        self.feedback_processor = feedback_processor

    def _collect_meetings(
        self,
        auth_context: AuthContext,
        current_time: datetime,
    ) -> tuple[Sequence[MeetingRecord], Dict[str, str]]:
        zone = _display_zone(self.settings.display_timezone)
        local_date = current_time.astimezone(zone).date()
        weekday = local_date.weekday()
        if weekday >= 5:
            target_date = local_date + timedelta(days=7 - weekday)
            window_start, window_end = _full_local_day_window(target_date, zone)
            meetings = self.calendar_collector.collect_meetings(auth_context, window_start, window_end)
            return meetings, {
                "mode": "weekend_monday",
                "target_date": target_date.isoformat(),
                "source_date": local_date.isoformat(),
            }

        meetings_end = _end_of_local_day(current_time, zone)
        meetings = self.calendar_collector.collect_meetings(auth_context, current_time, meetings_end)
        if meetings:
            return meetings, {
                "mode": "same_day",
                "target_date": local_date.isoformat(),
                "source_date": local_date.isoformat(),
            }

        target_date = local_date + timedelta(days=1)
        next_start, next_end = _full_local_day_window(target_date, zone)
        meetings = self.calendar_collector.collect_meetings(auth_context, next_start, next_end)
        return meetings, {
            "mode": "next_day",
            "target_date": target_date.isoformat(),
            "source_date": local_date.isoformat(),
        }

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
        auth_context = self.auth_provider.authenticate(self.settings.graph_scopes)
        messages = self.mail_collector.collect_messages(auth_context, window_start, window_end)
        meetings, meeting_horizon = self._collect_meetings(auth_context, current_time)
        self.storage.upsert_messages(messages)
        self.storage.upsert_meetings(meetings)
        preferences = self.storage.load_preferences()
        prioritized_items = self.scoring_engine.prioritize(
            messages,
            meetings,
            preferences,
            reference_time=current_time,
        )
        prioritized_items = self.digest_wording_engine.rewrite(prioritized_items)
        selected_delivery_mode = delivery_mode or self.settings.delivery_mode
        run_id = uuid.uuid4().hex
        payload = self.digest_renderer.render(
            run_id=run_id,
            generated_at=current_time,
            window_start=window_start,
            window_end=window_end,
            delivery_mode=selected_delivery_mode,
            prioritized_items=prioritized_items,
            meeting_horizon=meeting_horizon,
        )
        overview = self.digest_overview_engine.summarize(payload)
        if overview.summary or overview.source != "none":
            payload = self.digest_renderer.render(
                run_id=run_id,
                generated_at=current_time,
                window_start=window_start,
                window_end=window_end,
                delivery_mode=selected_delivery_mode,
                prioritized_items=prioritized_items,
                top_summary=overview.summary,
                top_summary_source=overview.source,
                meeting_horizon=meeting_horizon,
            )
        if selected_delivery_mode == "graph_send":
            _validate_graph_send_prerequisites(self.settings, auth_context)
            self.digest_delivery.deliver_digest(auth_context, payload)
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
    digest_wording_engine: Optional[DigestWordingEngine] = None,
    digest_overview_engine: Optional[DigestOverviewEngine] = None,
    digest_renderer: Optional[DigestRenderer] = None,
    digest_delivery: Optional[DigestDelivery] = None,
    recall_provider: Optional[RecallProvider] = None,
    feedback_processor: Optional[FeedbackProcessor] = None,
) -> DayCaptainApplication:
    resolved_settings = settings or DayCaptainSettings.from_env()
    resolved_database_url = resolved_settings.resolved_database_url()
    graph_client = GraphApiClient(
        base_url=resolved_settings.graph_base_url,
        timeout_seconds=resolved_settings.graph_timeout_seconds,
    )
    if resolved_settings.is_hosted_environment() and resolved_database_url:
        token_cache = DatabaseTokenCache(resolved_database_url)
        _seed_token_cache_from_settings(token_cache, resolved_settings)
    else:
        token_cache = FileTokenCache(resolved_settings.graph_auth_cache_path)
    authenticator = DeviceCodeAuthenticator(
        tenant_id=resolved_settings.graph_tenant_id,
        client_id=resolved_settings.graph_client_id,
        timeout_seconds=resolved_settings.graph_timeout_seconds,
    )
    if storage is not None:
        resolved_storage = storage
    elif resolved_database_url:
        resolved_storage = PostgresStorage(resolved_database_url)
    else:
        resolved_storage = SQLiteStorage(resolved_settings.sqlite_path)
    if auth_provider is not None:
        resolved_auth_provider = auth_provider
    elif resolved_settings.graph_access_token or resolved_settings.graph_client_id:
        resolved_auth_provider = GraphDelegatedAuthProvider(
            api_client=graph_client,
            access_token=resolved_settings.graph_access_token,
            token_cache=token_cache,
            authenticator=authenticator,
            user_id=resolved_settings.graph_user_id,
        )
    else:
        resolved_auth_provider = StubAuthProvider()

    if mail_collector is not None:
        resolved_mail_collector = mail_collector
    elif resolved_settings.graph_access_token or resolved_settings.graph_client_id:
        resolved_mail_collector = GraphMailCollector(graph_client)
    else:
        resolved_mail_collector = StaticMailCollector()

    if calendar_collector is not None:
        resolved_calendar_collector = calendar_collector
    elif resolved_settings.graph_access_token or resolved_settings.graph_client_id:
        resolved_calendar_collector = GraphCalendarCollector(graph_client)
    else:
        resolved_calendar_collector = StaticCalendarCollector()

    llm_provider = _build_llm_provider(resolved_settings)

    return DayCaptainApplication(
        settings=resolved_settings,
        auth_provider=resolved_auth_provider,
        mail_collector=resolved_mail_collector,
        calendar_collector=resolved_calendar_collector,
        storage=resolved_storage,
        scoring_engine=scoring_engine
        or DeterministicScoringEngine(
            digest_language=resolved_settings.resolved_digest_language(),
            display_timezone=resolved_settings.display_timezone,
        ),
        digest_wording_engine=digest_wording_engine or _default_digest_wording_engine(resolved_settings, provider=llm_provider),
        digest_overview_engine=digest_overview_engine or _default_digest_overview_engine(resolved_settings, provider=llm_provider),
        digest_renderer=digest_renderer
        or StructuredDigestRenderer(
            display_timezone=resolved_settings.display_timezone,
            digest_language=resolved_settings.resolved_digest_language(),
        ),
        digest_delivery=digest_delivery or GraphDigestDelivery(graph_client),
        recall_provider=recall_provider or SnapshotRecallProvider(),
        feedback_processor=feedback_processor or PreferenceFeedbackProcessor(),
    )

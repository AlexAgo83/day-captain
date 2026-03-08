"""Service interfaces for Day Captain."""

from datetime import date
from datetime import datetime
from typing import Mapping
from typing import Optional
from typing import Protocol
from typing import Sequence

from day_captain.models import AuthContext
from day_captain.models import DigestEntry
from day_captain.models import DigestOverview
from day_captain.models import DigestPayload
from day_captain.models import DigestRunRecord
from day_captain.models import FeedbackRecord
from day_captain.models import MeetingRecord
from day_captain.models import MessageRecord
from day_captain.models import UserPreference


class AuthProvider(Protocol):
    def authenticate(
        self,
        scopes: Sequence[str],
        target_user_id: str = "",
        tenant_id: str = "",
    ) -> AuthContext:
        ...


class MailCollector(Protocol):
    def collect_messages(
        self,
        auth_context: AuthContext,
        window_start: datetime,
        window_end: datetime,
    ) -> Sequence[MessageRecord]:
        ...


class CalendarCollector(Protocol):
    def collect_meetings(
        self,
        auth_context: AuthContext,
        window_start: datetime,
        window_end: datetime,
    ) -> Sequence[MeetingRecord]:
        ...


class Storage(Protocol):
    def load_preferences(self, tenant_id: str = "", user_id: str = "") -> Sequence[UserPreference]:
        ...

    def upsert_preferences(
        self,
        preferences: Sequence[UserPreference],
        tenant_id: str = "",
        user_id: str = "",
    ) -> None:
        ...

    def upsert_messages(
        self,
        messages: Sequence[MessageRecord],
        tenant_id: str = "",
        user_id: str = "",
    ) -> None:
        ...

    def upsert_meetings(
        self,
        meetings: Sequence[MeetingRecord],
        tenant_id: str = "",
        user_id: str = "",
    ) -> None:
        ...

    def get_message(
        self,
        graph_message_id: str,
        tenant_id: str = "",
        user_id: str = "",
    ) -> Optional[MessageRecord]:
        ...

    def get_meeting(
        self,
        graph_event_id: str,
        tenant_id: str = "",
        user_id: str = "",
    ) -> Optional[MeetingRecord]:
        ...

    def save_run(self, run: DigestRunRecord) -> None:
        ...

    def get_run(self, run_id: str, tenant_id: str = "", user_id: str = "") -> Optional[DigestRunRecord]:
        ...

    def get_latest_completed_run(self, tenant_id: str = "", user_id: str = "") -> Optional[DigestRunRecord]:
        ...

    def get_latest_completed_run_for_day(
        self,
        target_day: date,
        tenant_id: str = "",
        user_id: str = "",
    ) -> Optional[DigestRunRecord]:
        ...

    def save_feedback(self, feedback: FeedbackRecord, tenant_id: str = "", user_id: str = "") -> None:
        ...


class ScoringEngine(Protocol):
    def prioritize(
        self,
        messages: Sequence[MessageRecord],
        meetings: Sequence[MeetingRecord],
        preferences: Sequence[UserPreference],
        reference_time: Optional[datetime] = None,
    ) -> Sequence[DigestEntry]:
        ...


class DigestRenderer(Protocol):
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
        meeting_horizon: Optional[Mapping[str, str]] = None,
    ) -> DigestPayload:
        ...


class DigestWordingEngine(Protocol):
    def rewrite(
        self,
        prioritized_items: Sequence[DigestEntry],
    ) -> Sequence[DigestEntry]:
        ...


class DigestOverviewEngine(Protocol):
    def summarize(
        self,
        payload: DigestPayload,
    ) -> DigestOverview:
        ...


class DigestDelivery(Protocol):
    def deliver_digest(
        self,
        auth_context: AuthContext,
        payload: DigestPayload,
    ) -> None:
        ...


class RecallProvider(Protocol):
    def build_recall(self, run: DigestRunRecord) -> DigestPayload:
        ...


class FeedbackProcessor(Protocol):
    def process_feedback(self, storage: Storage, feedback: FeedbackRecord) -> None:
        ...

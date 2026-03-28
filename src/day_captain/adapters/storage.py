"""Relational storage adapters for Day Captain."""

from dataclasses import replace
from datetime import date
from datetime import timezone
import json
import sqlite3
from typing import Any
from typing import Mapping
from typing import Optional
from typing import Sequence
from zoneinfo import ZoneInfo

try:
    import psycopg
    from psycopg.rows import dict_row
except ImportError:  # pragma: no cover - exercised only when psycopg isn't installed
    psycopg = None
    dict_row = None

from day_captain.models import DigestPayload
from day_captain.models import DigestRunRecord
from day_captain.models import EmailCommandRecord
from day_captain.models import FeedbackRecord
from day_captain.models import MeetingRecord
from day_captain.models import MessageRecord
from day_captain.models import UserPreference
from day_captain.models import digest_payload_from_dict
from day_captain.models import parse_datetime
from day_captain.models import to_jsonable


SECTION_NAMES = (
    "critical_topics",
    "actions_to_take",
    "watch_items",
    "daily_presence",
    "upcoming_meetings",
)

DEFAULT_TENANT_ID = "default-tenant"
DEFAULT_USER_ID = "default-user"


def _json_dumps(value: Any) -> str:
    return json.dumps(to_jsonable(value), sort_keys=True)


def _json_loads(value: Optional[str]) -> Any:
    if not value:
        return None
    return json.loads(value)


def _normalize_scope_value(value: str, fallback: str) -> str:
    normalized = str(value or "").strip()
    return normalized or fallback


def _display_zone(name: str):
    try:
        return ZoneInfo(name)
    except Exception:
        return timezone.utc


class SQLiteStorage:
    def __init__(
        self,
        path: str,
        default_tenant_id: str = DEFAULT_TENANT_ID,
        default_user_id: str = DEFAULT_USER_ID,
    ) -> None:
        self.path = path
        self.default_tenant_id = _normalize_scope_value(default_tenant_id, DEFAULT_TENANT_ID)
        self.default_user_id = _normalize_scope_value(default_user_id, DEFAULT_USER_ID)
        self._ensure_schema()

    def _scope(self, tenant_id: str = "", user_id: str = "") -> tuple[str, str]:
        return (
            _normalize_scope_value(tenant_id, self.default_tenant_id),
            _normalize_scope_value(user_id, self.default_user_id),
        )

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.path)
        connection.row_factory = sqlite3.Row
        return connection

    def _table_exists(self, connection: sqlite3.Connection, table_name: str) -> bool:
        row = connection.execute(
            "SELECT name FROM sqlite_master WHERE type = 'table' AND name = ?",
            (table_name,),
        ).fetchone()
        return row is not None

    def _table_is_empty(self, connection: sqlite3.Connection, table_name: str) -> bool:
        row = connection.execute("SELECT COUNT(*) AS count FROM {0}".format(table_name)).fetchone()
        return row is not None and int(row["count"]) == 0

    def _ensure_schema(self) -> None:
        with self._connect() as connection:
            connection.executescript(
                """
                PRAGMA foreign_keys = ON;

                CREATE TABLE IF NOT EXISTS scoped_messages (
                    tenant_id TEXT NOT NULL,
                    user_id TEXT NOT NULL,
                    graph_message_id TEXT NOT NULL,
                    thread_id TEXT NOT NULL,
                    internet_message_id TEXT NOT NULL,
                    subject TEXT NOT NULL,
                    from_address TEXT NOT NULL,
                    to_addresses_json TEXT NOT NULL,
                    cc_addresses_json TEXT NOT NULL,
                    received_at TEXT NOT NULL,
                    body_preview TEXT NOT NULL,
                    categories_json TEXT NOT NULL,
                    is_unread INTEGER NOT NULL,
                    has_attachments INTEGER NOT NULL,
                    raw_payload_json TEXT NOT NULL,
                    first_seen_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    last_seen_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    PRIMARY KEY (tenant_id, user_id, graph_message_id)
                );

                CREATE TABLE IF NOT EXISTS scoped_meetings (
                    tenant_id TEXT NOT NULL,
                    user_id TEXT NOT NULL,
                    graph_event_id TEXT NOT NULL,
                    subject TEXT NOT NULL,
                    start_at TEXT NOT NULL,
                    end_at TEXT NOT NULL,
                    organizer_address TEXT NOT NULL,
                    attendees_json TEXT NOT NULL,
                    location TEXT NOT NULL,
                    join_url TEXT NOT NULL,
                    body_preview TEXT NOT NULL,
                    is_online_meeting INTEGER NOT NULL,
                    raw_payload_json TEXT NOT NULL,
                    first_seen_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    last_seen_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    PRIMARY KEY (tenant_id, user_id, graph_event_id)
                );

                CREATE TABLE IF NOT EXISTS scoped_digest_runs (
                    tenant_id TEXT NOT NULL,
                    user_id TEXT NOT NULL,
                    run_id TEXT NOT NULL,
                    run_type TEXT NOT NULL,
                    status TEXT NOT NULL,
                    generated_at TEXT NOT NULL,
                    window_start TEXT NOT NULL,
                    window_end TEXT NOT NULL,
                    delivery_mode TEXT NOT NULL,
                    summary_json TEXT NOT NULL,
                    PRIMARY KEY (tenant_id, user_id, run_id)
                );

                CREATE TABLE IF NOT EXISTS scoped_digest_items (
                    tenant_id TEXT NOT NULL,
                    user_id TEXT NOT NULL,
                    run_id TEXT NOT NULL,
                    item_type TEXT NOT NULL,
                    source_kind TEXT NOT NULL,
                    source_id TEXT NOT NULL,
                    score REAL NOT NULL,
                    reason_codes_json TEXT NOT NULL,
                    guardrail_applied INTEGER NOT NULL,
                    section_name TEXT NOT NULL,
                    rendered_text TEXT NOT NULL,
                    PRIMARY KEY (tenant_id, user_id, run_id, section_name, source_kind, source_id),
                    FOREIGN KEY (tenant_id, user_id, run_id)
                        REFERENCES scoped_digest_runs(tenant_id, user_id, run_id)
                        ON DELETE CASCADE
                );

                CREATE TABLE IF NOT EXISTS scoped_feedback (
                    tenant_id TEXT NOT NULL,
                    user_id TEXT NOT NULL,
                    feedback_id TEXT NOT NULL,
                    run_id TEXT NOT NULL,
                    source_kind TEXT NOT NULL,
                    source_id TEXT NOT NULL,
                    signal_type TEXT NOT NULL,
                    signal_value TEXT NOT NULL,
                    recorded_at TEXT NOT NULL,
                    PRIMARY KEY (tenant_id, user_id, feedback_id)
                );

                CREATE TABLE IF NOT EXISTS scoped_email_commands (
                    tenant_id TEXT NOT NULL,
                    command_message_id TEXT NOT NULL,
                    user_id TEXT NOT NULL,
                    normalized_command TEXT NOT NULL,
                    sender_address TEXT NOT NULL,
                    processed_at TEXT NOT NULL,
                    response_run_id TEXT NOT NULL,
                    PRIMARY KEY (tenant_id, command_message_id)
                );

                CREATE TABLE IF NOT EXISTS scoped_preferences (
                    tenant_id TEXT NOT NULL,
                    user_id TEXT NOT NULL,
                    preference_key TEXT NOT NULL,
                    preference_type TEXT NOT NULL,
                    weight REAL NOT NULL,
                    source TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    PRIMARY KEY (tenant_id, user_id, preference_key, preference_type)
                );
                """
            )
            self._migrate_legacy_data(connection)

    def _migrate_legacy_data(self, connection: sqlite3.Connection) -> None:
        tenant_id, user_id = self._scope()
        migrations = (
            (
                "messages",
                "scoped_messages",
                """
                INSERT INTO scoped_messages (
                    tenant_id,
                    user_id,
                    graph_message_id,
                    thread_id,
                    internet_message_id,
                    subject,
                    from_address,
                    to_addresses_json,
                    cc_addresses_json,
                    received_at,
                    body_preview,
                    categories_json,
                    is_unread,
                    has_attachments,
                    raw_payload_json,
                    first_seen_at,
                    last_seen_at
                )
                SELECT ?, ?, graph_message_id, thread_id, internet_message_id, subject, from_address,
                       to_addresses_json, cc_addresses_json, received_at, body_preview, categories_json,
                       is_unread, has_attachments, raw_payload_json, first_seen_at, last_seen_at
                FROM messages
                """,
            ),
            (
                "meetings",
                "scoped_meetings",
                """
                INSERT INTO scoped_meetings (
                    tenant_id,
                    user_id,
                    graph_event_id,
                    subject,
                    start_at,
                    end_at,
                    organizer_address,
                    attendees_json,
                    location,
                    join_url,
                    body_preview,
                    is_online_meeting,
                    raw_payload_json,
                    first_seen_at,
                    last_seen_at
                )
                SELECT ?, ?, graph_event_id, subject, start_at, end_at, organizer_address, attendees_json,
                       location, join_url, body_preview, is_online_meeting, raw_payload_json, first_seen_at, last_seen_at
                FROM meetings
                """,
            ),
            (
                "digest_runs",
                "scoped_digest_runs",
                """
                INSERT INTO scoped_digest_runs (
                    tenant_id,
                    user_id,
                    run_id,
                    run_type,
                    status,
                    generated_at,
                    window_start,
                    window_end,
                    delivery_mode,
                    summary_json
                )
                SELECT ?, ?, run_id, run_type, status, generated_at, window_start, window_end, delivery_mode, summary_json
                FROM digest_runs
                """,
            ),
            (
                "digest_items",
                "scoped_digest_items",
                """
                INSERT INTO scoped_digest_items (
                    tenant_id,
                    user_id,
                    run_id,
                    item_type,
                    source_kind,
                    source_id,
                    score,
                    reason_codes_json,
                    guardrail_applied,
                    section_name,
                    rendered_text
                )
                SELECT ?, ?, run_id, item_type, source_kind, source_id, score, reason_codes_json,
                       guardrail_applied, section_name, rendered_text
                FROM digest_items
                """,
            ),
            (
                "feedback",
                "scoped_feedback",
                """
                INSERT INTO scoped_feedback (
                    tenant_id,
                    user_id,
                    feedback_id,
                    run_id,
                    source_kind,
                    source_id,
                    signal_type,
                    signal_value,
                    recorded_at
                )
                SELECT ?, ?, feedback_id, run_id, source_kind, source_id, signal_type, signal_value, recorded_at
                FROM feedback
                """,
            ),
            (
                "preferences",
                "scoped_preferences",
                """
                INSERT INTO scoped_preferences (
                    tenant_id,
                    user_id,
                    preference_key,
                    preference_type,
                    weight,
                    source,
                    updated_at
                )
                SELECT ?, ?, preference_key, preference_type, weight, source, updated_at
                FROM preferences
                """,
            ),
        )
        for legacy_name, scoped_name, statement in migrations:
            if not self._table_exists(connection, legacy_name):
                continue
            if not self._table_is_empty(connection, scoped_name):
                continue
            connection.execute(statement, (tenant_id, user_id))

    def load_preferences(self, tenant_id: str = "", user_id: str = "") -> Sequence[UserPreference]:
        with self._connect() as connection:
            if tenant_id or user_id:
                scoped_tenant_id, scoped_user_id = self._scope(tenant_id, user_id)
                rows = connection.execute(
                    """
                    SELECT tenant_id, user_id, preference_key, preference_type, weight, source, updated_at
                    FROM scoped_preferences
                    WHERE tenant_id = ? AND user_id = ?
                    ORDER BY preference_type, preference_key
                    """,
                    (scoped_tenant_id, scoped_user_id),
                ).fetchall()
            else:
                rows = connection.execute(
                    """
                    SELECT tenant_id, user_id, preference_key, preference_type, weight, source, updated_at
                    FROM scoped_preferences
                    ORDER BY tenant_id, user_id, preference_type, preference_key
                    """
                ).fetchall()
        return tuple(
            UserPreference(
                preference_key=row["preference_key"],
                preference_type=row["preference_type"],
                weight=float(row["weight"]),
                source=row["source"],
                updated_at=parse_datetime(row["updated_at"]),
                tenant_id=row["tenant_id"],
                user_id=row["user_id"],
            )
            for row in rows
        )

    def upsert_preferences(
        self,
        preferences: Sequence[UserPreference],
        tenant_id: str = "",
        user_id: str = "",
    ) -> None:
        scoped_tenant_id, scoped_user_id = self._scope(tenant_id, user_id)
        with self._connect() as connection:
            for preference in preferences:
                connection.execute(
                    """
                    INSERT INTO scoped_preferences (
                        tenant_id,
                        user_id,
                        preference_key,
                        preference_type,
                        weight,
                        source,
                        updated_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?)
                    ON CONFLICT(tenant_id, user_id, preference_key, preference_type) DO UPDATE SET
                        weight = excluded.weight,
                        source = excluded.source,
                        updated_at = excluded.updated_at
                    """,
                    (
                        scoped_tenant_id,
                        scoped_user_id,
                        preference.preference_key,
                        preference.preference_type,
                        preference.weight,
                        preference.source,
                        preference.updated_at.isoformat(),
                    ),
                )

    def upsert_messages(
        self,
        messages: Sequence[MessageRecord],
        tenant_id: str = "",
        user_id: str = "",
    ) -> None:
        scoped_tenant_id, scoped_user_id = self._scope(tenant_id, user_id)
        with self._connect() as connection:
            for message in messages:
                connection.execute(
                    """
                    INSERT INTO scoped_messages (
                        tenant_id,
                        user_id,
                        graph_message_id,
                        thread_id,
                        internet_message_id,
                        subject,
                        from_address,
                        to_addresses_json,
                        cc_addresses_json,
                        received_at,
                        body_preview,
                        categories_json,
                        is_unread,
                        has_attachments,
                        raw_payload_json,
                        first_seen_at,
                        last_seen_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
                    ON CONFLICT(tenant_id, user_id, graph_message_id) DO UPDATE SET
                        thread_id = excluded.thread_id,
                        internet_message_id = excluded.internet_message_id,
                        subject = excluded.subject,
                        from_address = excluded.from_address,
                        to_addresses_json = excluded.to_addresses_json,
                        cc_addresses_json = excluded.cc_addresses_json,
                        received_at = excluded.received_at,
                        body_preview = excluded.body_preview,
                        categories_json = excluded.categories_json,
                        is_unread = excluded.is_unread,
                        has_attachments = excluded.has_attachments,
                        raw_payload_json = excluded.raw_payload_json,
                        last_seen_at = CURRENT_TIMESTAMP
                    """,
                    (
                        scoped_tenant_id,
                        scoped_user_id,
                        message.graph_message_id,
                        message.thread_id,
                        message.internet_message_id,
                        message.subject,
                        message.from_address,
                        _json_dumps(message.to_addresses),
                        _json_dumps(message.cc_addresses),
                        message.received_at.isoformat(),
                        message.body_preview,
                        _json_dumps(message.categories),
                        int(message.is_unread),
                        int(message.has_attachments),
                        _json_dumps(message.raw_payload),
                    ),
                )

    def upsert_meetings(
        self,
        meetings: Sequence[MeetingRecord],
        tenant_id: str = "",
        user_id: str = "",
    ) -> None:
        scoped_tenant_id, scoped_user_id = self._scope(tenant_id, user_id)
        with self._connect() as connection:
            for meeting in meetings:
                connection.execute(
                    """
                    INSERT INTO scoped_meetings (
                        tenant_id,
                        user_id,
                        graph_event_id,
                        subject,
                        start_at,
                        end_at,
                        organizer_address,
                        attendees_json,
                        location,
                        join_url,
                        body_preview,
                        is_online_meeting,
                        raw_payload_json,
                        first_seen_at,
                        last_seen_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
                    ON CONFLICT(tenant_id, user_id, graph_event_id) DO UPDATE SET
                        subject = excluded.subject,
                        start_at = excluded.start_at,
                        end_at = excluded.end_at,
                        organizer_address = excluded.organizer_address,
                        attendees_json = excluded.attendees_json,
                        location = excluded.location,
                        join_url = excluded.join_url,
                        body_preview = excluded.body_preview,
                        is_online_meeting = excluded.is_online_meeting,
                        raw_payload_json = excluded.raw_payload_json,
                        last_seen_at = CURRENT_TIMESTAMP
                    """,
                    (
                        scoped_tenant_id,
                        scoped_user_id,
                        meeting.graph_event_id,
                        meeting.subject,
                        meeting.start_at.isoformat(),
                        meeting.end_at.isoformat(),
                        meeting.organizer_address,
                        _json_dumps(meeting.attendees),
                        meeting.location,
                        meeting.join_url,
                        meeting.body_preview,
                        int(meeting.is_online_meeting),
                        _json_dumps(meeting.raw_payload),
                    ),
                )

    def get_message(self, graph_message_id: str, tenant_id: str = "", user_id: str = "") -> Optional[MessageRecord]:
        scoped_tenant_id, scoped_user_id = self._scope(tenant_id, user_id)
        with self._connect() as connection:
            row = connection.execute(
                """
                SELECT graph_message_id, thread_id, internet_message_id, subject, from_address,
                       to_addresses_json, cc_addresses_json, received_at, body_preview, categories_json,
                       is_unread, has_attachments, raw_payload_json
                FROM scoped_messages
                WHERE tenant_id = ? AND user_id = ? AND graph_message_id = ?
                """,
                (scoped_tenant_id, scoped_user_id, graph_message_id),
            ).fetchone()
        if row is None:
            return None
        return MessageRecord(
            graph_message_id=row["graph_message_id"],
            thread_id=row["thread_id"],
            internet_message_id=row["internet_message_id"],
            subject=row["subject"],
            from_address=row["from_address"],
            to_addresses=tuple(_json_loads(row["to_addresses_json"]) or ()),
            cc_addresses=tuple(_json_loads(row["cc_addresses_json"]) or ()),
            received_at=parse_datetime(row["received_at"]),
            body_preview=row["body_preview"],
            categories=tuple(_json_loads(row["categories_json"]) or ()),
            is_unread=bool(row["is_unread"]),
            has_attachments=bool(row["has_attachments"]),
            raw_payload=dict(_json_loads(row["raw_payload_json"]) or {}),
            tenant_id=scoped_tenant_id,
            user_id=scoped_user_id,
        )

    def get_meeting(self, graph_event_id: str, tenant_id: str = "", user_id: str = "") -> Optional[MeetingRecord]:
        scoped_tenant_id, scoped_user_id = self._scope(tenant_id, user_id)
        with self._connect() as connection:
            row = connection.execute(
                """
                SELECT graph_event_id, subject, start_at, end_at, organizer_address, attendees_json,
                       location, join_url, body_preview, is_online_meeting, raw_payload_json
                FROM scoped_meetings
                WHERE tenant_id = ? AND user_id = ? AND graph_event_id = ?
                """,
                (scoped_tenant_id, scoped_user_id, graph_event_id),
            ).fetchone()
        if row is None:
            return None
        return MeetingRecord(
            graph_event_id=row["graph_event_id"],
            subject=row["subject"],
            start_at=parse_datetime(row["start_at"]),
            end_at=parse_datetime(row["end_at"]),
            organizer_address=row["organizer_address"],
            attendees=tuple(_json_loads(row["attendees_json"]) or ()),
            location=row["location"],
            join_url=row["join_url"],
            body_preview=row["body_preview"],
            is_online_meeting=bool(row["is_online_meeting"]),
            raw_payload=dict(_json_loads(row["raw_payload_json"]) or {}),
            tenant_id=scoped_tenant_id,
            user_id=scoped_user_id,
        )

    def _save_digest_items(
        self,
        connection: sqlite3.Connection,
        payload: DigestPayload,
        tenant_id: str,
        user_id: str,
    ) -> None:
        connection.execute(
            "DELETE FROM scoped_digest_items WHERE tenant_id = ? AND user_id = ? AND run_id = ?",
            (tenant_id, user_id, payload.run_id),
        )
        for section_name in SECTION_NAMES:
            for entry in getattr(payload, section_name):
                connection.execute(
                    """
                    INSERT INTO scoped_digest_items (
                        tenant_id,
                        user_id,
                        run_id,
                        item_type,
                        source_kind,
                        source_id,
                        score,
                        reason_codes_json,
                        guardrail_applied,
                        section_name,
                        rendered_text
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        tenant_id,
                        user_id,
                        payload.run_id,
                        "digest_entry",
                        entry.source_kind,
                        entry.source_id,
                        entry.score,
                        _json_dumps(entry.reason_codes),
                        int(entry.guardrail_applied),
                        section_name,
                        entry.summary,
                    ),
                )

    def save_run(self, run: DigestRunRecord) -> None:
        scoped_tenant_id, scoped_user_id = self._scope(run.tenant_id, run.user_id)
        scoped_summary = replace(run.summary, tenant_id=scoped_tenant_id, user_id=scoped_user_id)
        with self._connect() as connection:
            connection.execute(
                """
                INSERT INTO scoped_digest_runs (
                    tenant_id,
                    user_id,
                    run_id,
                    run_type,
                    status,
                    generated_at,
                    window_start,
                    window_end,
                    delivery_mode,
                    summary_json
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(tenant_id, user_id, run_id) DO UPDATE SET
                    run_type = excluded.run_type,
                    status = excluded.status,
                    generated_at = excluded.generated_at,
                    window_start = excluded.window_start,
                    window_end = excluded.window_end,
                    delivery_mode = excluded.delivery_mode,
                    summary_json = excluded.summary_json
                """,
                (
                    scoped_tenant_id,
                    scoped_user_id,
                    run.run_id,
                    run.run_type,
                    run.status,
                    run.generated_at.isoformat(),
                    run.window_start.isoformat(),
                    run.window_end.isoformat(),
                    run.delivery_mode,
                    _json_dumps(scoped_summary),
                ),
            )
            self._save_digest_items(connection, scoped_summary, scoped_tenant_id, scoped_user_id)

    def _row_to_run(self, row: sqlite3.Row) -> DigestRunRecord:
        summary = digest_payload_from_dict(_json_loads(row["summary_json"]) or {})
        if not summary.tenant_id or not summary.user_id:
            summary = replace(summary, tenant_id=row["tenant_id"], user_id=row["user_id"])
        return DigestRunRecord(
            run_id=row["run_id"],
            run_type=row["run_type"],
            status=row["status"],
            generated_at=parse_datetime(row["generated_at"]),
            window_start=parse_datetime(row["window_start"]),
            window_end=parse_datetime(row["window_end"]),
            delivery_mode=row["delivery_mode"],
            summary=summary,
            tenant_id=row["tenant_id"],
            user_id=row["user_id"],
        )

    def _row_to_email_command(self, row: sqlite3.Row) -> EmailCommandRecord:
        return EmailCommandRecord(
            command_message_id=row["command_message_id"],
            normalized_command=row["normalized_command"],
            sender_address=row["sender_address"],
            processed_at=parse_datetime(row["processed_at"]),
            response_run_id=row["response_run_id"],
            tenant_id=row["tenant_id"],
            user_id=row["user_id"],
        )

    def get_run(self, run_id: str, tenant_id: str = "", user_id: str = "") -> Optional[DigestRunRecord]:
        with self._connect() as connection:
            if tenant_id or user_id:
                scoped_tenant_id, scoped_user_id = self._scope(tenant_id, user_id)
                row = connection.execute(
                    """
                    SELECT tenant_id, user_id, run_id, run_type, status, generated_at, window_start, window_end,
                           delivery_mode, summary_json
                    FROM scoped_digest_runs
                    WHERE tenant_id = ? AND user_id = ? AND run_id = ?
                    """,
                    (scoped_tenant_id, scoped_user_id, run_id),
                ).fetchone()
            else:
                row = connection.execute(
                    """
                    SELECT tenant_id, user_id, run_id, run_type, status, generated_at, window_start, window_end,
                           delivery_mode, summary_json
                    FROM scoped_digest_runs
                    WHERE run_id = ?
                    LIMIT 1
                    """,
                    (run_id,),
                ).fetchone()
        if row is None:
            return None
        return self._row_to_run(row)

    def get_latest_run(self, tenant_id: str = "", user_id: str = "") -> Optional[DigestRunRecord]:
        params = []
        where_clauses = ["1 = 1"]
        if tenant_id:
            scoped_tenant_id, _ = self._scope(tenant_id, "")
            where_clauses.append("tenant_id = ?")
            params.append(scoped_tenant_id)
        if user_id:
            _, scoped_user_id = self._scope("", user_id)
            where_clauses.append("user_id = ?")
            params.append(scoped_user_id)
        with self._connect() as connection:
            row = connection.execute(
                """
                SELECT tenant_id, user_id, run_id, run_type, status, generated_at, window_start, window_end,
                       delivery_mode, summary_json
                FROM scoped_digest_runs
                WHERE {0}
                ORDER BY generated_at DESC
                LIMIT 1
                """.format(" AND ".join(where_clauses)),
                tuple(params),
            ).fetchone()
        if row is None:
            return None
        return self._row_to_run(row)

    def get_latest_completed_run(
        self,
        tenant_id: str = "",
        user_id: str = "",
        run_type: str = "",
    ) -> Optional[DigestRunRecord]:
        params = []
        where_clauses = ["status = 'completed'"]
        if tenant_id:
            scoped_tenant_id, _ = self._scope(tenant_id, "")
            where_clauses.append("tenant_id = ?")
            params.append(scoped_tenant_id)
        if user_id:
            _, scoped_user_id = self._scope("", user_id)
            where_clauses.append("user_id = ?")
            params.append(scoped_user_id)
        if run_type:
            where_clauses.append("run_type = ?")
            params.append(run_type)
        with self._connect() as connection:
            row = connection.execute(
                """
                SELECT tenant_id, user_id, run_id, run_type, status, generated_at, window_start, window_end,
                       delivery_mode, summary_json
                FROM scoped_digest_runs
                WHERE {0}
                ORDER BY generated_at DESC
                LIMIT 1
                """.format(" AND ".join(where_clauses)),
                tuple(params),
            ).fetchone()
        if row is None:
            return None
        return self._row_to_run(row)

    def list_recent_completed_runs(
        self,
        limit: int,
        tenant_id: str = "",
        user_id: str = "",
        run_type: str = "",
    ) -> Sequence[DigestRunRecord]:
        params = []
        where_clauses = ["status = 'completed'"]
        if tenant_id:
            scoped_tenant_id, _ = self._scope(tenant_id, "")
            where_clauses.append("tenant_id = ?")
            params.append(scoped_tenant_id)
        if user_id:
            _, scoped_user_id = self._scope("", user_id)
            where_clauses.append("user_id = ?")
            params.append(scoped_user_id)
        if run_type:
            where_clauses.append("run_type = ?")
            params.append(run_type)
        params.append(max(0, int(limit)))
        with self._connect() as connection:
            rows = connection.execute(
                """
                SELECT tenant_id, user_id, run_id, run_type, status, generated_at, window_start, window_end,
                       delivery_mode, summary_json
                FROM scoped_digest_runs
                WHERE {0}
                ORDER BY generated_at DESC
                LIMIT ?
                """.format(" AND ".join(where_clauses)),
                tuple(params),
            ).fetchall()
        return tuple(self._row_to_run(row) for row in rows)

    def get_latest_completed_run_for_day(
        self,
        target_day: date,
        tenant_id: str = "",
        user_id: str = "",
        display_timezone: str = "UTC",
    ) -> Optional[DigestRunRecord]:
        params = []
        where_clauses = ["status = 'completed'"]
        if tenant_id:
            scoped_tenant_id, _ = self._scope(tenant_id, "")
            where_clauses.append("tenant_id = ?")
            params.append(scoped_tenant_id)
        if user_id:
            _, scoped_user_id = self._scope("", user_id)
            where_clauses.append("user_id = ?")
            params.append(scoped_user_id)
        with self._connect() as connection:
            rows = connection.execute(
                """
                SELECT tenant_id, user_id, run_id, run_type, status, generated_at, window_start, window_end,
                       delivery_mode, summary_json
                FROM scoped_digest_runs
                WHERE {0}
                ORDER BY generated_at DESC
                """.format(" AND ".join(where_clauses)),
                tuple(params),
            ).fetchall()
        zone = _display_zone(display_timezone)
        for row in rows:
            run = self._row_to_run(row)
            if run.generated_at.astimezone(zone).date() == target_day:
                return run
        return None

    def save_feedback(self, feedback: FeedbackRecord, tenant_id: str = "", user_id: str = "") -> None:
        scoped_tenant_id, scoped_user_id = self._scope(tenant_id or feedback.tenant_id, user_id or feedback.user_id)
        with self._connect() as connection:
            connection.execute(
                """
                INSERT INTO scoped_feedback (
                    tenant_id,
                    user_id,
                    feedback_id,
                    run_id,
                    source_kind,
                    source_id,
                    signal_type,
                    signal_value,
                    recorded_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(tenant_id, user_id, feedback_id) DO UPDATE SET
                    run_id = excluded.run_id,
                    source_kind = excluded.source_kind,
                    source_id = excluded.source_id,
                    signal_type = excluded.signal_type,
                    signal_value = excluded.signal_value,
                    recorded_at = excluded.recorded_at
                """,
                (
                    scoped_tenant_id,
                    scoped_user_id,
                    feedback.feedback_id,
                    feedback.run_id,
                    feedback.source_kind,
                    feedback.source_id,
                    feedback.signal_type,
                    feedback.signal_value,
                    feedback.recorded_at.isoformat(),
                ),
            )

    def get_email_command(self, command_message_id: str, tenant_id: str = "") -> Optional[EmailCommandRecord]:
        scoped_tenant_id, _ = self._scope(tenant_id, "")
        with self._connect() as connection:
            row = connection.execute(
                """
                SELECT tenant_id, command_message_id, user_id, normalized_command, sender_address, processed_at, response_run_id
                FROM scoped_email_commands
                WHERE tenant_id = ? AND command_message_id = ?
                LIMIT 1
                """,
                (scoped_tenant_id, command_message_id),
            ).fetchone()
        if row is None:
            return None
        return self._row_to_email_command(row)

    def save_email_command(self, record: EmailCommandRecord, tenant_id: str = "") -> None:
        scoped_tenant_id, _ = self._scope(tenant_id or record.tenant_id, "")
        with self._connect() as connection:
            connection.execute(
                """
                INSERT INTO scoped_email_commands (
                    tenant_id,
                    command_message_id,
                    user_id,
                    normalized_command,
                    sender_address,
                    processed_at,
                    response_run_id
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(tenant_id, command_message_id) DO UPDATE SET
                    user_id = excluded.user_id,
                    normalized_command = excluded.normalized_command,
                    sender_address = excluded.sender_address,
                    processed_at = excluded.processed_at,
                    response_run_id = excluded.response_run_id
                """,
                (
                    scoped_tenant_id,
                    record.command_message_id,
                    record.user_id,
                    record.normalized_command,
                    record.sender_address,
                    record.processed_at.isoformat(),
                    record.response_run_id,
                ),
            )

    def list_feedback(self, run_id: Optional[str] = None, tenant_id: str = "", user_id: str = "") -> Sequence[FeedbackRecord]:
        scoped_tenant_id, scoped_user_id = self._scope(tenant_id, user_id)
        query = """
            SELECT feedback_id, run_id, source_kind, source_id, signal_type, signal_value, recorded_at
            FROM scoped_feedback
            WHERE tenant_id = ? AND user_id = ?
        """
        params = [scoped_tenant_id, scoped_user_id]
        if run_id is not None:
            query += " AND run_id = ?"
            params.append(run_id)
        query += " ORDER BY recorded_at"
        with self._connect() as connection:
            rows = connection.execute(query, tuple(params)).fetchall()
        return tuple(
            FeedbackRecord(
                feedback_id=row["feedback_id"],
                run_id=row["run_id"],
                source_kind=row["source_kind"],
                source_id=row["source_id"],
                signal_type=row["signal_type"],
                signal_value=row["signal_value"],
                recorded_at=parse_datetime(row["recorded_at"]),
                tenant_id=scoped_tenant_id,
                user_id=scoped_user_id,
            )
            for row in rows
        )


class PostgresStorage:
    def __init__(
        self,
        database_url: str,
        default_tenant_id: str = DEFAULT_TENANT_ID,
        default_user_id: str = DEFAULT_USER_ID,
    ) -> None:
        if psycopg is None or dict_row is None:
            raise RuntimeError(
                "Postgres storage requires the `psycopg` package to be installed."
            )
        self.database_url = database_url
        self.default_tenant_id = _normalize_scope_value(default_tenant_id, DEFAULT_TENANT_ID)
        self.default_user_id = _normalize_scope_value(default_user_id, DEFAULT_USER_ID)
        self._ensure_schema()

    def _scope(self, tenant_id: str = "", user_id: str = "") -> tuple[str, str]:
        return (
            _normalize_scope_value(tenant_id, self.default_tenant_id),
            _normalize_scope_value(user_id, self.default_user_id),
        )

    def _connect(self):
        return psycopg.connect(self.database_url, row_factory=dict_row)

    def _table_exists(self, connection, table_name: str) -> bool:
        row = connection.execute(
            """
            SELECT table_name
            FROM information_schema.tables
            WHERE table_schema = 'public' AND table_name = %s
            """,
            (table_name,),
        ).fetchone()
        return row is not None

    def _table_is_empty(self, connection, table_name: str) -> bool:
        row = connection.execute("SELECT COUNT(*) AS count FROM {0}".format(table_name)).fetchone()
        return row is not None and int(row["count"]) == 0

    def _ensure_schema(self) -> None:
        with self._connect() as connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS scoped_messages (
                    tenant_id TEXT NOT NULL,
                    user_id TEXT NOT NULL,
                    graph_message_id TEXT NOT NULL,
                    thread_id TEXT NOT NULL,
                    internet_message_id TEXT NOT NULL,
                    subject TEXT NOT NULL,
                    from_address TEXT NOT NULL,
                    to_addresses_json TEXT NOT NULL,
                    cc_addresses_json TEXT NOT NULL,
                    received_at TEXT NOT NULL,
                    body_preview TEXT NOT NULL,
                    categories_json TEXT NOT NULL,
                    is_unread BOOLEAN NOT NULL,
                    has_attachments BOOLEAN NOT NULL,
                    raw_payload_json TEXT NOT NULL,
                    first_seen_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    last_seen_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    PRIMARY KEY (tenant_id, user_id, graph_message_id)
                )
                """
            )
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS scoped_meetings (
                    tenant_id TEXT NOT NULL,
                    user_id TEXT NOT NULL,
                    graph_event_id TEXT NOT NULL,
                    subject TEXT NOT NULL,
                    start_at TEXT NOT NULL,
                    end_at TEXT NOT NULL,
                    organizer_address TEXT NOT NULL,
                    attendees_json TEXT NOT NULL,
                    location TEXT NOT NULL,
                    join_url TEXT NOT NULL,
                    body_preview TEXT NOT NULL,
                    is_online_meeting BOOLEAN NOT NULL,
                    raw_payload_json TEXT NOT NULL,
                    first_seen_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    last_seen_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    PRIMARY KEY (tenant_id, user_id, graph_event_id)
                )
                """
            )
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS scoped_digest_runs (
                    tenant_id TEXT NOT NULL,
                    user_id TEXT NOT NULL,
                    run_id TEXT NOT NULL,
                    run_type TEXT NOT NULL,
                    status TEXT NOT NULL,
                    generated_at TEXT NOT NULL,
                    window_start TEXT NOT NULL,
                    window_end TEXT NOT NULL,
                    delivery_mode TEXT NOT NULL,
                    summary_json TEXT NOT NULL,
                    PRIMARY KEY (tenant_id, user_id, run_id)
                )
                """
            )
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS scoped_digest_items (
                    tenant_id TEXT NOT NULL,
                    user_id TEXT NOT NULL,
                    run_id TEXT NOT NULL,
                    item_type TEXT NOT NULL,
                    source_kind TEXT NOT NULL,
                    source_id TEXT NOT NULL,
                    score DOUBLE PRECISION NOT NULL,
                    reason_codes_json TEXT NOT NULL,
                    guardrail_applied BOOLEAN NOT NULL,
                    section_name TEXT NOT NULL,
                    rendered_text TEXT NOT NULL,
                    PRIMARY KEY (tenant_id, user_id, run_id, section_name, source_kind, source_id),
                    FOREIGN KEY (tenant_id, user_id, run_id)
                        REFERENCES scoped_digest_runs(tenant_id, user_id, run_id)
                        ON DELETE CASCADE
                )
                """
            )
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS scoped_feedback (
                    tenant_id TEXT NOT NULL,
                    user_id TEXT NOT NULL,
                    feedback_id TEXT NOT NULL,
                    run_id TEXT NOT NULL,
                    source_kind TEXT NOT NULL,
                    source_id TEXT NOT NULL,
                    signal_type TEXT NOT NULL,
                    signal_value TEXT NOT NULL,
                    recorded_at TEXT NOT NULL,
                    PRIMARY KEY (tenant_id, user_id, feedback_id)
                )
                """
            )
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS scoped_email_commands (
                    tenant_id TEXT NOT NULL,
                    command_message_id TEXT NOT NULL,
                    user_id TEXT NOT NULL,
                    normalized_command TEXT NOT NULL,
                    sender_address TEXT NOT NULL,
                    processed_at TEXT NOT NULL,
                    response_run_id TEXT NOT NULL,
                    PRIMARY KEY (tenant_id, command_message_id)
                )
                """
            )
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS scoped_preferences (
                    tenant_id TEXT NOT NULL,
                    user_id TEXT NOT NULL,
                    preference_key TEXT NOT NULL,
                    preference_type TEXT NOT NULL,
                    weight DOUBLE PRECISION NOT NULL,
                    source TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    PRIMARY KEY (tenant_id, user_id, preference_key, preference_type)
                )
                """
            )
            self._migrate_legacy_data(connection)
            connection.commit()

    def _migrate_legacy_data(self, connection) -> None:
        tenant_id, user_id = self._scope()
        migrations = (
            (
                "messages",
                "scoped_messages",
                """
                INSERT INTO scoped_messages (
                    tenant_id,
                    user_id,
                    graph_message_id,
                    thread_id,
                    internet_message_id,
                    subject,
                    from_address,
                    to_addresses_json,
                    cc_addresses_json,
                    received_at,
                    body_preview,
                    categories_json,
                    is_unread,
                    has_attachments,
                    raw_payload_json,
                    first_seen_at,
                    last_seen_at
                )
                SELECT %s, %s, graph_message_id, thread_id, internet_message_id, subject, from_address,
                       to_addresses_json, cc_addresses_json, received_at, body_preview, categories_json,
                       is_unread, has_attachments, raw_payload_json, first_seen_at, last_seen_at
                FROM messages
                """,
            ),
            (
                "meetings",
                "scoped_meetings",
                """
                INSERT INTO scoped_meetings (
                    tenant_id,
                    user_id,
                    graph_event_id,
                    subject,
                    start_at,
                    end_at,
                    organizer_address,
                    attendees_json,
                    location,
                    join_url,
                    body_preview,
                    is_online_meeting,
                    raw_payload_json,
                    first_seen_at,
                    last_seen_at
                )
                SELECT %s, %s, graph_event_id, subject, start_at, end_at, organizer_address, attendees_json,
                       location, join_url, body_preview, is_online_meeting, raw_payload_json, first_seen_at, last_seen_at
                FROM meetings
                """,
            ),
            (
                "digest_runs",
                "scoped_digest_runs",
                """
                INSERT INTO scoped_digest_runs (
                    tenant_id,
                    user_id,
                    run_id,
                    run_type,
                    status,
                    generated_at,
                    window_start,
                    window_end,
                    delivery_mode,
                    summary_json
                )
                SELECT %s, %s, run_id, run_type, status, generated_at, window_start, window_end, delivery_mode, summary_json
                FROM digest_runs
                """,
            ),
            (
                "digest_items",
                "scoped_digest_items",
                """
                INSERT INTO scoped_digest_items (
                    tenant_id,
                    user_id,
                    run_id,
                    item_type,
                    source_kind,
                    source_id,
                    score,
                    reason_codes_json,
                    guardrail_applied,
                    section_name,
                    rendered_text
                )
                SELECT %s, %s, run_id, item_type, source_kind, source_id, score, reason_codes_json,
                       guardrail_applied, section_name, rendered_text
                FROM digest_items
                """,
            ),
            (
                "feedback",
                "scoped_feedback",
                """
                INSERT INTO scoped_feedback (
                    tenant_id,
                    user_id,
                    feedback_id,
                    run_id,
                    source_kind,
                    source_id,
                    signal_type,
                    signal_value,
                    recorded_at
                )
                SELECT %s, %s, feedback_id, run_id, source_kind, source_id, signal_type, signal_value, recorded_at
                FROM feedback
                """,
            ),
            (
                "preferences",
                "scoped_preferences",
                """
                INSERT INTO scoped_preferences (
                    tenant_id,
                    user_id,
                    preference_key,
                    preference_type,
                    weight,
                    source,
                    updated_at
                )
                SELECT %s, %s, preference_key, preference_type, weight, source, updated_at
                FROM preferences
                """,
            ),
        )
        for legacy_name, scoped_name, statement in migrations:
            if not self._table_exists(connection, legacy_name):
                continue
            if not self._table_is_empty(connection, scoped_name):
                continue
            connection.execute(statement, (tenant_id, user_id))

    def load_preferences(self, tenant_id: str = "", user_id: str = "") -> Sequence[UserPreference]:
        with self._connect() as connection:
            if tenant_id or user_id:
                scoped_tenant_id, scoped_user_id = self._scope(tenant_id, user_id)
                rows = connection.execute(
                    """
                    SELECT tenant_id, user_id, preference_key, preference_type, weight, source, updated_at
                    FROM scoped_preferences
                    WHERE tenant_id = %s AND user_id = %s
                    ORDER BY preference_type, preference_key
                    """,
                    (scoped_tenant_id, scoped_user_id),
                ).fetchall()
            else:
                rows = connection.execute(
                    """
                    SELECT tenant_id, user_id, preference_key, preference_type, weight, source, updated_at
                    FROM scoped_preferences
                    ORDER BY tenant_id, user_id, preference_type, preference_key
                    """
                ).fetchall()
        return tuple(
            UserPreference(
                preference_key=row["preference_key"],
                preference_type=row["preference_type"],
                weight=float(row["weight"]),
                source=row["source"],
                updated_at=parse_datetime(row["updated_at"]),
                tenant_id=row["tenant_id"],
                user_id=row["user_id"],
            )
            for row in rows
        )

    def upsert_preferences(
        self,
        preferences: Sequence[UserPreference],
        tenant_id: str = "",
        user_id: str = "",
    ) -> None:
        scoped_tenant_id, scoped_user_id = self._scope(tenant_id, user_id)
        with self._connect() as connection:
            for preference in preferences:
                connection.execute(
                    """
                    INSERT INTO scoped_preferences (
                        tenant_id,
                        user_id,
                        preference_key,
                        preference_type,
                        weight,
                        source,
                        updated_at
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT(tenant_id, user_id, preference_key, preference_type) DO UPDATE SET
                        weight = EXCLUDED.weight,
                        source = EXCLUDED.source,
                        updated_at = EXCLUDED.updated_at
                    """,
                    (
                        scoped_tenant_id,
                        scoped_user_id,
                        preference.preference_key,
                        preference.preference_type,
                        preference.weight,
                        preference.source,
                        preference.updated_at.isoformat(),
                    ),
                )
            connection.commit()

    def upsert_messages(
        self,
        messages: Sequence[MessageRecord],
        tenant_id: str = "",
        user_id: str = "",
    ) -> None:
        scoped_tenant_id, scoped_user_id = self._scope(tenant_id, user_id)
        with self._connect() as connection:
            for message in messages:
                connection.execute(
                    """
                    INSERT INTO scoped_messages (
                        tenant_id,
                        user_id,
                        graph_message_id,
                        thread_id,
                        internet_message_id,
                        subject,
                        from_address,
                        to_addresses_json,
                        cc_addresses_json,
                        received_at,
                        body_preview,
                        categories_json,
                        is_unread,
                        has_attachments,
                        raw_payload_json,
                        first_seen_at,
                        last_seen_at
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
                    ON CONFLICT(tenant_id, user_id, graph_message_id) DO UPDATE SET
                        thread_id = EXCLUDED.thread_id,
                        internet_message_id = EXCLUDED.internet_message_id,
                        subject = EXCLUDED.subject,
                        from_address = EXCLUDED.from_address,
                        to_addresses_json = EXCLUDED.to_addresses_json,
                        cc_addresses_json = EXCLUDED.cc_addresses_json,
                        received_at = EXCLUDED.received_at,
                        body_preview = EXCLUDED.body_preview,
                        categories_json = EXCLUDED.categories_json,
                        is_unread = EXCLUDED.is_unread,
                        has_attachments = EXCLUDED.has_attachments,
                        raw_payload_json = EXCLUDED.raw_payload_json,
                        last_seen_at = CURRENT_TIMESTAMP
                    """,
                    (
                        scoped_tenant_id,
                        scoped_user_id,
                        message.graph_message_id,
                        message.thread_id,
                        message.internet_message_id,
                        message.subject,
                        message.from_address,
                        _json_dumps(message.to_addresses),
                        _json_dumps(message.cc_addresses),
                        message.received_at.isoformat(),
                        message.body_preview,
                        _json_dumps(message.categories),
                        message.is_unread,
                        message.has_attachments,
                        _json_dumps(message.raw_payload),
                    ),
                )
            connection.commit()

    def upsert_meetings(
        self,
        meetings: Sequence[MeetingRecord],
        tenant_id: str = "",
        user_id: str = "",
    ) -> None:
        scoped_tenant_id, scoped_user_id = self._scope(tenant_id, user_id)
        with self._connect() as connection:
            for meeting in meetings:
                connection.execute(
                    """
                    INSERT INTO scoped_meetings (
                        tenant_id,
                        user_id,
                        graph_event_id,
                        subject,
                        start_at,
                        end_at,
                        organizer_address,
                        attendees_json,
                        location,
                        join_url,
                        body_preview,
                        is_online_meeting,
                        raw_payload_json,
                        first_seen_at,
                        last_seen_at
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
                    ON CONFLICT(tenant_id, user_id, graph_event_id) DO UPDATE SET
                        subject = EXCLUDED.subject,
                        start_at = EXCLUDED.start_at,
                        end_at = EXCLUDED.end_at,
                        organizer_address = EXCLUDED.organizer_address,
                        attendees_json = EXCLUDED.attendees_json,
                        location = EXCLUDED.location,
                        join_url = EXCLUDED.join_url,
                        body_preview = EXCLUDED.body_preview,
                        is_online_meeting = EXCLUDED.is_online_meeting,
                        raw_payload_json = EXCLUDED.raw_payload_json,
                        last_seen_at = CURRENT_TIMESTAMP
                    """,
                    (
                        scoped_tenant_id,
                        scoped_user_id,
                        meeting.graph_event_id,
                        meeting.subject,
                        meeting.start_at.isoformat(),
                        meeting.end_at.isoformat(),
                        meeting.organizer_address,
                        _json_dumps(meeting.attendees),
                        meeting.location,
                        meeting.join_url,
                        meeting.body_preview,
                        meeting.is_online_meeting,
                        _json_dumps(meeting.raw_payload),
                    ),
                )
            connection.commit()

    def get_message(self, graph_message_id: str, tenant_id: str = "", user_id: str = "") -> Optional[MessageRecord]:
        scoped_tenant_id, scoped_user_id = self._scope(tenant_id, user_id)
        with self._connect() as connection:
            row = connection.execute(
                """
                SELECT graph_message_id, thread_id, internet_message_id, subject, from_address,
                       to_addresses_json, cc_addresses_json, received_at, body_preview, categories_json,
                       is_unread, has_attachments, raw_payload_json
                FROM scoped_messages
                WHERE tenant_id = %s AND user_id = %s AND graph_message_id = %s
                """,
                (scoped_tenant_id, scoped_user_id, graph_message_id),
            ).fetchone()
        if row is None:
            return None
        return MessageRecord(
            graph_message_id=row["graph_message_id"],
            thread_id=row["thread_id"],
            internet_message_id=row["internet_message_id"],
            subject=row["subject"],
            from_address=row["from_address"],
            to_addresses=tuple(_json_loads(row["to_addresses_json"]) or ()),
            cc_addresses=tuple(_json_loads(row["cc_addresses_json"]) or ()),
            received_at=parse_datetime(row["received_at"]),
            body_preview=row["body_preview"],
            categories=tuple(_json_loads(row["categories_json"]) or ()),
            is_unread=bool(row["is_unread"]),
            has_attachments=bool(row["has_attachments"]),
            raw_payload=dict(_json_loads(row["raw_payload_json"]) or {}),
            tenant_id=scoped_tenant_id,
            user_id=scoped_user_id,
        )

    def get_meeting(self, graph_event_id: str, tenant_id: str = "", user_id: str = "") -> Optional[MeetingRecord]:
        scoped_tenant_id, scoped_user_id = self._scope(tenant_id, user_id)
        with self._connect() as connection:
            row = connection.execute(
                """
                SELECT graph_event_id, subject, start_at, end_at, organizer_address, attendees_json,
                       location, join_url, body_preview, is_online_meeting, raw_payload_json
                FROM scoped_meetings
                WHERE tenant_id = %s AND user_id = %s AND graph_event_id = %s
                """,
                (scoped_tenant_id, scoped_user_id, graph_event_id),
            ).fetchone()
        if row is None:
            return None
        return MeetingRecord(
            graph_event_id=row["graph_event_id"],
            subject=row["subject"],
            start_at=parse_datetime(row["start_at"]),
            end_at=parse_datetime(row["end_at"]),
            organizer_address=row["organizer_address"],
            attendees=tuple(_json_loads(row["attendees_json"]) or ()),
            location=row["location"],
            join_url=row["join_url"],
            body_preview=row["body_preview"],
            is_online_meeting=bool(row["is_online_meeting"]),
            raw_payload=dict(_json_loads(row["raw_payload_json"]) or {}),
            tenant_id=scoped_tenant_id,
            user_id=scoped_user_id,
        )

    def _save_digest_items(self, connection, payload: DigestPayload, tenant_id: str, user_id: str) -> None:
        connection.execute(
            "DELETE FROM scoped_digest_items WHERE tenant_id = %s AND user_id = %s AND run_id = %s",
            (tenant_id, user_id, payload.run_id),
        )
        for section_name in SECTION_NAMES:
            for entry in getattr(payload, section_name):
                connection.execute(
                    """
                    INSERT INTO scoped_digest_items (
                        tenant_id,
                        user_id,
                        run_id,
                        item_type,
                        source_kind,
                        source_id,
                        score,
                        reason_codes_json,
                        guardrail_applied,
                        section_name,
                        rendered_text
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """,
                    (
                        tenant_id,
                        user_id,
                        payload.run_id,
                        "digest_entry",
                        entry.source_kind,
                        entry.source_id,
                        entry.score,
                        _json_dumps(entry.reason_codes),
                        entry.guardrail_applied,
                        section_name,
                        entry.summary,
                    ),
                )

    def save_run(self, run: DigestRunRecord) -> None:
        scoped_tenant_id, scoped_user_id = self._scope(run.tenant_id, run.user_id)
        scoped_summary = replace(run.summary, tenant_id=scoped_tenant_id, user_id=scoped_user_id)
        with self._connect() as connection:
            connection.execute(
                """
                INSERT INTO scoped_digest_runs (
                    tenant_id,
                    user_id,
                    run_id,
                    run_type,
                    status,
                    generated_at,
                    window_start,
                    window_end,
                    delivery_mode,
                    summary_json
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT(tenant_id, user_id, run_id) DO UPDATE SET
                    run_type = EXCLUDED.run_type,
                    status = EXCLUDED.status,
                    generated_at = EXCLUDED.generated_at,
                    window_start = EXCLUDED.window_start,
                    window_end = EXCLUDED.window_end,
                    delivery_mode = EXCLUDED.delivery_mode,
                    summary_json = EXCLUDED.summary_json
                """,
                (
                    scoped_tenant_id,
                    scoped_user_id,
                    run.run_id,
                    run.run_type,
                    run.status,
                    run.generated_at.isoformat(),
                    run.window_start.isoformat(),
                    run.window_end.isoformat(),
                    run.delivery_mode,
                    _json_dumps(scoped_summary),
                ),
            )
            self._save_digest_items(connection, scoped_summary, scoped_tenant_id, scoped_user_id)
            connection.commit()

    def _row_to_run(self, row: Mapping[str, Any]) -> DigestRunRecord:
        summary = digest_payload_from_dict(_json_loads(row["summary_json"]) or {})
        if not summary.tenant_id or not summary.user_id:
            summary = replace(summary, tenant_id=row["tenant_id"], user_id=row["user_id"])
        return DigestRunRecord(
            run_id=row["run_id"],
            run_type=row["run_type"],
            status=row["status"],
            generated_at=parse_datetime(row["generated_at"]),
            window_start=parse_datetime(row["window_start"]),
            window_end=parse_datetime(row["window_end"]),
            delivery_mode=row["delivery_mode"],
            summary=summary,
            tenant_id=row["tenant_id"],
            user_id=row["user_id"],
        )

    def _row_to_email_command(self, row: Mapping[str, Any]) -> EmailCommandRecord:
        return EmailCommandRecord(
            command_message_id=row["command_message_id"],
            normalized_command=row["normalized_command"],
            sender_address=row["sender_address"],
            processed_at=parse_datetime(row["processed_at"]),
            response_run_id=row["response_run_id"],
            tenant_id=row["tenant_id"],
            user_id=row["user_id"],
        )

    def get_run(self, run_id: str, tenant_id: str = "", user_id: str = "") -> Optional[DigestRunRecord]:
        with self._connect() as connection:
            if tenant_id or user_id:
                scoped_tenant_id, scoped_user_id = self._scope(tenant_id, user_id)
                row = connection.execute(
                    """
                    SELECT tenant_id, user_id, run_id, run_type, status, generated_at, window_start, window_end,
                           delivery_mode, summary_json
                    FROM scoped_digest_runs
                    WHERE tenant_id = %s AND user_id = %s AND run_id = %s
                    """,
                    (scoped_tenant_id, scoped_user_id, run_id),
                ).fetchone()
            else:
                row = connection.execute(
                    """
                    SELECT tenant_id, user_id, run_id, run_type, status, generated_at, window_start, window_end,
                           delivery_mode, summary_json
                    FROM scoped_digest_runs
                    WHERE run_id = %s
                    LIMIT 1
                    """,
                    (run_id,),
                ).fetchone()
        if row is None:
            return None
        return self._row_to_run(row)

    def get_latest_run(self, tenant_id: str = "", user_id: str = "") -> Optional[DigestRunRecord]:
        params = []
        where_clauses = ["1 = 1"]
        if tenant_id:
            scoped_tenant_id, _ = self._scope(tenant_id, "")
            where_clauses.append("tenant_id = %s")
            params.append(scoped_tenant_id)
        if user_id:
            _, scoped_user_id = self._scope("", user_id)
            where_clauses.append("user_id = %s")
            params.append(scoped_user_id)
        with self._connect() as connection:
            row = connection.execute(
                """
                SELECT tenant_id, user_id, run_id, run_type, status, generated_at, window_start, window_end,
                       delivery_mode, summary_json
                FROM scoped_digest_runs
                WHERE {0}
                ORDER BY generated_at DESC
                LIMIT 1
                """.format(" AND ".join(where_clauses)),
                tuple(params),
            ).fetchone()
        if row is None:
            return None
        return self._row_to_run(row)

    def get_latest_completed_run(
        self,
        tenant_id: str = "",
        user_id: str = "",
        run_type: str = "",
    ) -> Optional[DigestRunRecord]:
        params = []
        where_clauses = ["status = 'completed'"]
        if tenant_id:
            scoped_tenant_id, _ = self._scope(tenant_id, "")
            where_clauses.append("tenant_id = %s")
            params.append(scoped_tenant_id)
        if user_id:
            _, scoped_user_id = self._scope("", user_id)
            where_clauses.append("user_id = %s")
            params.append(scoped_user_id)
        if run_type:
            where_clauses.append("run_type = %s")
            params.append(run_type)
        with self._connect() as connection:
            row = connection.execute(
                """
                SELECT tenant_id, user_id, run_id, run_type, status, generated_at, window_start, window_end,
                       delivery_mode, summary_json
                FROM scoped_digest_runs
                WHERE {0}
                ORDER BY generated_at DESC
                LIMIT 1
                """.format(" AND ".join(where_clauses)),
                tuple(params),
            ).fetchone()
        if row is None:
            return None
        return self._row_to_run(row)

    def list_recent_completed_runs(
        self,
        limit: int,
        tenant_id: str = "",
        user_id: str = "",
        run_type: str = "",
    ) -> Sequence[DigestRunRecord]:
        params = []
        where_clauses = ["status = 'completed'"]
        if tenant_id:
            scoped_tenant_id, _ = self._scope(tenant_id, "")
            where_clauses.append("tenant_id = %s")
            params.append(scoped_tenant_id)
        if user_id:
            _, scoped_user_id = self._scope("", user_id)
            where_clauses.append("user_id = %s")
            params.append(scoped_user_id)
        if run_type:
            where_clauses.append("run_type = %s")
            params.append(run_type)
        params.append(max(0, int(limit)))
        with self._connect() as connection:
            rows = connection.execute(
                """
                SELECT tenant_id, user_id, run_id, run_type, status, generated_at, window_start, window_end,
                       delivery_mode, summary_json
                FROM scoped_digest_runs
                WHERE {0}
                ORDER BY generated_at DESC
                LIMIT %s
                """.format(" AND ".join(where_clauses)),
                tuple(params),
            ).fetchall()
        return tuple(self._row_to_run(row) for row in rows)

    def get_latest_completed_run_for_day(
        self,
        target_day: date,
        tenant_id: str = "",
        user_id: str = "",
        display_timezone: str = "UTC",
    ) -> Optional[DigestRunRecord]:
        params = []
        where_clauses = ["status = 'completed'"]
        if tenant_id:
            scoped_tenant_id, _ = self._scope(tenant_id, "")
            where_clauses.append("tenant_id = %s")
            params.append(scoped_tenant_id)
        if user_id:
            _, scoped_user_id = self._scope("", user_id)
            where_clauses.append("user_id = %s")
            params.append(scoped_user_id)
        with self._connect() as connection:
            rows = connection.execute(
                """
                SELECT tenant_id, user_id, run_id, run_type, status, generated_at, window_start, window_end,
                       delivery_mode, summary_json
                FROM scoped_digest_runs
                WHERE {0}
                ORDER BY generated_at DESC
                """.format(" AND ".join(where_clauses)),
                tuple(params),
            ).fetchall()
        zone = _display_zone(display_timezone)
        for row in rows:
            run = self._row_to_run(row)
            if run.generated_at.astimezone(zone).date() == target_day:
                return run
        return None

    def save_feedback(self, feedback: FeedbackRecord, tenant_id: str = "", user_id: str = "") -> None:
        scoped_tenant_id, scoped_user_id = self._scope(tenant_id or feedback.tenant_id, user_id or feedback.user_id)
        with self._connect() as connection:
            connection.execute(
                """
                INSERT INTO scoped_feedback (
                    tenant_id,
                    user_id,
                    feedback_id,
                    run_id,
                    source_kind,
                    source_id,
                    signal_type,
                    signal_value,
                    recorded_at
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT(tenant_id, user_id, feedback_id) DO UPDATE SET
                    run_id = EXCLUDED.run_id,
                    source_kind = EXCLUDED.source_kind,
                    source_id = EXCLUDED.source_id,
                    signal_type = EXCLUDED.signal_type,
                    signal_value = EXCLUDED.signal_value,
                    recorded_at = EXCLUDED.recorded_at
                """,
                (
                    scoped_tenant_id,
                    scoped_user_id,
                    feedback.feedback_id,
                    feedback.run_id,
                    feedback.source_kind,
                    feedback.source_id,
                    feedback.signal_type,
                    feedback.signal_value,
                    feedback.recorded_at.isoformat(),
                ),
            )
            connection.commit()

    def get_email_command(self, command_message_id: str, tenant_id: str = "") -> Optional[EmailCommandRecord]:
        scoped_tenant_id, _ = self._scope(tenant_id, "")
        with self._connect() as connection:
            row = connection.execute(
                """
                SELECT tenant_id, command_message_id, user_id, normalized_command, sender_address, processed_at, response_run_id
                FROM scoped_email_commands
                WHERE tenant_id = %s AND command_message_id = %s
                LIMIT 1
                """,
                (scoped_tenant_id, command_message_id),
            ).fetchone()
        if row is None:
            return None
        return self._row_to_email_command(row)

    def save_email_command(self, record: EmailCommandRecord, tenant_id: str = "") -> None:
        scoped_tenant_id, _ = self._scope(tenant_id or record.tenant_id, "")
        with self._connect() as connection:
            connection.execute(
                """
                INSERT INTO scoped_email_commands (
                    tenant_id,
                    command_message_id,
                    user_id,
                    normalized_command,
                    sender_address,
                    processed_at,
                    response_run_id
                ) VALUES (%s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT(tenant_id, command_message_id) DO UPDATE SET
                    user_id = EXCLUDED.user_id,
                    normalized_command = EXCLUDED.normalized_command,
                    sender_address = EXCLUDED.sender_address,
                    processed_at = EXCLUDED.processed_at,
                    response_run_id = EXCLUDED.response_run_id
                """,
                (
                    scoped_tenant_id,
                    record.command_message_id,
                    record.user_id,
                    record.normalized_command,
                    record.sender_address,
                    record.processed_at.isoformat(),
                    record.response_run_id,
                ),
            )
            connection.commit()

    def list_feedback(self, run_id: Optional[str] = None, tenant_id: str = "", user_id: str = "") -> Sequence[FeedbackRecord]:
        scoped_tenant_id, scoped_user_id = self._scope(tenant_id, user_id)
        query = """
            SELECT feedback_id, run_id, source_kind, source_id, signal_type, signal_value, recorded_at
            FROM scoped_feedback
            WHERE tenant_id = %s AND user_id = %s
        """
        params = [scoped_tenant_id, scoped_user_id]
        if run_id is not None:
            query += " AND run_id = %s"
            params.append(run_id)
        query += " ORDER BY recorded_at"
        with self._connect() as connection:
            rows = connection.execute(query, tuple(params)).fetchall()
        return tuple(
            FeedbackRecord(
                feedback_id=row["feedback_id"],
                run_id=row["run_id"],
                source_kind=row["source_kind"],
                source_id=row["source_id"],
                signal_type=row["signal_type"],
                signal_value=row["signal_value"],
                recorded_at=parse_datetime(row["recorded_at"]),
                tenant_id=scoped_tenant_id,
                user_id=scoped_user_id,
            )
            for row in rows
        )

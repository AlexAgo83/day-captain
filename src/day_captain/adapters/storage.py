"""SQLite storage adapter for Day Captain."""

from datetime import date
import json
import sqlite3
from typing import Any
from typing import Mapping
from typing import Optional
from typing import Sequence

from day_captain.models import DigestEntry
from day_captain.models import DigestPayload
from day_captain.models import DigestRunRecord
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
    "upcoming_meetings",
)


def _json_dumps(value: Any) -> str:
    return json.dumps(to_jsonable(value), sort_keys=True)


def _json_loads(value: Optional[str]) -> Any:
    if not value:
        return None
    return json.loads(value)


class SQLiteStorage:
    def __init__(self, path: str) -> None:
        self.path = path
        self._ensure_schema()

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.path)
        connection.row_factory = sqlite3.Row
        return connection

    def _ensure_schema(self) -> None:
        with self._connect() as connection:
            connection.executescript(
                """
                PRAGMA foreign_keys = ON;

                CREATE TABLE IF NOT EXISTS messages (
                    graph_message_id TEXT PRIMARY KEY,
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
                    last_seen_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                );

                CREATE TABLE IF NOT EXISTS meetings (
                    graph_event_id TEXT PRIMARY KEY,
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
                    last_seen_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                );

                CREATE TABLE IF NOT EXISTS digest_runs (
                    run_id TEXT PRIMARY KEY,
                    run_type TEXT NOT NULL,
                    status TEXT NOT NULL,
                    generated_at TEXT NOT NULL,
                    window_start TEXT NOT NULL,
                    window_end TEXT NOT NULL,
                    delivery_mode TEXT NOT NULL,
                    summary_json TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS digest_items (
                    run_id TEXT NOT NULL,
                    item_type TEXT NOT NULL,
                    source_kind TEXT NOT NULL,
                    source_id TEXT NOT NULL,
                    score REAL NOT NULL,
                    reason_codes_json TEXT NOT NULL,
                    guardrail_applied INTEGER NOT NULL,
                    section_name TEXT NOT NULL,
                    rendered_text TEXT NOT NULL,
                    PRIMARY KEY (run_id, section_name, source_kind, source_id),
                    FOREIGN KEY (run_id) REFERENCES digest_runs(run_id) ON DELETE CASCADE
                );

                CREATE TABLE IF NOT EXISTS feedback (
                    feedback_id TEXT PRIMARY KEY,
                    run_id TEXT NOT NULL,
                    source_kind TEXT NOT NULL,
                    source_id TEXT NOT NULL,
                    signal_type TEXT NOT NULL,
                    signal_value TEXT NOT NULL,
                    recorded_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS preferences (
                    preference_key TEXT NOT NULL,
                    preference_type TEXT NOT NULL,
                    weight REAL NOT NULL,
                    source TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    PRIMARY KEY (preference_key, preference_type)
                );
                """
            )

    def load_preferences(self) -> Sequence[UserPreference]:
        with self._connect() as connection:
            rows = connection.execute(
                """
                SELECT preference_key, preference_type, weight, source, updated_at
                FROM preferences
                ORDER BY preference_type, preference_key
                """
            ).fetchall()
        return tuple(
            UserPreference(
                preference_key=row["preference_key"],
                preference_type=row["preference_type"],
                weight=float(row["weight"]),
                source=row["source"],
                updated_at=parse_datetime(row["updated_at"]),
            )
            for row in rows
        )

    def upsert_messages(self, messages: Sequence[MessageRecord]) -> None:
        with self._connect() as connection:
            for message in messages:
                connection.execute(
                    """
                    INSERT INTO messages (
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
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
                    ON CONFLICT(graph_message_id) DO UPDATE SET
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

    def upsert_meetings(self, meetings: Sequence[MeetingRecord]) -> None:
        with self._connect() as connection:
            for meeting in meetings:
                connection.execute(
                    """
                    INSERT INTO meetings (
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
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
                    ON CONFLICT(graph_event_id) DO UPDATE SET
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

    def _save_digest_items(self, connection: sqlite3.Connection, payload: DigestPayload) -> None:
        connection.execute("DELETE FROM digest_items WHERE run_id = ?", (payload.run_id,))
        for section_name in SECTION_NAMES:
            entries = getattr(payload, section_name)
            for entry in entries:
                connection.execute(
                    """
                    INSERT INTO digest_items (
                        run_id,
                        item_type,
                        source_kind,
                        source_id,
                        score,
                        reason_codes_json,
                        guardrail_applied,
                        section_name,
                        rendered_text
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
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
        with self._connect() as connection:
            connection.execute(
                """
                INSERT INTO digest_runs (
                    run_id,
                    run_type,
                    status,
                    generated_at,
                    window_start,
                    window_end,
                    delivery_mode,
                    summary_json
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(run_id) DO UPDATE SET
                    run_type = excluded.run_type,
                    status = excluded.status,
                    generated_at = excluded.generated_at,
                    window_start = excluded.window_start,
                    window_end = excluded.window_end,
                    delivery_mode = excluded.delivery_mode,
                    summary_json = excluded.summary_json
                """,
                (
                    run.run_id,
                    run.run_type,
                    run.status,
                    run.generated_at.isoformat(),
                    run.window_start.isoformat(),
                    run.window_end.isoformat(),
                    run.delivery_mode,
                    _json_dumps(run.summary),
                ),
            )
            self._save_digest_items(connection, run.summary)

    def _row_to_run(self, row: sqlite3.Row) -> DigestRunRecord:
        summary = digest_payload_from_dict(_json_loads(row["summary_json"]) or {})
        return DigestRunRecord(
            run_id=row["run_id"],
            run_type=row["run_type"],
            status=row["status"],
            generated_at=parse_datetime(row["generated_at"]),
            window_start=parse_datetime(row["window_start"]),
            window_end=parse_datetime(row["window_end"]),
            delivery_mode=row["delivery_mode"],
            summary=summary,
        )

    def get_run(self, run_id: str) -> Optional[DigestRunRecord]:
        with self._connect() as connection:
            row = connection.execute(
                """
                SELECT run_id, run_type, status, generated_at, window_start, window_end, delivery_mode, summary_json
                FROM digest_runs
                WHERE run_id = ?
                """,
                (run_id,),
            ).fetchone()
        if row is None:
            return None
        return self._row_to_run(row)

    def get_latest_completed_run(self) -> Optional[DigestRunRecord]:
        with self._connect() as connection:
            row = connection.execute(
                """
                SELECT run_id, run_type, status, generated_at, window_start, window_end, delivery_mode, summary_json
                FROM digest_runs
                WHERE status = 'completed'
                ORDER BY generated_at DESC
                LIMIT 1
                """
            ).fetchone()
        if row is None:
            return None
        return self._row_to_run(row)

    def get_latest_completed_run_for_day(self, target_day: date) -> Optional[DigestRunRecord]:
        with self._connect() as connection:
            row = connection.execute(
                """
                SELECT run_id, run_type, status, generated_at, window_start, window_end, delivery_mode, summary_json
                FROM digest_runs
                WHERE status = 'completed'
                  AND substr(generated_at, 1, 10) = ?
                ORDER BY generated_at DESC
                LIMIT 1
                """,
                (target_day.isoformat(),),
            ).fetchone()
        if row is None:
            return None
        return self._row_to_run(row)

    def save_feedback(self, feedback: FeedbackRecord) -> None:
        with self._connect() as connection:
            connection.execute(
                """
                INSERT INTO feedback (
                    feedback_id,
                    run_id,
                    source_kind,
                    source_id,
                    signal_type,
                    signal_value,
                    recorded_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(feedback_id) DO UPDATE SET
                    run_id = excluded.run_id,
                    source_kind = excluded.source_kind,
                    source_id = excluded.source_id,
                    signal_type = excluded.signal_type,
                    signal_value = excluded.signal_value,
                    recorded_at = excluded.recorded_at
                """,
                (
                    feedback.feedback_id,
                    feedback.run_id,
                    feedback.source_kind,
                    feedback.source_id,
                    feedback.signal_type,
                    feedback.signal_value,
                    feedback.recorded_at.isoformat(),
                ),
            )

    def list_feedback(self, run_id: Optional[str] = None) -> Sequence[FeedbackRecord]:
        query = """
            SELECT feedback_id, run_id, source_kind, source_id, signal_type, signal_value, recorded_at
            FROM feedback
        """
        params = ()
        if run_id is not None:
            query += " WHERE run_id = ?"
            params = (run_id,)
        query += " ORDER BY recorded_at"
        with self._connect() as connection:
            rows = connection.execute(query, params).fetchall()
        return tuple(
            FeedbackRecord(
                feedback_id=row["feedback_id"],
                run_id=row["run_id"],
                source_kind=row["source_kind"],
                source_id=row["source_id"],
                signal_type=row["signal_type"],
                signal_value=row["signal_value"],
                recorded_at=parse_datetime(row["recorded_at"]),
            )
            for row in rows
        )

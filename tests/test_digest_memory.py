from datetime import datetime, timezone

from day_captain.digest_memory import annotate_with_recent_memory
from day_captain.models import DigestEntry, DigestPayload, DigestRunRecord


def _entry(source_id: str, section: str = "actions_to_take") -> DigestEntry:
    return DigestEntry(
        title="Project decision",
        summary="Please confirm the project decision.",
        section_name=section,
        source_kind="message",
        source_id=source_id,
        score=2.0,
        recommended_action="Confirm the project decision.",
        context_metadata={"stable_thread_id": "thread-1"},
    )


def _run(entry: DigestEntry) -> DigestRunRecord:
    now = datetime(2026, 7, 12, tzinfo=timezone.utc)
    payload = DigestPayload(
        run_id="previous",
        generated_at=now,
        window_start=now,
        window_end=now,
        delivery_mode="json",
        actions_to_take=(entry,) if entry.section_name == "actions_to_take" else (),
        watch_items=(entry,) if entry.section_name == "watch_items" else (),
    )
    return DigestRunRecord("previous", "morning_digest", "completed", now, now, now, "json", payload)


def test_tracks_same_thread_when_graph_message_id_changes() -> None:
    current = _entry("new-message")

    items, _ = annotate_with_recent_memory((current,), (_run(_entry("old-message")),))

    assert items[0].card.continuity_state == "still_open"


def test_suppresses_unchanged_watch_item_from_same_thread() -> None:
    current = _entry("new-message", section="watch_items")

    items, _ = annotate_with_recent_memory((current,), (_run(_entry("old-message", section="watch_items")),))

    assert items == ()


def test_marks_explicit_elapsed_noon_deadline_overdue() -> None:
    current = _entry("new-message")
    current = DigestEntry(**{**current.__dict__, "context_metadata": {"stable_thread_id": "thread-1", "due_hint": "before noon"}})

    items, _ = annotate_with_recent_memory(
        (current,),
        (_run(_entry("old-message")),),
        reference_time=datetime(2026, 7, 12, 13, 0, tzinfo=timezone.utc),
    )

    assert items[0].card.continuity_state == "overdue"

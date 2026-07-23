from day_captain.digest_metrics import digest_metrics
from day_captain.digest_metrics import digest_debug_report
from day_captain.models import DigestEntry, MessageRecord
from day_captain.replay import run_synthetic_replay
from day_captain.services import enrich_digest_candidates, filter_digest_items_for_usefulness


def test_synthetic_replay_is_safe_and_covers_critical_cases() -> None:
    first, second, no_work, rich_context, weekly = run_synthetic_replay()
    rendered = repr((first, second, no_work, rich_context, weekly))

    assert "123456" not in rendered
    assert "entertainment newsletter" not in rendered.lower()
    assert first.critical_topics[0].source_id == "alert-1"
    assert any(item.context_metadata.get("due_hint") == "before noon" for item in first.actions_to_take)
    assert all("meeting_conflict" in item.reason_codes for item in first.upcoming_meetings)
    assert second.actions_to_take[0].card.continuity_state == "still_open"
    assert not no_work.critical_topics and not no_work.actions_to_take
    assert "urgent" in no_work.top_summary.lower()
    assert "launch checklist" in rich_context.actions_to_take[0].summary
    assert rich_context.actions_to_take[0].context_metadata["rich_context_used"] is True
    assert "weekly brief" in weekly.delivery_subject
    assert digest_metrics((first, second, no_work, rich_context, weekly))["sensitive_suppressions"] == 9
    debug = digest_debug_report((first, second, no_work, rich_context, weekly))
    assert debug["usefulness"]["critical_failures"] >= 1
    assert debug["usefulness"]["no_meaningful_work_briefs"] >= 1
    assert debug["briefs"][0]["cards"][0]["reason_codes"]

    assert "secure link" not in rendered.lower()
    assert "sign in" not in rendered.lower()


def test_rich_context_enrichment_is_bounded_and_synthetic_only() -> None:
    items = (
        DigestEntry("A", "Vague.", "actions_to_take", "message", "a", 3.0, reason_codes=("action_keyword",)),
        DigestEntry("B", "Vague.", "actions_to_take", "message", "b", 2.0, reason_codes=("action_keyword",)),
    )
    messages = (
        MessageRecord("a", "ta", "A", "lead@example.test", body_preview="Vague.", raw_payload={"dayCaptainSyntheticRichContext": "Please validate the launch checklist before noon."}),
        MessageRecord("b", "tb", "B", "lead@example.test", body_preview="Vague.", raw_payload={"dayCaptainSyntheticRichContext": "Please validate the budget before noon."}),
    )

    enriched = enrich_digest_candidates(items, messages, limit=1)

    assert "launch checklist" in enriched[0].summary
    assert enriched[0].context_metadata["rich_context_used"] is True
    assert "rich_context" in enriched[0].reason_codes
    assert enriched[1].summary == "Vague."


def test_usefulness_filter_downgrades_generic_action_and_suppresses_unsupported_watch() -> None:
    filtered, metrics = filter_digest_items_for_usefulness(
        (
            DigestEntry("Generic", "Summary.", "actions_to_take", "message", "a", 2.0, "Reply or confirm the request.", reason_codes=("action_keyword",)),
            DigestEntry("Weak", "Summary.", "watch_items", "message", "b", 1.0),
        )
    )

    assert len(filtered) == 1
    assert filtered[0].section_name == "watch_items"
    assert filtered[0].recommended_action == ""
    assert metrics == {"unsupported_action_downgrades": 1, "unsupported_watch_suppressions": 1}

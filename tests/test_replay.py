from day_captain.digest_metrics import digest_metrics
from day_captain.replay import run_synthetic_replay


def test_synthetic_replay_is_safe_and_covers_critical_cases() -> None:
    first, second = run_synthetic_replay()
    rendered = repr((first, second))

    assert "123456" not in rendered
    assert "entertainment newsletter" not in rendered.lower()
    assert first.critical_topics[0].source_id == "alert-1"
    assert any(item.context_metadata.get("due_hint") == "before noon" for item in first.actions_to_take)
    assert all("meeting_conflict" in item.reason_codes for item in first.upcoming_meetings)
    assert second.actions_to_take[0].card.continuity_state == "still_open"
    assert digest_metrics((first, second))["sensitive_suppressions"] == 2

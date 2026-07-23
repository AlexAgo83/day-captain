from datetime import datetime, timezone

from day_captain.digest_metrics import candidate_gate, digest_debug_report, digest_metrics
from day_captain.models import DigestEntry, DigestPayload


def test_reports_only_versioned_aggregate_metrics() -> None:
    now = datetime(2026, 7, 12, tzinfo=timezone.utc)
    payload = DigestPayload(
        run_id="synthetic-run",
        generated_at=now,
        window_start=now,
        window_end=now,
        delivery_mode="json",
        delivery_body="Synthetic visible brief",
        actions_to_take=(DigestEntry("Decision", "Synthetic", "actions_to_take", "message", "message-1", 2.0, "Reply or confirm the request."),),
        delivery_payload={"usefulness_metrics": {"sensitive_suppressions": 2}},
    )

    report = digest_metrics((payload,))

    assert report == {
        "metrics_version": "1.2",
        "briefs": 1,
        "median_visible_characters": 23,
        "rendered_cards": 1,
        "generic_actions": 1,
        "risk_warnings": 0,
        "external_news_items": 0,
        "confidence_label_count": 0,
        "source_open_control_count": 0,
        "sensitive_suppressions": 2,
        "repeated_unchanged_suppressions": 0,
        "usefulness": {
            "concrete_next_steps": 0,
            "owner_clear": 0,
            "due_signals": 0,
            "change_signals": 0,
            "critical_failures": 0,
            "meeting_conflicts": 0,
            "unsupported_watch": 0,
            "no_meaningful_work_briefs": 1,
        },
    }


def test_candidate_gate_compares_per_brief_rates_to_versioned_baseline() -> None:
    result = candidate_gate({"briefs": 2, "median_visible_characters": 1804, "generic_actions": 0})

    assert result["baseline_version"] == "public-safe-baseline-v1"
    assert result["passed"] is True
    assert result["checks"] == {
        "visible_length_reduction_at_least_40_percent": True,
        "generic_action_reduction_at_least_80_percent": True,
    }


def test_debug_report_explains_cards_without_mailbox_content() -> None:
    now = datetime(2026, 7, 12, tzinfo=timezone.utc)
    payload = DigestPayload(
        run_id="synthetic-run",
        generated_at=now,
        window_start=now,
        window_end=now,
        delivery_mode="json",
        delivery_body="Synthetic visible brief",
        actions_to_take=(
            DigestEntry(
                "Private raw subject should not appear",
                "Private raw body should not appear",
                "actions_to_take",
                "message",
                "message-1",
                2.0,
                "Reply to Lead about Decision before noon.",
                context_metadata={"action_owner": "user", "due_hint": "before noon"},
                reason_codes=("action_keyword",),
            ),
        ),
    )

    report = digest_debug_report((payload,))
    rendered = repr(report)

    assert "Private raw subject" not in rendered
    assert "Private raw body" not in rendered
    assert report["briefs"][0]["cards"][0]["owner"] == "user"
    assert report["briefs"][0]["cards"][0]["has_due_signal"] is True
    assert report["usefulness"]["concrete_next_steps"] == 1

from datetime import datetime, timezone

from day_captain.digest_metrics import digest_metrics
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
        "metrics_version": "1.0",
        "briefs": 1,
        "median_visible_characters": 23,
        "rendered_cards": 1,
        "generic_actions": 1,
        "risk_warnings": 0,
        "external_news_items": 0,
        "sensitive_suppressions": 2,
    }

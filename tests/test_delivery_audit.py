from day_captain.delivery_audit import delivery_count_audit


def test_delivery_count_audit_reports_content_free_anomalies() -> None:
    report = delivery_count_audit(
        (
            {"sent_at": "2026-07-23T06:45:01Z", "edition": "daily", "to_count": 1, "cc_count": 0, "bcc_count": 0},
            {"sent_at": "2026-07-23T06:45:12Z", "edition": "daily", "to_count": 1, "cc_count": 0, "bcc_count": 0},
            {"sent_at": "2026-07-23T06:45:30Z", "edition": "daily", "to_count": 1, "cc_count": 0, "bcc_count": 0},
        ),
        expected_targets=2,
    )

    assert report["passed"] is False
    assert report["findings"][0]["kind"] == "duplicate_or_retry_overlap"
    assert "subject" not in repr(report).lower()
    assert "recipient" not in repr(report).lower()


def test_delivery_count_audit_passes_expected_single_recipient_fanout() -> None:
    report = delivery_count_audit(
        (
            {"sent_at": "2026-07-23T06:45:01Z", "edition": "daily", "to_count": 1, "cc_count": 0, "bcc_count": 0},
            {"sent_at": "2026-07-23T06:45:12Z", "edition": "daily", "to_count": 1, "cc_count": 0, "bcc_count": 0},
        ),
        expected_targets=2,
    )

    assert report["passed"] is True
    assert report["findings"] == []

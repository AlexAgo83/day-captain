"""Content-free delivery count diagnostics."""

from collections import Counter
from datetime import datetime
from typing import Mapping, Sequence

from day_captain.models import parse_datetime


def _parse_sent_at(record: Mapping[str, object]) -> datetime:
    return parse_datetime(str(record.get("sent_at") or record.get("sentDateTime") or "1970-01-01T00:00:00+00:00"))


def _edition(record: Mapping[str, object]) -> str:
    candidate = str(record.get("edition") or record.get("run_type") or "").strip().lower()
    if candidate in {"weekly", "weekly_digest"}:
        return "weekly"
    return "daily"


def _bucket_key(record: Mapping[str, object]) -> tuple[str, str]:
    sent_at = _parse_sent_at(record)
    return (_edition(record), sent_at.strftime("%Y-%m-%dT%H:%M"))


def delivery_count_audit(records: Sequence[Mapping[str, object]], *, expected_targets: int) -> Mapping[str, object]:
    expected = max(0, int(expected_targets))
    buckets = Counter(_bucket_key(record) for record in records)
    fanout_shapes = Counter(
        (
            int(record.get("to_count") or 0),
            int(record.get("cc_count") or 0),
            int(record.get("bcc_count") or 0),
        )
        for record in records
    )
    findings = []
    for (edition, bucket), count in sorted(buckets.items()):
        if expected and count > expected:
            findings.append({"kind": "duplicate_or_retry_overlap", "edition": edition, "bucket": bucket, "expected": expected, "observed": count})
        elif expected and count < expected:
            findings.append({"kind": "missing_target_send", "edition": edition, "bucket": bucket, "expected": expected, "observed": count})
    mixed_editions = {}
    by_day = {}
    for record in records:
        day = _parse_sent_at(record).strftime("%Y-%m-%d")
        by_day.setdefault(day, set()).add(_edition(record))
    for day, editions in by_day.items():
        if len(editions) > 1:
            mixed_editions[day] = sorted(editions)
    for day, editions in mixed_editions.items():
        findings.append({"kind": "daily_weekly_overlap", "day": day, "editions": editions})
    return {
        "audit_version": "1.0",
        "expected_targets": expected,
        "observed_messages": len(records),
        "buckets": [
            {"edition": edition, "bucket": bucket, "observed": count}
            for (edition, bucket), count in sorted(buckets.items())
        ],
        "fanout_shapes": [
            {"to_count": shape[0], "cc_count": shape[1], "bcc_count": shape[2], "messages": count}
            for shape, count in sorted(fanout_shapes.items())
        ],
        "findings": findings,
        "passed": not findings and all(shape == (1, 0, 0) for shape in fanout_shapes),
    }

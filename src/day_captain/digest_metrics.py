"""Content-free, versioned digest usefulness metrics."""

from typing import Mapping, Sequence

from day_captain.models import DigestPayload


METRICS_VERSION = "1.0"
PRODUCTION_BASELINE_V1 = {
    "baseline_version": "public-safe-baseline-v1",
    "briefs": 118,
    "median_visible_characters": 5455,
    "generic_actions": 869,
}
GENERIC_ACTIONS = (
    "reply or confirm",
    "répondre ou confirmer",
    "review or handle quickly",
    "examiner ou traiter rapidement",
    "keep this topic in view",
    "garder ce sujet en vue",
)


def digest_metrics(payloads: Sequence[DigestPayload]) -> Mapping[str, object]:
    visible_lengths = []
    card_count = generic_actions = risk_warnings = news_items = sensitive_suppressions = repeated_suppressions = 0
    for payload in payloads:
        entries = tuple(payload.critical_topics) + tuple(payload.actions_to_take) + tuple(payload.watch_items) + tuple(payload.daily_presence) + tuple(payload.upcoming_meetings)
        visible_lengths.append(len(payload.delivery_body))
        card_count += len(entries)
        generic_actions += sum(
            1 for item in entries if any(pattern in item.recommended_action.lower() for pattern in GENERIC_ACTIONS)
        )
        risk_warnings += sum(1 for item in entries if item.card and item.card.risk_level in {"medium", "high"})
        news_items += len(payload.external_news)
        metrics = payload.delivery_payload.get("usefulness_metrics") or {}
        sensitive_suppressions += int(metrics.get("sensitive_suppressions") or 0)
        repeated_suppressions += int(metrics.get("repeated_unchanged_suppressions") or 0)
    ordered_lengths = sorted(visible_lengths)
    median_length = ordered_lengths[len(ordered_lengths) // 2] if ordered_lengths else 0
    return {
        "metrics_version": METRICS_VERSION,
        "briefs": len(payloads),
        "median_visible_characters": median_length,
        "rendered_cards": card_count,
        "generic_actions": generic_actions,
        "risk_warnings": risk_warnings,
        "external_news_items": news_items,
        "sensitive_suppressions": sensitive_suppressions,
        "repeated_unchanged_suppressions": repeated_suppressions,
    }


def candidate_gate(candidate: Mapping[str, object], baseline: Mapping[str, object] = PRODUCTION_BASELINE_V1) -> Mapping[str, object]:
    baseline_briefs = max(1, int(baseline["briefs"]))
    candidate_briefs = max(1, int(candidate["briefs"]))
    length_reduction = 1 - (int(candidate["median_visible_characters"]) / int(baseline["median_visible_characters"]))
    baseline_generic_rate = int(baseline["generic_actions"]) / baseline_briefs
    candidate_generic_rate = int(candidate["generic_actions"]) / candidate_briefs
    generic_reduction = 1 - (candidate_generic_rate / baseline_generic_rate)
    checks = {
        "visible_length_reduction_at_least_40_percent": length_reduction >= 0.40,
        "generic_action_reduction_at_least_80_percent": generic_reduction >= 0.80,
    }
    return {
        "baseline_version": baseline["baseline_version"],
        "passed": all(checks.values()),
        "checks": checks,
        "visible_length_reduction": round(length_reduction, 4),
        "generic_action_reduction": round(generic_reduction, 4),
    }

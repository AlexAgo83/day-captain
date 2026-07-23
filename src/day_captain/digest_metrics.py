"""Content-free, versioned digest usefulness metrics."""

from typing import Mapping, Sequence

from day_captain.models import DigestEntry
from day_captain.models import DigestPayload


METRICS_VERSION = "1.2"
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
USEFUL_WATCH_REASONS = {
    "changed",
    "critical_keyword",
    "flagged",
    "meeting_conflict",
    "overdue",
    "preference_signal",
    "still_open",
    "transactional_alert",
    "waiting",
}


def _entries(payload: DigestPayload) -> Sequence[DigestEntry]:
    return (
        tuple(payload.critical_topics)
        + tuple(payload.actions_to_take)
        + tuple(payload.team_actions)
        + tuple(payload.watch_items)
        + tuple(payload.daily_presence)
        + tuple(payload.upcoming_meetings)
    )


def _is_generic_action(value: str) -> bool:
    normalized = str(value or "").lower()
    return any(pattern in normalized for pattern in GENERIC_ACTIONS)


def _action_owner(item: DigestEntry) -> str:
    if item.card is not None and item.card.action_owner:
        return item.card.action_owner
    return str((item.context_metadata or {}).get("action_owner") or "").strip()


def _continuity_state(item: DigestEntry) -> str:
    if item.card is not None and item.card.continuity_state:
        return item.card.continuity_state
    return str((item.context_metadata or {}).get("continuity_state") or "").strip()


def _has_due_signal(item: DigestEntry) -> bool:
    metadata = item.context_metadata or {}
    return bool(metadata.get("due_hint") or metadata.get("due_at") or "overdue" in item.reason_codes)


def _has_concrete_next_step(item: DigestEntry) -> bool:
    action = str(item.recommended_action or "").strip()
    return bool(action and not _is_generic_action(action))


def _is_unsupported_watch(item: DigestEntry) -> bool:
    if item.section_name != "watch_items":
        return False
    if item.recommended_action and not _is_generic_action(item.recommended_action):
        return False
    return not bool(set(item.reason_codes) & USEFUL_WATCH_REASONS or _continuity_state(item) or _has_due_signal(item))


def usefulness_metrics(payloads: Sequence[DigestPayload]) -> Mapping[str, object]:
    concrete_next_steps = owner_clear = due_signals = change_signals = 0
    critical_failures = meeting_conflicts = unsupported_watch = no_meaningful_work = 0
    for payload in payloads:
        entries = _entries(payload)
        meaningful = False
        for item in entries:
            concrete = _has_concrete_next_step(item)
            due = _has_due_signal(item)
            continuity = _continuity_state(item)
            reasons = set(item.reason_codes)
            concrete_next_steps += int(concrete)
            owner_clear += int(_action_owner(item) in {"user", "shared", "other"})
            due_signals += int(due)
            change_signals += int(continuity in {"changed", "still_open", "waiting", "overdue"} or bool(reasons & {"changed", "still_open", "waiting", "overdue"}))
            critical_failures += int("transactional_alert" in reasons)
            meeting_conflicts += int("meeting_conflict" in reasons)
            unsupported_watch += int(_is_unsupported_watch(item))
            meaningful = meaningful or concrete or due or item.guardrail_applied or bool(reasons & {"transactional_alert", "meeting_conflict", "flagged", "changed", "overdue"})
        no_meaningful_work += int(not meaningful)
    return {
        "concrete_next_steps": concrete_next_steps,
        "owner_clear": owner_clear,
        "due_signals": due_signals,
        "change_signals": change_signals,
        "critical_failures": critical_failures,
        "meeting_conflicts": meeting_conflicts,
        "unsupported_watch": unsupported_watch,
        "no_meaningful_work_briefs": no_meaningful_work,
    }


def digest_metrics(payloads: Sequence[DigestPayload]) -> Mapping[str, object]:
    visible_lengths = []
    card_count = generic_actions = risk_warnings = news_items = sensitive_suppressions = repeated_suppressions = 0
    confidence_labels = source_open_controls = 0
    for payload in payloads:
        entries = _entries(payload)
        visible_lengths.append(len(payload.delivery_body))
        card_count += len(entries)
        generic_actions += sum(1 for item in entries if _is_generic_action(item.recommended_action))
        risk_warnings += sum(1 for item in entries if item.card and item.card.risk_level in {"medium", "high"})
        news_items += len(payload.external_news)
        confidence_labels += sum(1 for item in entries if item.confidence_label and item.confidence_score < 90)
        source_open_controls += sum(1 for item in entries if item.source_url or item.desktop_source_url)
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
        "confidence_label_count": confidence_labels,
        "source_open_control_count": source_open_controls,
        "sensitive_suppressions": sensitive_suppressions,
        "repeated_unchanged_suppressions": repeated_suppressions,
        "usefulness": usefulness_metrics(payloads),
    }


def digest_debug_report(payloads: Sequence[DigestPayload]) -> Mapping[str, object]:
    reports = []
    for payload in payloads:
        cards = []
        for item in _entries(payload):
            cards.append(
                {
                    "section": item.section_name,
                    "source_kind": item.source_kind,
                    "score_bucket": "high" if item.score >= 3 else "medium" if item.score >= 1.5 else "low",
                    "reason_codes": list(item.reason_codes),
                    "owner": _action_owner(item),
                    "confidence": item.confidence_label,
                    "continuity_state": _continuity_state(item),
                    "has_concrete_next_step": _has_concrete_next_step(item),
                    "has_due_signal": _has_due_signal(item),
                    "has_source_open": bool(item.source_url or item.desktop_source_url),
                    "guardrail": bool(item.guardrail_applied),
                    "unsupported_watch": _is_unsupported_watch(item),
                }
            )
        metrics = payload.delivery_payload.get("usefulness_metrics") or {}
        reports.append(
            {
                "run_id": payload.run_id,
                "run_type": str(payload.delivery_payload.get("run_type") or ""),
                "subject_kind": "weekly" if "weekly" in payload.delivery_subject.lower() else "daily",
                "card_count": len(cards),
                "cards": cards,
                "suppressions": {
                    "sensitive": int(metrics.get("sensitive_suppressions") or 0),
                    "repeated_unchanged": int(metrics.get("repeated_unchanged_suppressions") or 0),
                },
            }
        )
    return {
        "debug_version": METRICS_VERSION,
        "briefs": reports,
        "usefulness": usefulness_metrics(payloads),
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

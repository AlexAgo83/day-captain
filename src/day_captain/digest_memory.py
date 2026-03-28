"""Short-term digest memory helpers."""

from dataclasses import replace
from datetime import datetime
from typing import Mapping
from typing import Sequence

from day_captain.models import DigestCard
from day_captain.models import DigestEntry
from day_captain.models import DigestRunRecord


def _item_key(item: DigestEntry) -> tuple[str, str]:
    return (item.source_kind, item.source_id)


def _with_card(item: DigestEntry, *, card: DigestCard) -> DigestEntry:
    return replace(item, card=card)


def annotate_with_recent_memory(
    items: Sequence[DigestEntry],
    recent_runs: Sequence[DigestRunRecord],
) -> tuple[Sequence[DigestEntry], Sequence[Mapping[str, str]]]:
    current_by_key = {_item_key(item): item for item in items}
    latest_prior = recent_runs[0] if recent_runs else None
    prior_by_key = {}
    for run in recent_runs:
        for section in (
            run.summary.critical_topics,
            run.summary.actions_to_take,
            run.summary.watch_items,
            run.summary.daily_presence,
            run.summary.upcoming_meetings,
        ):
            for item in section:
                prior_by_key.setdefault(_item_key(item), item)

    updated = []
    for item in items:
        previous = prior_by_key.get(_item_key(item))
        if previous is None:
            updated.append(item)
            continue
        continuity_state = "already_surfaced"
        continuity_reason = "Seen in a recent digest run."
        if latest_prior is not None:
            latest_previous = None
            for section in (
                latest_prior.summary.critical_topics,
                latest_prior.summary.actions_to_take,
                latest_prior.summary.watch_items,
                latest_prior.summary.daily_presence,
                latest_prior.summary.upcoming_meetings,
            ):
                for candidate in section:
                    if _item_key(candidate) == _item_key(item):
                        latest_previous = candidate
                        break
                if latest_previous is not None:
                    break
            if latest_previous is not None:
                if latest_previous.summary != item.summary or latest_previous.recommended_action != item.recommended_action:
                    continuity_state = "changed"
                    continuity_reason = "The item was surfaced recently and its interpretation changed."
                elif item.section_name in {"critical_topics", "actions_to_take"}:
                    continuity_state = "still_open"
                    continuity_reason = "The item was surfaced recently and still looks active."
        existing = item.card or DigestCard()
        updated.append(
            _with_card(
                item,
                card=replace(
                    existing,
                    continuity_state=continuity_state,
                    continuity_previous_date=previous.sort_at.date().isoformat() if previous.sort_at is not None else "",
                    continuity_reason=continuity_reason,
                ),
            )
        )

    cleared = []
    if latest_prior is not None:
        for section in (
            latest_prior.summary.critical_topics,
            latest_prior.summary.actions_to_take,
            latest_prior.summary.watch_items,
            latest_prior.summary.daily_presence,
            latest_prior.summary.upcoming_meetings,
        ):
            for previous in section:
                if _item_key(previous) in current_by_key:
                    continue
                cleared.append(
                    {
                        "source_kind": previous.source_kind,
                        "source_id": previous.source_id,
                        "title": previous.title,
                        "section_name": previous.section_name,
                        "state": "cleared",
                    }
                )
    return tuple(updated), tuple(cleared)

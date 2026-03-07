"""CLI entrypoints for Day Captain."""

import argparse
from datetime import date
from datetime import datetime
import json
from typing import Optional

from day_captain.app import build_application
from day_captain.models import to_jsonable


def _parse_datetime(value: Optional[str]) -> Optional[datetime]:
    if not value:
        return None
    return datetime.fromisoformat(value)


def _parse_date(value: Optional[str]) -> Optional[date]:
    if not value:
        return None
    return date.fromisoformat(value)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="day-captain")
    subparsers = parser.add_subparsers(dest="command", required=True)

    morning = subparsers.add_parser("morning-digest", help="Run the morning digest flow.")
    morning.add_argument("--now", help="ISO datetime override for the run clock.")
    morning.add_argument("--delivery-mode", help="Override the configured delivery mode.")
    morning.add_argument("--force", action="store_true", help="Ignore the last successful run window.")

    recall = subparsers.add_parser("recall-digest", help="Recall the latest completed digest.")
    recall.add_argument("--run-id", help="Specific digest run identifier.")
    recall.add_argument("--day", help="ISO date used to find the latest run for a day.")

    feedback = subparsers.add_parser("record-feedback", help="Record user feedback on a digest item.")
    feedback.add_argument("--run-id", required=True)
    feedback.add_argument("--source-kind", required=True)
    feedback.add_argument("--source-id", required=True)
    feedback.add_argument("--signal-type", required=True)
    feedback.add_argument("--signal-value", required=True)
    feedback.add_argument("--recorded-at", help="ISO datetime for the feedback event.")

    return parser


def main(argv: Optional[list] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    app = build_application()

    if args.command == "morning-digest":
        result = app.run_morning_digest(
            now=_parse_datetime(args.now),
            delivery_mode=args.delivery_mode,
            force=args.force,
        )
    elif args.command == "recall-digest":
        result = app.recall_digest(
            run_id=args.run_id,
            day=_parse_date(args.day),
        )
    else:
        result = app.record_feedback(
            run_id=args.run_id,
            source_kind=args.source_kind,
            source_id=args.source_id,
            signal_type=args.signal_type,
            signal_value=args.signal_value,
            recorded_at=_parse_datetime(args.recorded_at),
        )

    print(json.dumps(to_jsonable(result), indent=2, sort_keys=True))
    return 0

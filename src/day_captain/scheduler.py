"""Scheduler helper functions shared by tests and ops workflows."""

from datetime import datetime
from datetime import timezone
from typing import Optional
from zoneinfo import ZoneInfo


def _resolve_scheduled_utc_time(now: Optional[datetime], trigger_schedule: Optional[str]) -> datetime:
    current_time = now or datetime.now(timezone.utc)
    if current_time.tzinfo is None:
        current_time = current_time.replace(tzinfo=timezone.utc)

    if not trigger_schedule:
        return current_time

    schedule_fields = trigger_schedule.split()
    if len(schedule_fields) < 2:
        return current_time

    minute_field, hour_field = schedule_fields[:2]
    if not (minute_field.isdigit() and hour_field.isdigit()):
        return current_time

    return current_time.replace(hour=int(hour_field), minute=int(minute_field), second=0, microsecond=0)


def should_run_sunday_weekly_digest(
    now: Optional[datetime] = None,
    *,
    timezone_name: str = "Europe/Paris",
    target_hour: int = 20,
    target_minute: int = 30,
    trigger_schedule: Optional[str] = None,
) -> bool:
    current_time = _resolve_scheduled_utc_time(now, trigger_schedule)
    local_now = current_time.astimezone(ZoneInfo(timezone_name))
    return (
        local_now.weekday() == 6
        and local_now.hour == target_hour
        and local_now.minute >= target_minute
    )


def should_run_weekday_morning_digest(
    now: Optional[datetime] = None,
    *,
    timezone_name: str = "Europe/Paris",
    target_hour: int = 8,
    target_minute: int = 45,
    trigger_schedule: Optional[str] = None,
) -> bool:
    current_time = _resolve_scheduled_utc_time(now, trigger_schedule)
    local_now = current_time.astimezone(ZoneInfo(timezone_name))
    return (
        local_now.weekday() < 5
        and local_now.hour == target_hour
        and local_now.minute >= target_minute
    )

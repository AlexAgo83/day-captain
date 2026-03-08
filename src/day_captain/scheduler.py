"""Scheduler helper functions shared by tests and ops workflows."""

from datetime import datetime
from datetime import timezone
from typing import Optional
from zoneinfo import ZoneInfo


def should_run_sunday_weekly_digest(
    now: Optional[datetime] = None,
    *,
    timezone_name: str = "Europe/Paris",
    target_hour: int = 20,
    target_minute: int = 30,
) -> bool:
    current_time = now or datetime.now(timezone.utc)
    if current_time.tzinfo is None:
        current_time = current_time.replace(tzinfo=timezone.utc)
    local_now = current_time.astimezone(ZoneInfo(timezone_name))
    return (
        local_now.weekday() == 6
        and local_now.hour == target_hour
        and local_now.minute >= target_minute
    )

"""Configuration loading for Day Captain."""

from dataclasses import dataclass
import os
from typing import Tuple


def _parse_bool(value: str, default: bool = False) -> bool:
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def _parse_scopes(value: str) -> Tuple[str, ...]:
    if not value:
        return ("Mail.Read", "Calendars.Read")
    parts = [part.strip() for part in value.split(",")]
    return tuple(part for part in parts if part)


@dataclass(frozen=True)
class DayCaptainSettings:
    environment: str = "development"
    sqlite_path: str = "day_captain.sqlite3"
    delivery_mode: str = "json"
    default_lookback_hours: int = 24
    graph_base_url: str = "https://graph.microsoft.com/v1.0"
    graph_access_token: str = ""
    graph_tenant_id: str = ""
    graph_client_id: str = ""
    graph_client_secret: str = ""
    graph_user_id: str = ""
    graph_send_enabled: bool = False
    graph_timeout_seconds: int = 30
    graph_scopes: Tuple[str, ...] = ("Mail.Read", "Calendars.Read")

    @classmethod
    def from_env(cls) -> "DayCaptainSettings":
        return cls(
            environment=os.getenv("DAY_CAPTAIN_ENV", "development"),
            sqlite_path=os.getenv("DAY_CAPTAIN_SQLITE_PATH", "day_captain.sqlite3"),
            delivery_mode=os.getenv("DAY_CAPTAIN_DELIVERY_MODE", "json"),
            default_lookback_hours=int(os.getenv("DAY_CAPTAIN_DEFAULT_LOOKBACK_HOURS", "24")),
            graph_base_url=os.getenv("DAY_CAPTAIN_GRAPH_BASE_URL", "https://graph.microsoft.com/v1.0"),
            graph_access_token=os.getenv("DAY_CAPTAIN_GRAPH_ACCESS_TOKEN", ""),
            graph_tenant_id=os.getenv("DAY_CAPTAIN_GRAPH_TENANT_ID", ""),
            graph_client_id=os.getenv("DAY_CAPTAIN_GRAPH_CLIENT_ID", ""),
            graph_client_secret=os.getenv("DAY_CAPTAIN_GRAPH_CLIENT_SECRET", ""),
            graph_user_id=os.getenv("DAY_CAPTAIN_GRAPH_USER_ID", ""),
            graph_send_enabled=_parse_bool(os.getenv("DAY_CAPTAIN_GRAPH_SEND_ENABLED"), default=False),
            graph_timeout_seconds=int(os.getenv("DAY_CAPTAIN_GRAPH_TIMEOUT_SECONDS", "30")),
            graph_scopes=_parse_scopes(os.getenv("DAY_CAPTAIN_GRAPH_SCOPES", "")),
        )

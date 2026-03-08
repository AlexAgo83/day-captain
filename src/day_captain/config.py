"""Configuration loading for Day Captain."""

from dataclasses import dataclass
import os
from typing import Sequence
from urllib.parse import parse_qsl
from urllib.parse import urlencode
from urllib.parse import urlparse
from urllib.parse import urlunparse
from typing import Tuple


def _parse_bool(value: str, default: bool = False) -> bool:
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def _parse_scopes(value: str) -> Tuple[str, ...]:
    if not value:
        return ("User.Read", "Mail.Read", "Calendars.Read")
    parts = [part.strip() for part in value.split(",")]
    scopes = [part for part in parts if part]
    if "User.Read" not in scopes:
        scopes.insert(0, "User.Read")
    return tuple(scopes)


def _parse_csv(value: str) -> Tuple[str, ...]:
    if not value:
        return ()
    return tuple(part.strip() for part in value.split(",") if part.strip())


def _normalize_graph_auth_mode(value: str, default: str = "delegated") -> str:
    candidate = (value or "").strip().lower()
    if candidate in {"delegated", "app_only", "auto"}:
        return candidate
    return default


def _normalize_language(value: str, default: str = "en") -> str:
    candidate = (value or "").strip().lower()
    if candidate in {"en", "fr"}:
        return candidate
    return default


@dataclass(frozen=True)
class DayCaptainSettings:
    environment: str = "development"
    sqlite_path: str = "day_captain.sqlite3"
    database_url: str = ""
    database_ssl_mode: str = "prefer"
    http_host: str = "0.0.0.0"
    http_port: int = 8000
    job_secret: str = ""
    delivery_mode: str = "json"
    default_lookback_hours: int = 24
    graph_auth_mode: str = "delegated"
    graph_tenant_id: str = "common"
    graph_client_id: str = ""
    graph_client_secret: str = ""
    graph_refresh_token: str = ""
    graph_auth_cache_path: str = ".day_captain_auth.json"
    graph_base_url: str = "https://graph.microsoft.com/v1.0"
    graph_access_token: str = ""
    graph_user_id: str = ""
    target_users: Tuple[str, ...] = ()
    graph_send_enabled: bool = False
    graph_timeout_seconds: int = 30
    graph_scopes: Tuple[str, ...] = ("User.Read", "Mail.Read", "Calendars.Read")
    display_timezone: str = "UTC"
    digest_language: str = "en"
    llm_language: str = ""
    llm_provider: str = "disabled"
    llm_api_key: str = ""
    llm_model: str = ""
    llm_base_url: str = "https://api.openai.com/v1"
    llm_timeout_seconds: int = 30
    llm_shortlist_limit: int = 5
    llm_max_output_tokens: int = 300
    llm_temperature: float = 0.2
    llm_enabled_sections: Tuple[str, ...] = ("critical_topics", "actions_to_take", "watch_items")
    llm_style_prompt: str = "Write like a concise executive assistant."

    @classmethod
    def from_env(cls) -> "DayCaptainSettings":
        return cls(
            environment=os.getenv("DAY_CAPTAIN_ENV", "development"),
            sqlite_path=os.getenv("DAY_CAPTAIN_SQLITE_PATH", "day_captain.sqlite3"),
            database_url=os.getenv("DAY_CAPTAIN_DATABASE_URL", ""),
            database_ssl_mode=os.getenv("DAY_CAPTAIN_DATABASE_SSL_MODE", "prefer"),
            http_host=os.getenv("DAY_CAPTAIN_HTTP_HOST", "0.0.0.0"),
            http_port=int(os.getenv("PORT", os.getenv("DAY_CAPTAIN_HTTP_PORT", "8000"))),
            job_secret=os.getenv("DAY_CAPTAIN_JOB_SECRET", ""),
            delivery_mode=os.getenv("DAY_CAPTAIN_DELIVERY_MODE", "json"),
            default_lookback_hours=int(os.getenv("DAY_CAPTAIN_DEFAULT_LOOKBACK_HOURS", "24")),
            graph_auth_mode=_normalize_graph_auth_mode(os.getenv("DAY_CAPTAIN_GRAPH_AUTH_MODE", "delegated")),
            graph_tenant_id=os.getenv("DAY_CAPTAIN_GRAPH_TENANT_ID", "common"),
            graph_client_id=os.getenv("DAY_CAPTAIN_GRAPH_CLIENT_ID", ""),
            graph_client_secret=os.getenv("DAY_CAPTAIN_GRAPH_CLIENT_SECRET", ""),
            graph_refresh_token=os.getenv("DAY_CAPTAIN_GRAPH_REFRESH_TOKEN", ""),
            graph_auth_cache_path=os.getenv("DAY_CAPTAIN_GRAPH_AUTH_CACHE_PATH", ".day_captain_auth.json"),
            graph_base_url=os.getenv("DAY_CAPTAIN_GRAPH_BASE_URL", "https://graph.microsoft.com/v1.0"),
            graph_access_token=os.getenv("DAY_CAPTAIN_GRAPH_ACCESS_TOKEN", ""),
            graph_user_id=os.getenv("DAY_CAPTAIN_GRAPH_USER_ID", ""),
            target_users=_parse_csv(os.getenv("DAY_CAPTAIN_TARGET_USERS", "")),
            graph_send_enabled=_parse_bool(os.getenv("DAY_CAPTAIN_GRAPH_SEND_ENABLED"), default=False),
            graph_timeout_seconds=int(os.getenv("DAY_CAPTAIN_GRAPH_TIMEOUT_SECONDS", "30")),
            graph_scopes=_parse_scopes(os.getenv("DAY_CAPTAIN_GRAPH_SCOPES", "")),
            display_timezone=os.getenv("DAY_CAPTAIN_DISPLAY_TIMEZONE", "UTC"),
            digest_language=_normalize_language(os.getenv("DAY_CAPTAIN_DIGEST_LANGUAGE", "en")),
            llm_language=_normalize_language(os.getenv("DAY_CAPTAIN_LLM_LANGUAGE", ""), default=""),
            llm_provider=os.getenv("DAY_CAPTAIN_LLM_PROVIDER", "disabled"),
            llm_api_key=os.getenv("DAY_CAPTAIN_LLM_API_KEY", ""),
            llm_model=os.getenv("DAY_CAPTAIN_LLM_MODEL", ""),
            llm_base_url=os.getenv("DAY_CAPTAIN_LLM_BASE_URL", "https://api.openai.com/v1"),
            llm_timeout_seconds=int(os.getenv("DAY_CAPTAIN_LLM_TIMEOUT_SECONDS", "30")),
            llm_shortlist_limit=int(os.getenv("DAY_CAPTAIN_LLM_SHORTLIST_LIMIT", "5")),
            llm_max_output_tokens=int(os.getenv("DAY_CAPTAIN_LLM_MAX_OUTPUT_TOKENS", "300")),
            llm_temperature=float(os.getenv("DAY_CAPTAIN_LLM_TEMPERATURE", "0.2")),
            llm_enabled_sections=_parse_csv(
                os.getenv(
                    "DAY_CAPTAIN_LLM_ENABLED_SECTIONS",
                    "critical_topics,actions_to_take,watch_items",
                )
            ),
            llm_style_prompt=os.getenv(
                "DAY_CAPTAIN_LLM_STYLE_PROMPT",
                "Write like a concise executive assistant.",
            ),
        )

    def graph_login_scopes(self) -> Tuple[str, ...]:
        base = ["openid", "profile", "offline_access"]
        for scope in self.graph_scopes:
            if scope not in base:
                base.append(scope)
        return tuple(base)

    def resolved_graph_auth_mode(self) -> str:
        mode = _normalize_graph_auth_mode(self.graph_auth_mode, default="delegated")
        if mode == "auto":
            if self.graph_client_secret and self.resolved_target_users():
                return "app_only"
            return "delegated"
        return mode

    def resolved_tenant_scope(self) -> str:
        return self.graph_tenant_id.strip() or "common"

    def resolved_target_users(self) -> Tuple[str, ...]:
        if self.target_users:
            return tuple(dict.fromkeys(self.target_users))
        if self.graph_user_id.strip():
            return (self.graph_user_id.strip(),)
        return ()

    def resolved_default_target_user(self) -> str:
        if self.graph_user_id.strip():
            return self.graph_user_id.strip()
        targets = self.resolved_target_users()
        if len(targets) == 1:
            return targets[0]
        return ""

    def is_hosted_environment(self) -> bool:
        return self.environment.strip().lower() in {"production", "staging"}

    def validate_hosted(self) -> None:
        if self.is_hosted_environment() and not self.job_secret:
            raise ValueError("DAY_CAPTAIN_JOB_SECRET is required in hosted environments.")

    def llm_is_enabled(self) -> bool:
        return self.llm_provider.strip().lower() not in {"", "disabled", "none"}

    def resolved_digest_language(self) -> str:
        return _normalize_language(self.digest_language, default="en")

    def resolved_llm_language(self) -> str:
        return _normalize_language(self.llm_language, default=self.resolved_digest_language())

    def resolved_database_url(self) -> str:
        if not self.database_url:
            return ""
        parsed = urlparse(self.database_url)
        if parsed.scheme not in {"postgres", "postgresql"}:
            return self.database_url
        query = dict(parse_qsl(parsed.query, keep_blank_values=True))
        sslmode = query.get("sslmode") or self.database_ssl_mode
        if sslmode:
            query["sslmode"] = sslmode
        return urlunparse(parsed._replace(query=urlencode(query)))

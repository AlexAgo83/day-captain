"""Minimal HTTP surface for hosted Day Captain execution."""

from datetime import date
from datetime import datetime
from hmac import compare_digest
import json
import logging
from typing import Callable
from typing import Iterable
from typing import Optional
from wsgiref.simple_server import make_server

from day_captain.app import build_application
from day_captain.config import DayCaptainSettings
from day_captain.models import parse_datetime
from day_captain.models import to_jsonable


JsonDict = dict
StartResponse = Callable[[str, Iterable[tuple]], None]
logger = logging.getLogger(__name__)


def _parse_datetime(value: Optional[str]) -> Optional[datetime]:
    if not value:
        return None
    return parse_datetime(str(value))


def _parse_date(value: Optional[str]) -> Optional[date]:
    if not value:
        return None
    return date.fromisoformat(value)


def _parse_bool(value, *, field_name: str) -> bool:
    if isinstance(value, bool):
        return value
    if value is None:
        return False
    if isinstance(value, (int, float)):
        return bool(value)
    if isinstance(value, str):
        candidate = value.strip().lower()
        if candidate in {"", "0", "false", "no", "off"}:
            return False
        if candidate in {"1", "true", "yes", "on"}:
            return True
    raise ValueError(f"{field_name} must be a boolean value.")


class DayCaptainWebApp:
    def __init__(self, settings: DayCaptainSettings) -> None:
        self.settings = settings

    def __call__(self, environ, start_response: StartResponse):
        method = environ.get("REQUEST_METHOD", "GET").upper()
        path = environ.get("PATH_INFO", "/")

        try:
            if path == "/healthz" and method == "GET":
                health_payload: JsonDict = {"status": "ok"}
                if self._has_valid_secret(environ):
                    health_payload["runtime"] = dict(self.settings.validation_summary())
                return self._json_response(start_response, 200, health_payload)
            if path == "/jobs/morning-digest" and method == "POST":
                self._require_secret(environ)
                payload = self._read_json(environ)
                self.settings.require_target_user_if_needed(str(payload.get("target_user_id") or ""))
                app = build_application(settings=self.settings)
                result = app.run_morning_digest(
                    now=_parse_datetime(payload.get("now")),
                    delivery_mode=payload.get("delivery_mode"),
                    force=_parse_bool(payload.get("force", False), field_name="force"),
                    target_user_id=payload.get("target_user_id"),
                )
                return self._json_response(start_response, 200, self._job_ack("morning_digest", result))
            if path == "/jobs/weekly-digest" and method == "POST":
                self._require_secret(environ)
                payload = self._read_json(environ)
                self.settings.require_target_user_if_needed(str(payload.get("target_user_id") or ""))
                app = build_application(settings=self.settings)
                result = app.run_weekly_digest(
                    now=_parse_datetime(payload.get("now")),
                    delivery_mode=payload.get("delivery_mode"),
                    target_user_id=payload.get("target_user_id"),
                )
                return self._json_response(start_response, 200, self._job_ack("weekly_digest", result))
            if path == "/jobs/recall-digest" and method == "POST":
                self._require_secret(environ)
                payload = self._read_json(environ)
                self.settings.require_target_user_if_needed(str(payload.get("target_user_id") or ""))
                app = build_application(settings=self.settings)
                result = app.recall_digest(
                    run_id=payload.get("run_id"),
                    day=_parse_date(payload.get("day")),
                    target_user_id=payload.get("target_user_id"),
                )
                return self._json_response(start_response, 200, self._job_ack("recall_digest", result))
            if path == "/jobs/email-command-recall" and method == "POST":
                self._require_secret(environ)
                payload = self._read_json(environ)
                app = build_application(settings=self.settings)
                result = app.process_email_command_recall(
                    command_message_id=str(payload.get("command_message_id") or payload.get("message_id") or ""),
                    sender_address=str(payload.get("sender_address") or ""),
                    command_text=str(payload.get("command_text") or ""),
                    subject=str(payload.get("subject") or ""),
                    body=str(payload.get("body") or ""),
                    now=_parse_datetime(payload.get("now")),
                )
                return self._json_response(start_response, 200, self._email_command_ack(result))
            return self._json_response(start_response, 404, {"error": "not_found"})
        except PermissionError as exc:
            return self._json_response(start_response, 401, {"error": str(exc)})
        except LookupError as exc:
            return self._json_response(start_response, 404, {"error": str(exc)})
        except ValueError as exc:
            return self._json_response(start_response, 400, {"error": str(exc)})
        except Exception as exc:  # pragma: no cover - defensive fallback
            logger.exception("Unhandled Day Captain web error for %s %s", method, path)
            return self._json_response(start_response, 500, {"error": "internal_error"})

    def _require_secret(self, environ) -> None:
        if not self.settings.job_secret:
            return
        if not self._has_valid_secret(environ):
            raise PermissionError("unauthorized")

    def _has_valid_secret(self, environ) -> bool:
        if not self.settings.job_secret:
            return False
        candidate = str(environ.get("HTTP_X_DAY_CAPTAIN_SECRET", "") or "")
        return compare_digest(candidate, self.settings.job_secret)

    def _read_json(self, environ) -> JsonDict:
        content_length = environ.get("CONTENT_LENGTH") or "0"
        try:
            length = int(content_length)
        except ValueError:
            length = 0
        body = environ["wsgi.input"].read(length) if length > 0 else b""
        if not body:
            return {}
        payload = json.loads(body.decode("utf-8"))
        if not isinstance(payload, dict):
            raise ValueError("Request body must be a JSON object.")
        return payload

    def _json_response(self, start_response: StartResponse, status_code: int, payload) -> list:
        body = json.dumps(to_jsonable(payload), indent=2, sort_keys=True).encode("utf-8")
        headers = [
            ("Content-Type", "application/json"),
            ("Content-Length", str(len(body))),
        ]
        start_response("{0} {1}".format(status_code, _status_text(status_code)), headers)
        return [body]

    def _job_ack(self, job_name: str, payload) -> JsonDict:
        return {
            "status": "completed",
            "job": job_name,
            "run_id": payload.run_id,
            "generated_at": payload.generated_at.isoformat(),
            "delivery_mode": payload.delivery_mode,
            "section_counts": {
                "critical_topics": len(payload.critical_topics),
                "actions_to_take": len(payload.actions_to_take),
                "watch_items": len(payload.watch_items),
                "daily_presence": len(payload.daily_presence),
                "upcoming_meetings": len(payload.upcoming_meetings),
            },
        }

    def _email_command_ack(self, result) -> JsonDict:
        payload = result.payload
        return {
            "status": "completed",
            "job": "email_command_recall",
            "command_message_id": result.command_message_id,
            "command_name": result.command_name,
            "target_user_id": result.target_user_id,
            "deduplicated": bool(result.deduplicated),
            "run_id": payload.run_id,
            "generated_at": payload.generated_at.isoformat(),
            "delivery_mode": payload.delivery_mode,
            "section_counts": {
                "critical_topics": len(payload.critical_topics),
                "actions_to_take": len(payload.actions_to_take),
                "watch_items": len(payload.watch_items),
                "daily_presence": len(payload.daily_presence),
                "upcoming_meetings": len(payload.upcoming_meetings),
            },
        }


def _status_text(status_code: int) -> str:
    return {
        200: "OK",
        400: "Bad Request",
        401: "Unauthorized",
        404: "Not Found",
        500: "Internal Server Error",
    }.get(status_code, "OK")


def create_web_app(settings: Optional[DayCaptainSettings] = None) -> DayCaptainWebApp:
    resolved = settings or DayCaptainSettings.from_env()
    resolved.validate_hosted()
    return DayCaptainWebApp(resolved)


def serve(
    settings: Optional[DayCaptainSettings] = None,
    host: Optional[str] = None,
    port: Optional[int] = None,
) -> None:
    resolved = settings or DayCaptainSettings.from_env()
    resolved.validate_hosted()
    bind_host = host or resolved.http_host
    bind_port = port or resolved.http_port
    app = create_web_app(resolved)
    with make_server(bind_host, bind_port, app) as server:
        print("Day Captain listening on http://{0}:{1}".format(bind_host, bind_port))
        server.serve_forever()

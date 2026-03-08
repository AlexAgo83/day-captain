"""Minimal HTTP surface for hosted Day Captain execution."""

from datetime import date
from datetime import datetime
import json
from typing import Callable
from typing import Iterable
from typing import Optional
from wsgiref.simple_server import make_server

from day_captain.app import build_application
from day_captain.config import DayCaptainSettings
from day_captain.models import to_jsonable


JsonDict = dict
StartResponse = Callable[[str, Iterable[tuple]], None]


def _parse_datetime(value: Optional[str]) -> Optional[datetime]:
    if not value:
        return None
    return datetime.fromisoformat(value)


def _parse_date(value: Optional[str]) -> Optional[date]:
    if not value:
        return None
    return date.fromisoformat(value)


class DayCaptainWebApp:
    def __init__(self, settings: DayCaptainSettings) -> None:
        self.settings = settings

    def __call__(self, environ, start_response: StartResponse):
        method = environ.get("REQUEST_METHOD", "GET").upper()
        path = environ.get("PATH_INFO", "/")

        try:
            if path == "/healthz" and method == "GET":
                return self._json_response(start_response, 200, {"status": "ok"})
            if path == "/jobs/morning-digest" and method == "POST":
                self._require_secret(environ)
                payload = self._read_json(environ)
                self.settings.require_target_user_if_needed(str(payload.get("target_user_id") or ""))
                app = build_application(settings=self.settings)
                result = app.run_morning_digest(
                    now=_parse_datetime(payload.get("now")),
                    delivery_mode=payload.get("delivery_mode"),
                    force=bool(payload.get("force", False)),
                    target_user_id=payload.get("target_user_id"),
                )
                return self._json_response(start_response, 200, self._job_ack("morning_digest", result))
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
            return self._json_response(start_response, 404, {"error": "not_found"})
        except PermissionError as exc:
            return self._json_response(start_response, 401, {"error": str(exc)})
        except LookupError as exc:
            return self._json_response(start_response, 404, {"error": str(exc)})
        except ValueError as exc:
            return self._json_response(start_response, 400, {"error": str(exc)})
        except Exception as exc:  # pragma: no cover - defensive fallback
            return self._json_response(start_response, 500, {"error": "internal_error"})

    def _require_secret(self, environ) -> None:
        if not self.settings.job_secret:
            return
        candidate = environ.get("HTTP_X_DAY_CAPTAIN_SECRET", "")
        if candidate != self.settings.job_secret:
            raise PermissionError("unauthorized")

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

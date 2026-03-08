from datetime import datetime
from datetime import timezone
from io import BytesIO
import json
from pathlib import Path
import sys
import unittest
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from day_captain.config import DayCaptainSettings
from day_captain.models import DigestPayload
from day_captain.web import create_web_app


class FakeHostedApp:
    def __init__(self) -> None:
        self.calls = []

    def run_morning_digest(self, now=None, delivery_mode=None, force=False, target_user_id=None):
        self.calls.append(("morning", now, delivery_mode, force, target_user_id))
        return DigestPayload(
            run_id="run-1",
            generated_at=datetime(2026, 3, 7, 8, 0, tzinfo=timezone.utc),
            window_start=datetime(2026, 3, 6, 8, 0, tzinfo=timezone.utc),
            window_end=datetime(2026, 3, 7, 8, 0, tzinfo=timezone.utc),
            delivery_mode=delivery_mode or "json",
        )

    def recall_digest(self, run_id=None, day=None, target_user_id=None):
        self.calls.append(("recall", run_id, day, target_user_id))
        return DigestPayload(
            run_id=run_id or "run-1",
            generated_at=datetime(2026, 3, 7, 8, 0, tzinfo=timezone.utc),
            window_start=datetime(2026, 3, 6, 8, 0, tzinfo=timezone.utc),
            window_end=datetime(2026, 3, 7, 8, 0, tzinfo=timezone.utc),
            delivery_mode="json",
        )

    def run_weekly_digest(self, now=None, delivery_mode=None, target_user_id=None):
        self.calls.append(("weekly", now, delivery_mode, target_user_id))
        return DigestPayload(
            run_id="run-weekly",
            generated_at=datetime(2026, 3, 8, 19, 30, tzinfo=timezone.utc),
            window_start=datetime(2026, 3, 1, 23, 0, tzinfo=timezone.utc),
            window_end=datetime(2026, 3, 8, 19, 30, tzinfo=timezone.utc),
            delivery_mode=delivery_mode or "json",
        )

    def process_email_command_recall(self, command_message_id="", sender_address="", command_text="", subject="", body="", now=None):
        self.calls.append(("email_command", command_message_id, sender_address, command_text, subject, body, now))
        return type(
            "EmailCommandResult",
            (),
            {
                "command_message_id": command_message_id,
                "command_name": command_text or subject,
                "target_user_id": sender_address,
                "deduplicated": False,
                "payload": DigestPayload(
                    run_id="run-email",
                    generated_at=datetime(2026, 3, 7, 8, 0, tzinfo=timezone.utc),
                    window_start=datetime(2026, 3, 6, 8, 0, tzinfo=timezone.utc),
                    window_end=datetime(2026, 3, 7, 8, 0, tzinfo=timezone.utc),
                    delivery_mode="graph_send",
                ),
            },
        )()


class DayCaptainWebAppTest(unittest.TestCase):
    def _request(self, app, method, path, payload=None, secret="secret"):
        body = b""
        if payload is not None:
            body = json.dumps(payload).encode("utf-8")
        environ = {
            "REQUEST_METHOD": method,
            "PATH_INFO": path,
            "CONTENT_LENGTH": str(len(body)),
            "wsgi.input": BytesIO(body),
            "HTTP_X_DAY_CAPTAIN_SECRET": secret,
        }
        captured = {}

        def start_response(status, headers):
            captured["status"] = status
            captured["headers"] = headers

        response = b"".join(app(environ, start_response))
        captured["json"] = json.loads(response.decode("utf-8"))
        return captured

    def test_healthz_returns_ok(self) -> None:
        app = create_web_app(DayCaptainSettings())

        response = self._request(app, "GET", "/healthz", secret="")

        self.assertEqual(response["status"], "200 OK")
        self.assertEqual(response["json"]["status"], "ok")

    def test_healthz_returns_runtime_summary_when_secret_matches(self) -> None:
        app = create_web_app(
            DayCaptainSettings(
                environment="production",
                job_secret="secret",
                database_url="postgresql://db.example/day_captain",
                delivery_mode="graph_send",
                graph_send_enabled=True,
                graph_auth_mode="app_only",
                graph_client_id="client-id",
                graph_client_secret="client-secret",
                target_users=("alice@example.com",),
            )
        )

        response = self._request(app, "GET", "/healthz", secret="secret")

        self.assertEqual(response["status"], "200 OK")
        self.assertEqual(response["json"]["status"], "ok")
        self.assertEqual(response["json"]["runtime"]["graph_auth_mode"], "app_only")
        self.assertEqual(response["json"]["runtime"]["storage_backend"], "postgres")

    def test_morning_digest_requires_secret(self) -> None:
        app = create_web_app(DayCaptainSettings(job_secret="secret"))

        response = self._request(app, "POST", "/jobs/morning-digest", payload={}, secret="wrong")

        self.assertEqual(response["status"], "401 Unauthorized")
        self.assertEqual(response["json"]["error"], "unauthorized")

    def test_morning_digest_executes_hosted_app(self) -> None:
        settings = DayCaptainSettings(job_secret="secret")
        fake_app = FakeHostedApp()
        app = create_web_app(settings)

        with mock.patch("day_captain.web.build_application", return_value=fake_app):
            response = self._request(
                app,
                "POST",
                "/jobs/morning-digest",
                payload={
                    "now": "2026-03-07T08:30:00+00:00",
                    "delivery_mode": "graph_send",
                    "force": True,
                    "target_user_id": "alex@example.com",
                },
            )

        self.assertEqual(response["status"], "200 OK")
        self.assertEqual(fake_app.calls[0][0], "morning")
        self.assertEqual(fake_app.calls[0][2], "graph_send")
        self.assertTrue(fake_app.calls[0][3])
        self.assertEqual(fake_app.calls[0][4], "alex@example.com")
        self.assertEqual(response["json"]["run_id"], "run-1")
        self.assertEqual(response["json"]["status"], "completed")
        self.assertEqual(response["json"]["section_counts"]["watch_items"], 0)
        self.assertNotIn("delivery_body", response["json"])

    def test_weekly_digest_executes_hosted_app(self) -> None:
        settings = DayCaptainSettings(job_secret="secret")
        fake_app = FakeHostedApp()
        app = create_web_app(settings)

        with mock.patch("day_captain.web.build_application", return_value=fake_app):
            response = self._request(
                app,
                "POST",
                "/jobs/weekly-digest",
                payload={
                    "now": "2026-03-08T19:30:00+00:00",
                    "delivery_mode": "graph_send",
                    "target_user_id": "alex@example.com",
                },
            )

        self.assertEqual(response["status"], "200 OK")
        self.assertEqual(fake_app.calls[0][0], "weekly")
        self.assertEqual(fake_app.calls[0][2], "graph_send")
        self.assertEqual(fake_app.calls[0][3], "alex@example.com")
        self.assertEqual(response["json"]["job"], "weekly_digest")
        self.assertEqual(response["json"]["run_id"], "run-weekly")

    def test_create_web_app_fails_closed_in_production_without_secret(self) -> None:
        with self.assertRaises(ValueError):
            create_web_app(DayCaptainSettings(environment="production"))

    def test_internal_errors_are_not_returned_verbatim(self) -> None:
        settings = DayCaptainSettings(job_secret="secret")
        app = create_web_app(settings)

        with mock.patch("day_captain.web.build_application", side_effect=RuntimeError("db password leaked")):
            response = self._request(app, "POST", "/jobs/morning-digest", payload={})

        self.assertEqual(response["status"], "500 Internal Server Error")
        self.assertEqual(response["json"]["error"], "internal_error")

    def test_email_command_recall_executes_hosted_app(self) -> None:
        settings = DayCaptainSettings(job_secret="secret")
        fake_app = FakeHostedApp()
        app = create_web_app(settings)

        with mock.patch("day_captain.web.build_application", return_value=fake_app):
            response = self._request(
                app,
                "POST",
                "/jobs/email-command-recall",
                payload={
                    "command_message_id": "cmd-1",
                    "sender_address": "alice@example.com",
                    "subject": "recall-week",
                    "now": "2026-03-11T10:00:00+00:00",
                },
            )

        self.assertEqual(response["status"], "200 OK")
        self.assertEqual(fake_app.calls[0][0], "email_command")
        self.assertEqual(fake_app.calls[0][1], "cmd-1")
        self.assertEqual(response["json"]["job"], "email_command_recall")
        self.assertEqual(response["json"]["run_id"], "run-email")

    def test_morning_digest_returns_400_when_target_user_is_missing_for_multi_user_setup(self) -> None:
        settings = DayCaptainSettings(
            job_secret="secret",
            target_users=("alice@example.com", "bob@example.com"),
        )
        fake_app = FakeHostedApp()
        app = create_web_app(settings)

        with mock.patch("day_captain.web.build_application", return_value=fake_app):
            response = self._request(app, "POST", "/jobs/morning-digest", payload={})

        self.assertEqual(response["status"], "400 Bad Request")
        self.assertIn("Multiple target users are configured", response["json"]["error"])

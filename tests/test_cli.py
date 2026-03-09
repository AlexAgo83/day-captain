from datetime import datetime
from datetime import timezone
from pathlib import Path
import os
import sys
import tempfile
import unittest
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from day_captain.cli import _export_digest_preview
from day_captain.cli import _resolved_delivery_mode
from day_captain.cli import _run_trigger_hosted_job_command
from day_captain.cli import _run_check_hosted_health_command
from day_captain.cli import _run_validate_command
from day_captain.cli import _run_validate_hosted_service_command
from day_captain.cli import build_parser
from day_captain.config import DayCaptainSettings
from day_captain.models import DigestPayload
from day_captain.models import EmailCommandResult


class ValidateConfigCommandTest(unittest.TestCase):
    def test_validate_config_returns_runtime_summary(self) -> None:
        settings = DayCaptainSettings(
            environment="production",
            job_secret="secret",
            delivery_mode="graph_send",
            graph_send_enabled=True,
            graph_auth_mode="app_only",
            graph_client_id="client-id",
            graph_client_secret="client-secret",
            target_users=("alice@example.com",),
        )

        result = _run_validate_command(type("Args", (), {"target_user": "alice@example.com"})(), settings)

        self.assertEqual(result["status"], "ok")
        self.assertEqual(result["selected_target_user"], "alice@example.com")

    def test_validate_config_raises_for_invalid_target(self) -> None:
        settings = DayCaptainSettings(
            environment="production",
            job_secret="secret",
            delivery_mode="graph_send",
            graph_send_enabled=True,
            graph_auth_mode="app_only",
            graph_client_id="client-id",
            graph_client_secret="client-secret",
            target_users=("alice@example.com",),
        )

        with self.assertRaises(SystemExit):
            _run_validate_command(type("Args", (), {"target_user": "bob@example.com"})(), settings)

    def test_trigger_hosted_job_command_uses_env_fallbacks(self) -> None:
        previous = dict(os.environ)
        try:
            os.environ["DAY_CAPTAIN_SERVICE_URL"] = "https://example.com"
            os.environ["DAY_CAPTAIN_JOB_SECRET"] = "secret"
            with mock.patch("day_captain.cli.trigger_hosted_job", return_value={"status": "ok"}) as trigger:
                result = _run_trigger_hosted_job_command(
                    type(
                        "Args",
                        (),
                        {
                            "service_url": "",
                            "job_secret": "",
                            "job": "morning-digest",
                            "target_user": "alice@example.com",
                            "force": True,
                            "delivery_mode": "",
                            "now": "",
                            "run_id": "",
                            "day": "",
                            "timeout_seconds": 30,
                            "wake_service": True,
                            "wake_timeout_seconds": 45,
                            "wake_max_attempts": 3,
                            "wake_delay_seconds": 10,
                        },
                    )()
                )
        finally:
            os.environ.clear()
            os.environ.update(previous)

        trigger.assert_called_once()
        self.assertEqual(result["status"], "ok")

    def test_trigger_hosted_job_command_supports_email_command_recall(self) -> None:
        with mock.patch("day_captain.cli.trigger_hosted_job", return_value={"status": "ok"}) as trigger:
            result = _run_trigger_hosted_job_command(
                type(
                    "Args",
                    (),
                    {
                        "service_url": "https://example.com",
                        "job_secret": "secret",
                        "job": "email-command-recall",
                        "target_user": "",
                        "force": False,
                        "delivery_mode": "",
                        "now": "2026-03-11T10:00:00+00:00",
                        "run_id": "",
                        "day": "",
                        "message_id": "cmd-1",
                        "sender_address": "alice@example.com",
                        "command_text": "recall-week",
                        "subject": "",
                        "body": "",
                        "timeout_seconds": 30,
                        "wake_service": False,
                        "wake_timeout_seconds": 45,
                        "wake_max_attempts": 3,
                        "wake_delay_seconds": 10,
                    },
                )()
            )

        trigger.assert_called_once()
        self.assertEqual(result["status"], "ok")

    def test_trigger_hosted_job_command_supports_weekly_digest(self) -> None:
        with mock.patch("day_captain.cli.trigger_hosted_job", return_value={"status": "ok"}) as trigger:
            result = _run_trigger_hosted_job_command(
                type(
                    "Args",
                    (),
                    {
                        "service_url": "https://example.com",
                        "job_secret": "secret",
                        "job": "weekly-digest",
                        "target_user": "alice@example.com",
                        "force": False,
                        "delivery_mode": "graph_send",
                        "now": "2026-03-08T19:30:00+00:00",
                        "run_id": "",
                        "day": "",
                        "message_id": "",
                        "sender_address": "",
                        "command_text": "",
                        "subject": "",
                        "body": "",
                        "timeout_seconds": 30,
                        "wake_service": False,
                        "wake_timeout_seconds": 45,
                        "wake_max_attempts": 3,
                        "wake_delay_seconds": 10,
                    },
                )()
            )

        trigger.assert_called_once()
        self.assertEqual(result["status"], "ok")

    def test_check_hosted_health_command_uses_env_fallbacks(self) -> None:
        previous = dict(os.environ)
        try:
            os.environ["DAY_CAPTAIN_SERVICE_URL"] = "https://example.com"
            os.environ["DAY_CAPTAIN_JOB_SECRET"] = "secret"
            with mock.patch(
                "day_captain.cli.wait_for_hosted_health",
                return_value={"status": "ok"},
            ) as warm_health:
                result = _run_check_hosted_health_command(
                    type(
                        "Args",
                        (),
                        {
                            "service_url": "",
                            "job_secret": "",
                            "timeout_seconds": 30,
                            "wake_service": True,
                            "wake_timeout_seconds": 45,
                            "wake_max_attempts": 3,
                            "wake_delay_seconds": 10,
                            "expect_graph_auth_mode": "app_only",
                            "expect_storage_backend": "postgres",
                        },
                    )()
                )
        finally:
            os.environ.clear()
            os.environ.update(previous)

        warm_health.assert_called_once()
        self.assertEqual(result["status"], "ok")

    def test_validate_hosted_service_command_uses_env_fallbacks(self) -> None:
        previous = dict(os.environ)
        try:
            os.environ["DAY_CAPTAIN_SERVICE_URL"] = "https://example.com"
            os.environ["DAY_CAPTAIN_JOB_SECRET"] = "secret"
            with mock.patch(
                "day_captain.cli.validate_hosted_service",
                return_value={"status": "ok"},
            ) as validate_hosted:
                result = _run_validate_hosted_service_command(
                    type(
                        "Args",
                        (),
                        {
                            "service_url": "",
                            "job_secret": "",
                            "target_user": "alice@example.com",
                            "wake_service": True,
                            "wake_timeout_seconds": 45,
                            "wake_max_attempts": 3,
                            "wake_delay_seconds": 10,
                            "expect_graph_auth_mode": "",
                            "expect_storage_backend": "",
                            "timeout_seconds": 30,
                            "skip_recall": False,
                            "check_email_command": True,
                            "email_command_sender": "alice@example.com",
                            "email_command_text": "recall-week",
                        },
                    )()
                )
        finally:
            os.environ.clear()
            os.environ.update(previous)

        validate_hosted.assert_called_once()
        self.assertEqual(result["status"], "ok")

    def test_export_digest_preview_writes_html_and_text_files(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            html_path = Path(tmpdir) / "preview" / "digest.html"
            text_path = Path(tmpdir) / "preview" / "digest.txt"
            payload = DigestPayload(
                run_id="run-1",
                generated_at=datetime(2026, 3, 8, 8, 0, tzinfo=timezone.utc),
                window_start=datetime(2026, 3, 7, 8, 0, tzinfo=timezone.utc),
                window_end=datetime(2026, 3, 8, 8, 0, tzinfo=timezone.utc),
                delivery_mode="json",
                delivery_body="Plain digest body",
                delivery_payload={"html_body": "<html>Digest</html>"},
            )

            _export_digest_preview(
                type("Args", (), {"output_html": str(html_path), "output_text": str(text_path)})(),
                payload,
            )

            self.assertEqual(html_path.read_text(encoding="utf-8"), "<html>Digest</html>")
            self.assertEqual(text_path.read_text(encoding="utf-8"), "Plain digest body")

    def test_export_digest_preview_supports_email_command_result(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            html_path = Path(tmpdir) / "digest.html"
            payload = DigestPayload(
                run_id="run-2",
                generated_at=datetime(2026, 3, 8, 8, 0, tzinfo=timezone.utc),
                window_start=datetime(2026, 3, 7, 8, 0, tzinfo=timezone.utc),
                window_end=datetime(2026, 3, 8, 8, 0, tzinfo=timezone.utc),
                delivery_mode="json",
                delivery_body="Digest body",
                delivery_payload={"html_body": "<html>Recall digest</html>"},
            )
            result = EmailCommandResult(
                command_message_id="cmd-1",
                command_name="recall",
                target_user_id="alex@example.com",
                payload=payload,
            )

            _export_digest_preview(
                type("Args", (), {"output_html": str(html_path), "output_text": ""})(),
                result,
            )

            self.assertEqual(html_path.read_text(encoding="utf-8"), "<html>Recall digest</html>")

    def test_parser_accepts_preview_export_flags_on_morning_digest(self) -> None:
        parser = build_parser()

        args = parser.parse_args(
            [
                "morning-digest",
                "--force",
                "--preview",
                "--output-html",
                "tmp/preview.html",
                "--output-text",
                "tmp/preview.txt",
            ]
        )

        self.assertEqual(args.command, "morning-digest")
        self.assertTrue(args.preview)
        self.assertEqual(args.output_html, "tmp/preview.html")
        self.assertEqual(args.output_text, "tmp/preview.txt")

    def test_preview_mode_forces_json_delivery(self) -> None:
        args = type("Args", (), {"preview": True})()

        resolved = _resolved_delivery_mode(args, explicit_delivery_mode="graph_send")

        self.assertEqual(resolved, "json")

    def test_non_preview_mode_preserves_explicit_delivery(self) -> None:
        args = type("Args", (), {"preview": False})()

        resolved = _resolved_delivery_mode(args, explicit_delivery_mode="graph_send")

        self.assertEqual(resolved, "graph_send")

    def test_parser_accepts_preview_export_flags_on_recall_digest(self) -> None:
        parser = build_parser()

        args = parser.parse_args(
            [
                "recall-digest",
                "--target-user",
                "alice@example.com",
                "--output-html",
                "tmp/recall.html",
            ]
        )

        self.assertEqual(args.command, "recall-digest")
        self.assertEqual(args.target_user, "alice@example.com")
        self.assertEqual(args.output_html, "tmp/recall.html")

    def test_parser_accepts_preview_on_email_command_recall(self) -> None:
        parser = build_parser()

        args = parser.parse_args(
            [
                "email-command-recall",
                "--message-id",
                "inbound-1",
                "--sender-address",
                "alice@example.com",
                "--preview",
            ]
        )

        self.assertEqual(args.command, "email-command-recall")
        self.assertTrue(args.preview)


if __name__ == "__main__":
    unittest.main()

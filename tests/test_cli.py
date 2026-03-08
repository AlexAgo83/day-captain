from pathlib import Path
import os
import sys
import unittest
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from day_captain.cli import _run_trigger_hosted_job_command
from day_captain.cli import _run_check_hosted_health_command
from day_captain.cli import _run_validate_command
from day_captain.cli import _run_validate_hosted_service_command
from day_captain.config import DayCaptainSettings


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
                        },
                    )()
                )
        finally:
            os.environ.clear()
            os.environ.update(previous)

        validate_hosted.assert_called_once()
        self.assertEqual(result["status"], "ok")


if __name__ == "__main__":
    unittest.main()

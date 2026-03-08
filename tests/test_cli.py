from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from day_captain.cli import _run_validate_command
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


if __name__ == "__main__":
    unittest.main()

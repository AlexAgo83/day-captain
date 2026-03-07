import os
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from day_captain.config import DayCaptainSettings


class DayCaptainSettingsTest(unittest.TestCase):
    def test_from_env_uses_day_captain_variables(self) -> None:
        previous = dict(os.environ)
        try:
            os.environ["DAY_CAPTAIN_ENV"] = "test"
            os.environ["DAY_CAPTAIN_SQLITE_PATH"] = "/tmp/day-captain.sqlite3"
            os.environ["DAY_CAPTAIN_DELIVERY_MODE"] = "graph_send"
            os.environ["DAY_CAPTAIN_DEFAULT_LOOKBACK_HOURS"] = "12"
            os.environ["DAY_CAPTAIN_GRAPH_TENANT_ID"] = "common"
            os.environ["DAY_CAPTAIN_GRAPH_CLIENT_ID"] = "app-client-id"
            os.environ["DAY_CAPTAIN_GRAPH_AUTH_CACHE_PATH"] = "/tmp/day-captain-auth.json"
            os.environ["DAY_CAPTAIN_GRAPH_BASE_URL"] = "https://graph.microsoft.com/v1.0"
            os.environ["DAY_CAPTAIN_GRAPH_ACCESS_TOKEN"] = "delegated-token"
            os.environ["DAY_CAPTAIN_GRAPH_USER_ID"] = "alex@example.com"
            os.environ["DAY_CAPTAIN_GRAPH_SEND_ENABLED"] = "true"
            os.environ["DAY_CAPTAIN_GRAPH_TIMEOUT_SECONDS"] = "45"
            os.environ["DAY_CAPTAIN_GRAPH_SCOPES"] = "Mail.Read, Calendars.Read, Mail.Send"
            settings = DayCaptainSettings.from_env()
        finally:
            os.environ.clear()
            os.environ.update(previous)

        self.assertEqual(settings.environment, "test")
        self.assertEqual(settings.sqlite_path, "/tmp/day-captain.sqlite3")
        self.assertEqual(settings.delivery_mode, "graph_send")
        self.assertEqual(settings.default_lookback_hours, 12)
        self.assertEqual(settings.graph_tenant_id, "common")
        self.assertEqual(settings.graph_client_id, "app-client-id")
        self.assertEqual(settings.graph_auth_cache_path, "/tmp/day-captain-auth.json")
        self.assertEqual(settings.graph_base_url, "https://graph.microsoft.com/v1.0")
        self.assertEqual(settings.graph_access_token, "delegated-token")
        self.assertEqual(settings.graph_user_id, "alex@example.com")
        self.assertTrue(settings.graph_send_enabled)
        self.assertEqual(settings.graph_timeout_seconds, 45)
        self.assertEqual(settings.graph_scopes, ("User.Read", "Mail.Read", "Calendars.Read", "Mail.Send"))
        self.assertEqual(
            settings.graph_login_scopes(),
            ("openid", "profile", "offline_access", "User.Read", "Mail.Read", "Calendars.Read", "Mail.Send"),
        )


if __name__ == "__main__":
    unittest.main()

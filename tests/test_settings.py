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
            os.environ["DAY_CAPTAIN_DATABASE_URL"] = "postgresql://user:pass@localhost:5432/day_captain"
            os.environ["DAY_CAPTAIN_DATABASE_SSL_MODE"] = "require"
            os.environ["DAY_CAPTAIN_DELIVERY_MODE"] = "graph_send"
            os.environ["DAY_CAPTAIN_DEFAULT_LOOKBACK_HOURS"] = "12"
            os.environ["DAY_CAPTAIN_GRAPH_AUTH_MODE"] = "app_only"
            os.environ["DAY_CAPTAIN_GRAPH_TENANT_ID"] = "common"
            os.environ["DAY_CAPTAIN_GRAPH_CLIENT_ID"] = "app-client-id"
            os.environ["DAY_CAPTAIN_GRAPH_CLIENT_SECRET"] = "app-client-secret"
            os.environ["DAY_CAPTAIN_GRAPH_REFRESH_TOKEN"] = "refresh-token"
            os.environ["DAY_CAPTAIN_GRAPH_AUTH_CACHE_PATH"] = "/tmp/day-captain-auth.json"
            os.environ["DAY_CAPTAIN_GRAPH_BASE_URL"] = "https://graph.microsoft.com/v1.0"
            os.environ["DAY_CAPTAIN_GRAPH_ACCESS_TOKEN"] = "delegated-token"
            os.environ["DAY_CAPTAIN_GRAPH_USER_ID"] = "alex@example.com"
            os.environ["DAY_CAPTAIN_GRAPH_SENDER_USER_ID"] = "daycaptain@example.com"
            os.environ["DAY_CAPTAIN_TARGET_USERS"] = "alex@example.com, bob@example.com"
            os.environ["DAY_CAPTAIN_EMAIL_COMMAND_ALLOWED_SENDERS"] = "assistant@example.com"
            os.environ["DAY_CAPTAIN_GRAPH_SEND_ENABLED"] = "true"
            os.environ["DAY_CAPTAIN_GRAPH_TIMEOUT_SECONDS"] = "45"
            os.environ["DAY_CAPTAIN_GRAPH_SCOPES"] = "Mail.Read, Calendars.Read, Mail.Send"
            os.environ["DAY_CAPTAIN_DISPLAY_TIMEZONE"] = "Europe/Paris"
            os.environ["DAY_CAPTAIN_DIGEST_LANGUAGE"] = "fr"
            os.environ["DAY_CAPTAIN_LLM_LANGUAGE"] = "fr"
            os.environ["DAY_CAPTAIN_LLM_PROVIDER"] = "openai"
            os.environ["DAY_CAPTAIN_LLM_API_KEY"] = "sk-test"
            os.environ["DAY_CAPTAIN_LLM_MODEL"] = "gpt-5-mini"
            os.environ["DAY_CAPTAIN_LLM_BASE_URL"] = "https://api.openai.com/v1"
            os.environ["DAY_CAPTAIN_LLM_TIMEOUT_SECONDS"] = "20"
            os.environ["DAY_CAPTAIN_LLM_SHORTLIST_LIMIT"] = "4"
            os.environ["DAY_CAPTAIN_LLM_MAX_OUTPUT_TOKENS"] = "180"
            os.environ["DAY_CAPTAIN_LLM_TEMPERATURE"] = "0.1"
            os.environ["DAY_CAPTAIN_LLM_ENABLED_SECTIONS"] = "critical_topics,actions_to_take"
            os.environ["DAY_CAPTAIN_LLM_STYLE_PROMPT"] = "Write like my chief of staff."
            os.environ["DAY_CAPTAIN_WEATHER_LATITUDE"] = "48.8566"
            os.environ["DAY_CAPTAIN_WEATHER_LONGITUDE"] = "2.3522"
            os.environ["DAY_CAPTAIN_WEATHER_LOCATION_NAME"] = "Paris"
            os.environ["DAY_CAPTAIN_WEATHER_BASE_URL"] = "https://api.open-meteo.com/v1/forecast"
            os.environ["DAY_CAPTAIN_WEATHER_TIMEOUT_SECONDS"] = "12"
            settings = DayCaptainSettings.from_env()
        finally:
            os.environ.clear()
            os.environ.update(previous)

        self.assertEqual(settings.environment, "test")
        self.assertEqual(settings.sqlite_path, "/tmp/day-captain.sqlite3")
        self.assertEqual(
            settings.database_url,
            "postgresql://user:pass@localhost:5432/day_captain",
        )
        self.assertEqual(settings.database_ssl_mode, "require")
        self.assertEqual(settings.delivery_mode, "graph_send")
        self.assertEqual(settings.default_lookback_hours, 12)
        self.assertEqual(settings.graph_auth_mode, "app_only")
        self.assertEqual(settings.graph_tenant_id, "common")
        self.assertEqual(settings.graph_client_id, "app-client-id")
        self.assertEqual(settings.graph_client_secret, "app-client-secret")
        self.assertEqual(settings.graph_refresh_token, "refresh-token")
        self.assertEqual(settings.graph_auth_cache_path, "/tmp/day-captain-auth.json")
        self.assertEqual(settings.graph_base_url, "https://graph.microsoft.com/v1.0")
        self.assertEqual(settings.graph_access_token, "delegated-token")
        self.assertEqual(settings.graph_user_id, "alex@example.com")
        self.assertEqual(settings.graph_sender_user_id, "daycaptain@example.com")
        self.assertEqual(settings.target_users, ("alex@example.com", "bob@example.com"))
        self.assertEqual(settings.email_command_allowed_senders, ("assistant@example.com",))
        self.assertTrue(settings.graph_send_enabled)
        self.assertEqual(settings.graph_timeout_seconds, 45)
        self.assertEqual(settings.graph_scopes, ("User.Read", "Mail.Read", "Calendars.Read", "Mail.Send"))
        self.assertEqual(settings.display_timezone, "Europe/Paris")
        self.assertEqual(settings.digest_language, "fr")
        self.assertEqual(settings.llm_language, "fr")
        self.assertEqual(settings.llm_provider, "openai")
        self.assertEqual(settings.llm_api_key, "sk-test")
        self.assertEqual(settings.llm_model, "gpt-5-mini")
        self.assertEqual(settings.llm_base_url, "https://api.openai.com/v1")
        self.assertEqual(settings.llm_timeout_seconds, 20)
        self.assertEqual(settings.llm_shortlist_limit, 4)
        self.assertEqual(settings.llm_max_output_tokens, 180)
        self.assertEqual(settings.llm_temperature, 0.1)
        self.assertEqual(settings.llm_enabled_sections, ("critical_topics", "actions_to_take"))
        self.assertEqual(settings.llm_style_prompt, "Write like my chief of staff.")
        self.assertEqual(settings.weather_latitude, 48.8566)
        self.assertEqual(settings.weather_longitude, 2.3522)
        self.assertEqual(settings.weather_location_name, "Paris")
        self.assertEqual(settings.weather_base_url, "https://api.open-meteo.com/v1/forecast")
        self.assertEqual(settings.weather_timeout_seconds, 12)
        self.assertTrue(settings.llm_is_enabled())
        self.assertTrue(settings.weather_is_enabled())
        self.assertEqual(settings.resolved_digest_language(), "fr")
        self.assertEqual(settings.resolved_llm_language(), "fr")
        self.assertEqual(settings.resolved_weather_location_name(), "Paris")
        self.assertEqual(
            settings.graph_login_scopes(),
            ("openid", "profile", "offline_access", "User.Read", "Mail.Read", "Calendars.Read", "Mail.Send"),
        )
        self.assertEqual(
            settings.resolved_database_url(),
            "postgresql://user:pass@localhost:5432/day_captain?sslmode=require",
        )
        self.assertEqual(settings.resolved_graph_auth_mode(), "app_only")
        self.assertEqual(settings.resolved_target_users(), ("alex@example.com", "bob@example.com"))
        self.assertEqual(settings.resolved_default_target_user(), "alex@example.com")

    def test_validate_hosted_requires_job_secret(self) -> None:
        settings = DayCaptainSettings(environment="production", job_secret="")

        with self.assertRaises(ValueError):
            settings.validate_hosted()

    def test_validate_hosted_requires_app_only_credentials_and_targets(self) -> None:
        with self.assertRaises(ValueError):
            DayCaptainSettings(
                environment="production",
                job_secret="secret",
                graph_auth_mode="app_only",
                graph_client_id="client-id",
            ).validate_hosted()

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

        settings.validate_hosted()

    def test_validate_hosted_email_command_requires_graph_send_and_app_only(self) -> None:
        with self.assertRaisesRegex(ValueError, "hosted email-command recall"):
            DayCaptainSettings(
                environment="production",
                job_secret="secret",
                graph_auth_mode="app_only",
                graph_client_id="client-id",
                graph_client_secret="client-secret",
                target_users=("alice@example.com",),
                email_command_allowed_senders=("assistant@example.com",),
            ).validate_hosted()

        with self.assertRaisesRegex(ValueError, "app-only Graph auth"):
            DayCaptainSettings(
                environment="production",
                job_secret="secret",
                delivery_mode="json",
                graph_send_enabled=True,
                graph_auth_mode="delegated",
                target_users=("alice@example.com",),
                email_command_allowed_senders=("assistant@example.com",),
            ).validate_hosted()

        DayCaptainSettings(
            environment="production",
            job_secret="secret",
            delivery_mode="json",
            graph_send_enabled=True,
            graph_auth_mode="app_only",
            graph_client_id="client-id",
            graph_client_secret="client-secret",
            target_users=("alice@example.com",),
            email_command_allowed_senders=("assistant@example.com",),
        ).validate_hosted()

    def test_validate_hosted_email_command_requires_single_target_user(self) -> None:
        with self.assertRaisesRegex(ValueError, "exactly one hosted target user"):
            DayCaptainSettings(
                environment="production",
                job_secret="secret",
                graph_send_enabled=True,
                graph_auth_mode="app_only",
                graph_client_id="client-id",
                graph_client_secret="client-secret",
                target_users=("alice@example.com", "bob@example.com"),
                email_command_allowed_senders=("assistant@example.com",),
            ).validate_hosted()

    def test_validate_target_user_rejects_unknown_user(self) -> None:
        settings = DayCaptainSettings(target_users=("alice@example.com", "bob@example.com"))

        with self.assertRaises(ValueError):
            settings.validate_target_user("carol@example.com")

    def test_validation_summary_reports_resolved_runtime(self) -> None:
        settings = DayCaptainSettings(
            environment="production",
            job_secret="secret",
            delivery_mode="graph_send",
            graph_send_enabled=True,
            graph_auth_mode="app_only",
            graph_client_id="client-id",
            graph_client_secret="client-secret",
            target_users=("alice@example.com", "bob@example.com"),
        )

        summary = settings.validation_summary(target_user_id="alice@example.com")

        self.assertEqual(summary["status"], "ok")
        self.assertEqual(summary["graph_auth_mode"], "app_only")
        self.assertEqual(summary["configured_target_users"], ("alice@example.com", "bob@example.com"))
        self.assertEqual(summary["selected_target_user"], "alice@example.com")
        self.assertEqual(summary["configured_sender_user"], "")
        self.assertEqual(summary["email_command_allowed_senders"], ())
        self.assertFalse(summary["weather_enabled"])
        self.assertEqual(summary["weather_location_name"], "")

    def test_llm_is_disabled_by_default(self) -> None:
        self.assertFalse(DayCaptainSettings().llm_is_enabled())
        self.assertEqual(DayCaptainSettings().resolved_digest_language(), "en")
        self.assertEqual(DayCaptainSettings().resolved_llm_language(), "en")

    def test_graph_auth_mode_auto_prefers_app_only_when_secret_and_user_are_present(self) -> None:
        settings = DayCaptainSettings(
            graph_auth_mode="auto",
            graph_client_secret="secret",
            target_users=("alex@example.com", "bob@example.com"),
        )

        self.assertEqual(settings.resolved_graph_auth_mode(), "app_only")


if __name__ == "__main__":
    unittest.main()

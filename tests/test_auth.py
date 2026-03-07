from datetime import datetime
from datetime import timedelta
from datetime import timezone
import io
import json
from pathlib import Path
import sys
import tempfile
import unittest
from urllib import error

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from day_captain.adapters.auth import DeviceCodeAuthenticator
from day_captain.adapters.auth import DeviceCodeSession
from day_captain.adapters.auth import FileTokenCache
from day_captain.adapters.graph import GraphDelegatedAuthProvider
from day_captain.cli import _run_auth_command
from day_captain.config import DayCaptainSettings
from day_captain.models import AuthTokenBundle


class FakeResponse:
    def __init__(self, payload):
        self.payload = payload

    def read(self):
        return json.dumps(self.payload).encode("utf-8")

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False


class SequenceOpener:
    def __init__(self, payloads):
        self.payloads = list(payloads)
        self.requests = []

    def __call__(self, req, timeout=0):
        self.requests.append((req.full_url, req.data.decode("utf-8") if req.data else ""))
        payload = self.payloads.pop(0)
        if isinstance(payload, Exception):
            raise payload
        return FakeResponse(payload)


def http_json_error(status, payload):
    return error.HTTPError(
        url="https://login.microsoftonline.com/common/oauth2/v2.0/token",
        code=status,
        msg="error",
        hdrs=None,
        fp=io.BytesIO(json.dumps(payload).encode("utf-8")),
    )


class StaticApiClient:
    def get_object(self, path, access_token, params=None, headers=None):
        return {"id": "user-123"}


class AuthFlowTest(unittest.TestCase):
    def test_token_cache_round_trip_and_clear(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            path = str(Path(tmpdir) / "auth.json")
            cache = FileTokenCache(path)
            bundle = AuthTokenBundle(
                access_token="access",
                refresh_token="refresh",
                expires_at=datetime(2026, 3, 7, 8, 0, tzinfo=timezone.utc),
                scopes=("Mail.Read",),
                user_id="user-123",
            )

            cache.save(bundle)
            loaded = cache.load()
            cache.clear()

            self.assertEqual(loaded.access_token, "access")
            self.assertFalse(Path(path).exists())

    def test_device_code_authenticator_refreshes_tokens(self) -> None:
        opener = SequenceOpener(
            [
                {
                    "access_token": "new-access",
                    "refresh_token": "new-refresh",
                    "expires_in": 3600,
                    "scope": "Mail.Read Calendars.Read",
                    "token_type": "Bearer",
                }
            ]
        )
        authenticator = DeviceCodeAuthenticator(
            tenant_id="common",
            client_id="client-id",
            opener=opener,
            sleeper=lambda seconds: None,
        )

        bundle = authenticator.refresh_tokens("old-refresh", ("Mail.Read", "Calendars.Read"))

        self.assertEqual(bundle.access_token, "new-access")
        self.assertEqual(bundle.refresh_token, "new-refresh")
        self.assertEqual(bundle.scopes, ("Mail.Read", "Calendars.Read"))

    def test_device_code_poll_handles_authorization_pending_then_succeeds(self) -> None:
        opener = SequenceOpener(
            [
                http_json_error(
                    400,
                    {
                        "error": "authorization_pending",
                        "error_description": "Authorization is pending.",
                    },
                ),
                {
                    "access_token": "ready-access",
                    "refresh_token": "ready-refresh",
                    "expires_in": 3600,
                    "scope": "Mail.Read Calendars.Read",
                    "token_type": "Bearer",
                },
            ]
        )
        sleeps = []
        authenticator = DeviceCodeAuthenticator(
            tenant_id="common",
            client_id="client-id",
            opener=opener,
            sleeper=lambda seconds: sleeps.append(seconds),
        )

        bundle = authenticator.poll_for_tokens(
            DeviceCodeSession(
                device_code="device-code",
                user_code="user-code",
                verification_uri="https://microsoft.com/devicelogin",
                expires_in=900,
                interval=5,
                message="",
            ),
            ("Mail.Read", "Calendars.Read"),
        )

        self.assertEqual(bundle.access_token, "ready-access")
        self.assertEqual(sleeps, [5])

    def test_graph_provider_uses_cached_token_and_refresh(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            cache = FileTokenCache(str(Path(tmpdir) / "auth.json"))
            cache.save(
                AuthTokenBundle(
                    access_token="expired-access",
                    refresh_token="refresh-token",
                    expires_at=datetime.now(timezone.utc) - timedelta(minutes=5),
                    scopes=("Mail.Read",),
                )
            )
            opener = SequenceOpener(
                [
                    {
                        "access_token": "fresh-access",
                        "refresh_token": "fresh-refresh",
                        "expires_in": 3600,
                        "scope": "Mail.Read",
                        "token_type": "Bearer",
                    }
                ]
            )
            authenticator = DeviceCodeAuthenticator(
                tenant_id="common",
                client_id="client-id",
                opener=opener,
                sleeper=lambda seconds: None,
            )
            provider = GraphDelegatedAuthProvider(
                api_client=StaticApiClient(),
                token_cache=cache,
                authenticator=authenticator,
            )

            context = provider.authenticate(("Mail.Read",))

            self.assertEqual(context.access_token, "fresh-access")
            self.assertEqual(context.user_id, "user-123")

    def test_auth_status_and_logout_commands_use_cache(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            cache_path = str(Path(tmpdir) / "auth.json")
            FileTokenCache(cache_path).save(
                AuthTokenBundle(
                    access_token="access",
                    refresh_token="refresh",
                    expires_at=datetime(2026, 3, 7, 8, 0, tzinfo=timezone.utc),
                    scopes=("Mail.Read",),
                    user_id="user-123",
                )
            )
            settings = DayCaptainSettings(
                graph_client_id="client-id",
                graph_auth_cache_path=cache_path,
            )

            status = _run_auth_command(type("Args", (), {"auth_command": "status"})(), settings)
            logout = _run_auth_command(type("Args", (), {"auth_command": "logout"})(), settings)

            self.assertEqual(status["status"], "authenticated")
            self.assertEqual(status["user_id"], "user-123")
            self.assertEqual(logout["status"], "logged_out")
            self.assertFalse(Path(cache_path).exists())


if __name__ == "__main__":
    unittest.main()

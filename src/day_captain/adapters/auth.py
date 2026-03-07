"""Microsoft Entra ID device code authentication for Day Captain."""

from datetime import datetime
from datetime import timedelta
from datetime import timezone
import json
import os
from pathlib import Path
import stat
import time
from typing import Any
from typing import Callable
from typing import Mapping
from typing import Optional
from typing import Sequence
from urllib import error
from urllib import parse
from urllib import request

from day_captain.models import AuthTokenBundle
from day_captain.models import DeviceCodeSession
from day_captain.models import parse_datetime
from day_captain.models import to_jsonable


class EntraAuthError(RuntimeError):
    """Raised when Microsoft Entra ID auth fails."""


class FileTokenCache:
    def __init__(self, path: str) -> None:
        self.path = Path(path)

    def load(self) -> Optional[AuthTokenBundle]:
        if not self.path.exists():
            return None
        payload = json.loads(self.path.read_text(encoding="utf-8"))
        return AuthTokenBundle(
            access_token=str(payload.get("access_token") or ""),
            refresh_token=str(payload.get("refresh_token") or ""),
            expires_at=parse_datetime(str(payload.get("expires_at"))),
            scopes=tuple(str(item) for item in payload.get("scopes") or ()),
            token_type=str(payload.get("token_type") or "Bearer"),
            user_id=str(payload.get("user_id") or ""),
        )

    def save(self, bundle: AuthTokenBundle) -> None:
        if self.path.parent and not self.path.parent.exists():
            self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(json.dumps(to_jsonable(bundle), indent=2, sort_keys=True), encoding="utf-8")
        try:
            os.chmod(self.path, stat.S_IRUSR | stat.S_IWUSR)
        except OSError:
            pass

    def clear(self) -> None:
        if self.path.exists():
            self.path.unlink()


class DeviceCodeAuthenticator:
    def __init__(
        self,
        tenant_id: str,
        client_id: str,
        timeout_seconds: int = 30,
        opener: Optional[Callable[..., Any]] = None,
        sleeper: Optional[Callable[[float], None]] = None,
    ) -> None:
        self.tenant_id = tenant_id
        self.client_id = client_id
        self.timeout_seconds = timeout_seconds
        self._opener = opener or request.urlopen
        self._sleeper = sleeper or time.sleep

    def _endpoint(self, name: str) -> str:
        return "https://login.microsoftonline.com/{0}/oauth2/v2.0/{1}".format(self.tenant_id, name)

    def _post_form(
        self,
        endpoint: str,
        payload: Mapping[str, str],
        allow_error_response: bool = False,
    ) -> Mapping[str, Any]:
        body = parse.urlencode(payload).encode("utf-8")
        req = request.Request(
            self._endpoint(endpoint),
            data=body,
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            method="POST",
        )
        try:
            with self._opener(req, timeout=self.timeout_seconds) as response:
                raw = response.read().decode("utf-8")
        except error.HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="replace")
            if allow_error_response:
                try:
                    data = json.loads(detail or "{}")
                except json.JSONDecodeError as decode_error:
                    raise EntraAuthError(
                        "Entra auth request failed with {0}: {1}".format(exc.code, detail)
                    ) from decode_error
                if isinstance(data, dict):
                    return data
            raise EntraAuthError("Entra auth request failed with {0}: {1}".format(exc.code, detail)) from exc
        except error.URLError as exc:
            raise EntraAuthError("Unable to reach Microsoft Entra ID: {0}".format(exc.reason)) from exc
        data = json.loads(raw or "{}")
        if not isinstance(data, dict):
            raise EntraAuthError("Expected JSON object from Entra ID.")
        return data

    def start_device_code(self, scopes: Sequence[str]) -> DeviceCodeSession:
        if not self.client_id:
            raise EntraAuthError("DAY_CAPTAIN_GRAPH_CLIENT_ID is required for device code auth.")
        data = self._post_form(
            "devicecode",
            {
                "client_id": self.client_id,
                "scope": " ".join(scopes),
            },
        )
        return DeviceCodeSession(
            device_code=str(data.get("device_code") or ""),
            user_code=str(data.get("user_code") or ""),
            verification_uri=str(data.get("verification_uri") or data.get("verification_uri_complete") or ""),
            expires_in=int(data.get("expires_in") or 0),
            interval=int(data.get("interval") or 5),
            message=str(data.get("message") or ""),
        )

    def poll_for_tokens(self, session: DeviceCodeSession, scopes: Sequence[str]) -> AuthTokenBundle:
        deadline = datetime.now(timezone.utc) + timedelta(seconds=session.expires_in or 900)
        interval = max(1, session.interval or 5)
        while datetime.now(timezone.utc) < deadline:
            data = self._post_form(
                "token",
                {
                    "grant_type": "urn:ietf:params:oauth:grant-type:device_code",
                    "client_id": self.client_id,
                    "device_code": session.device_code,
                },
                allow_error_response=True,
            )
            error_code = str(data.get("error") or "")
            if not error_code:
                return self._bundle_from_token_response(data, scopes=scopes)
            if error_code == "authorization_pending":
                self._sleeper(interval)
                continue
            if error_code == "slow_down":
                interval += 5
                self._sleeper(interval)
                continue
            if error_code == "authorization_declined":
                raise EntraAuthError("Device code authorization was declined by the user.")
            if error_code == "expired_token":
                raise EntraAuthError("Device code expired before authorization completed.")
            raise EntraAuthError("Unexpected device code error: {0}".format(error_code))
        raise EntraAuthError("Timed out while waiting for device code authorization.")

    def refresh_tokens(self, refresh_token: str, scopes: Sequence[str]) -> AuthTokenBundle:
        if not refresh_token:
            raise EntraAuthError("No refresh token available.")
        data = self._post_form(
            "token",
            {
                "grant_type": "refresh_token",
                "client_id": self.client_id,
                "refresh_token": refresh_token,
                "scope": " ".join(scopes),
            },
        )
        return self._bundle_from_token_response(data, scopes=scopes, refresh_fallback=refresh_token)

    def _bundle_from_token_response(
        self,
        data: Mapping[str, Any],
        scopes: Sequence[str],
        refresh_fallback: str = "",
    ) -> AuthTokenBundle:
        expires_in = int(data.get("expires_in") or 3600)
        expires_at = datetime.now(timezone.utc) + timedelta(seconds=max(0, expires_in - 60))
        raw_scopes = str(data.get("scope") or "").split()
        return AuthTokenBundle(
            access_token=str(data.get("access_token") or ""),
            refresh_token=str(data.get("refresh_token") or refresh_fallback),
            expires_at=expires_at,
            scopes=tuple(raw_scopes or scopes),
            token_type=str(data.get("token_type") or "Bearer"),
        )

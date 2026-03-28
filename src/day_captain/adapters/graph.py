"""Microsoft Graph adapters for Day Captain."""

from datetime import datetime
from datetime import timezone
import json
import socket
from typing import Any
from typing import Callable
from typing import Dict
from typing import Iterable
from typing import Mapping
from typing import Optional
from typing import Sequence
from urllib import error
from urllib import parse
from urllib import request
from urllib.parse import quote
from urllib.parse import urlparse
from zoneinfo import ZoneInfo

from day_captain.adapters.auth import EntraAuthError
from day_captain.adapters.auth import DeviceCodeAuthenticator
from day_captain.adapters.auth import TokenCache
from day_captain.models import AuthContext
from day_captain.models import MeetingRecord
from day_captain.models import MessageRecord
from day_captain.models import parse_datetime


class GraphApiError(RuntimeError):
    """Raised when Microsoft Graph returns an unexpected response."""


def _graph_timeout_error_message(timeout_seconds: int) -> str:
    return "Microsoft Graph request timed out after {0} seconds.".format(timeout_seconds)


def _normalize_identity(value: str) -> str:
    candidate = str(value or "").strip()
    if "@" in candidate:
        return candidate.lower()
    return candidate


def _normalize_address_list(items: Iterable[Mapping[str, Any]]) -> Sequence[str]:
    addresses = []
    for item in items:
        email = ((item.get("emailAddress") or {}).get("address")) or ""
        if email:
            addresses.append(str(email))
    return tuple(addresses)


def _normalize_received_at(value: str) -> datetime:
    return parse_datetime(value)


def _normalize_graph_datetime(payload: Mapping[str, Any]) -> datetime:
    raw_value = str(payload.get("dateTime") or "")
    if not raw_value:
        return datetime.now(timezone.utc)
    normalized = raw_value
    if "." in normalized:
        head, tail = normalized.split(".", 1)
        fraction = []
        suffix = []
        for char in tail:
            if char.isdigit() and not suffix:
                fraction.append(char)
            else:
                suffix.append(char)
        normalized = "{0}.{1}{2}".format(head, "".join(fraction[:6]), "".join(suffix)).rstrip(".")
    parsed = parse_datetime(normalized)
    if parsed.tzinfo is None:
        timezone_name = str(payload.get("timeZone") or "").strip()
        if timezone_name.upper() == "UTC":
            return parsed.replace(tzinfo=timezone.utc)
        try:
            return parsed.replace(tzinfo=ZoneInfo(timezone_name))
        except Exception:
            return parsed.replace(tzinfo=timezone.utc)
    return parsed


def normalize_message(payload: Mapping[str, Any]) -> MessageRecord:
    return MessageRecord(
        graph_message_id=str(payload.get("id") or ""),
        thread_id=str(payload.get("conversationId") or ""),
        internet_message_id=str(payload.get("internetMessageId") or ""),
        subject=str(payload.get("subject") or ""),
        from_address=str((((payload.get("from") or {}).get("emailAddress") or {}).get("address")) or ""),
        to_addresses=_normalize_address_list(payload.get("toRecipients") or ()),
        cc_addresses=_normalize_address_list(payload.get("ccRecipients") or ()),
        received_at=_normalize_received_at(str(payload.get("receivedDateTime") or datetime.now(timezone.utc).isoformat())),
        body_preview=str(payload.get("bodyPreview") or ""),
        categories=tuple(str(item) for item in payload.get("categories") or ()),
        is_unread=bool(payload.get("isRead") is False),
        has_attachments=bool(payload.get("hasAttachments")),
        raw_payload=dict(payload),
    )


def normalize_meeting(payload: Mapping[str, Any]) -> MeetingRecord:
    online_meeting = payload.get("onlineMeeting") or {}
    return MeetingRecord(
        graph_event_id=str(payload.get("id") or ""),
        subject=str(payload.get("subject") or ""),
        start_at=_normalize_graph_datetime(payload.get("start") or {}),
        end_at=_normalize_graph_datetime(payload.get("end") or {}),
        organizer_address=str((((payload.get("organizer") or {}).get("emailAddress") or {}).get("address")) or ""),
        attendees=_normalize_address_list(payload.get("attendees") or ()),
        location=str((((payload.get("location") or {}).get("displayName")) or "")),
        join_url=str(online_meeting.get("joinUrl") or payload.get("webLink") or ""),
        body_preview=str((((payload.get("bodyPreview")) or ""))),
        is_online_meeting=bool(payload.get("isOnlineMeeting") or online_meeting),
        raw_payload=dict(payload),
    )


class GraphApiClient:
    def __init__(
        self,
        base_url: str,
        timeout_seconds: int = 30,
        opener: Optional[Callable[..., Any]] = None,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.timeout_seconds = timeout_seconds
        self._opener = opener or request.urlopen
        parsed_base_url = urlparse(self.base_url)
        self._trusted_scheme = str(parsed_base_url.scheme or "").lower()
        self._trusted_netloc = str(parsed_base_url.netloc or "").lower()

    def _validate_absolute_graph_url(self, candidate_url: str) -> str:
        parsed = urlparse(candidate_url)
        candidate_scheme = str(parsed.scheme or "").lower()
        candidate_netloc = str(parsed.netloc or "").lower()
        if not candidate_scheme or not candidate_netloc:
            raise GraphApiError("Expected an absolute Graph URL.")
        if (
            candidate_scheme != self._trusted_scheme
            or candidate_netloc != self._trusted_netloc
        ):
            raise GraphApiError(
                "Graph absolute URL points outside the configured Graph origin."
            )
        return candidate_url

    def _build_url(self, path: str, params: Optional[Mapping[str, Any]] = None) -> str:
        if path.startswith("http://") or path.startswith("https://"):
            base = self._validate_absolute_graph_url(path)
        else:
            base = "{0}/{1}".format(self.base_url, path.lstrip("/"))
        if not params:
            return base
        query = parse.urlencode(params, doseq=True)
        separator = "&" if "?" in base else "?"
        return "{0}{1}{2}".format(base, separator, query)

    def get_object(
        self,
        path: str,
        access_token: str,
        params: Optional[Mapping[str, Any]] = None,
        headers: Optional[Mapping[str, str]] = None,
    ) -> Mapping[str, Any]:
        url = self._build_url(path, params=params)
        request_headers = {
            "Authorization": "Bearer {0}".format(access_token),
            "Accept": "application/json",
        }
        if headers:
            request_headers.update(headers)
        req = request.Request(url, headers=request_headers, method="GET")
        try:
            with self._opener(req, timeout=self.timeout_seconds) as response:
                raw = response.read().decode("utf-8")
        except error.HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="replace")
            raise GraphApiError("Graph request failed with {0}: {1}".format(exc.code, detail)) from exc
        except (TimeoutError, socket.timeout) as exc:
            raise GraphApiError(_graph_timeout_error_message(self.timeout_seconds)) from exc
        except error.URLError as exc:
            raise GraphApiError("Unable to reach Microsoft Graph: {0}".format(exc.reason)) from exc
        payload = json.loads(raw or "{}")
        if not isinstance(payload, dict):
            raise GraphApiError("Expected Graph JSON object response.")
        return payload

    def post_object(
        self,
        path: str,
        access_token: str,
        payload: Mapping[str, Any],
        headers: Optional[Mapping[str, str]] = None,
        expected_statuses: Sequence[int] = (200, 201, 202, 204),
    ) -> Mapping[str, Any]:
        url = self._build_url(path)
        request_headers = {
            "Authorization": "Bearer {0}".format(access_token),
            "Accept": "application/json",
            "Content-Type": "application/json",
        }
        if headers:
            request_headers.update(headers)
        body = json.dumps(payload).encode("utf-8")
        req = request.Request(url, data=body, headers=request_headers, method="POST")
        try:
            with self._opener(req, timeout=self.timeout_seconds) as response:
                if response.status not in expected_statuses:
                    raise GraphApiError(
                        "Graph request failed with unexpected status {0}.".format(response.status)
                    )
                raw = response.read().decode("utf-8")
        except error.HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="replace")
            raise GraphApiError("Graph request failed with {0}: {1}".format(exc.code, detail)) from exc
        except (TimeoutError, socket.timeout) as exc:
            raise GraphApiError(_graph_timeout_error_message(self.timeout_seconds)) from exc
        except error.URLError as exc:
            raise GraphApiError("Unable to reach Microsoft Graph: {0}".format(exc.reason)) from exc
        if not raw.strip():
            return {}
        parsed = json.loads(raw)
        if not isinstance(parsed, dict):
            raise GraphApiError("Expected Graph JSON object response.")
        return parsed

    def list_collection(
        self,
        path: str,
        access_token: str,
        params: Optional[Mapping[str, Any]] = None,
        headers: Optional[Mapping[str, str]] = None,
    ) -> Sequence[Mapping[str, Any]]:
        items = []
        next_path = path
        next_params = params
        while next_path:
            payload = self.get_object(
                next_path,
                access_token=access_token,
                params=next_params,
                headers=headers,
            )
            batch = payload.get("value")
            if not isinstance(batch, list):
                raise GraphApiError(
                    "Expected Graph collection response to contain a list in `value`. Got keys: {0}".format(
                        ", ".join(sorted(str(key) for key in payload.keys()))
                    )
                )
            items.extend(item for item in batch if isinstance(item, dict))
            next_path = payload.get("@odata.nextLink")
            next_params = None
        return tuple(items)


class GraphDelegatedAuthProvider:
    def __init__(
        self,
        api_client: GraphApiClient,
        access_token: str = "",
        token_cache: Optional[TokenCache] = None,
        authenticator: Optional[DeviceCodeAuthenticator] = None,
        user_id: str = "",
    ) -> None:
        self.api_client = api_client
        self.access_token = access_token
        self.token_cache = token_cache
        self.authenticator = authenticator
        self.user_id = user_id

    def authenticate(
        self,
        scopes: Sequence[str],
        target_user_id: str = "",
        tenant_id: str = "",
    ) -> AuthContext:
        access_token = self.access_token
        cached_bundle = None if access_token else (self.token_cache.load() if self.token_cache is not None else None)
        active_bundle = None
        if not access_token and cached_bundle is not None:
            requested_scopes = {str(scope) for scope in scopes}
            cached_scopes = {str(scope) for scope in cached_bundle.scopes}
            cached_is_fresh = cached_bundle.expires_at > datetime.now(timezone.utc)
            if cached_is_fresh and requested_scopes.issubset(cached_scopes):
                access_token = cached_bundle.access_token
                active_bundle = cached_bundle
            elif cached_is_fresh:
                access_token = cached_bundle.access_token
                active_bundle = cached_bundle
            elif self.authenticator is not None and cached_bundle.refresh_token:
                try:
                    refreshed = self.authenticator.refresh_tokens(cached_bundle.refresh_token, scopes)
                except EntraAuthError as exc:
                    raise ValueError(
                        "Delegated Graph token refresh failed. Re-authenticate or repair the hosted auth configuration."
                    ) from exc
                if self.token_cache is not None:
                    self.token_cache.save(refreshed)
                cached_bundle = refreshed
                access_token = refreshed.access_token
                active_bundle = refreshed
            else:
                raise ValueError(
                    "Cached delegated Graph access token has expired and no usable refresh path is configured. "
                    "Re-authenticate or set DAY_CAPTAIN_GRAPH_ACCESS_TOKEN."
                )
        if not access_token:
            raise ValueError(
                "No delegated Graph access token available. Run `day-captain auth login` or set DAY_CAPTAIN_GRAPH_ACCESS_TOKEN."
            )

        resolved_user_id = _normalize_identity(self.user_id or (cached_bundle.user_id if cached_bundle is not None else ""))
        if not resolved_user_id:
            profile = self.api_client.get_object("/me", access_token=access_token)
            resolved_user_id = _normalize_identity(
                str(profile.get("id") or profile.get("userPrincipalName") or "graph-user")
            )
            if cached_bundle is not None and self.token_cache is not None:
                refreshed_profile_bundle = type(cached_bundle)(
                    access_token=access_token,
                    refresh_token=cached_bundle.refresh_token,
                    expires_at=cached_bundle.expires_at,
                    scopes=cached_bundle.scopes,
                    token_type=cached_bundle.token_type,
                    user_id=resolved_user_id,
                )
                self.token_cache.save(refreshed_profile_bundle)
                active_bundle = refreshed_profile_bundle
        requested_user_id = _normalize_identity(target_user_id)
        if requested_user_id and requested_user_id != resolved_user_id:
            raise ValueError("Delegated auth can only run for the authenticated user.")
        if requested_user_id:
            resolved_user_id = requested_user_id
        granted_scopes = tuple(active_bundle.scopes) if active_bundle is not None and active_bundle.scopes else tuple(scopes)
        return AuthContext(
            access_token=access_token,
            granted_scopes=granted_scopes,
            user_id=resolved_user_id,
            tenant_id=str(tenant_id or "").strip(),
            auth_mode="delegated",
            graph_root_path="/me",
            sender_user_id=resolved_user_id,
            sender_graph_root_path="/me",
        )


def _user_graph_root(user_id: str) -> str:
    normalized = str(user_id or "").strip()
    if not normalized:
        raise ValueError("A target Graph user id is required for app-only auth.")
    return "/users/{0}".format(quote(normalized, safe=""))


class GraphAppOnlyAuthProvider:
    def __init__(
        self,
        authenticator,
        user_id: str,
        sender_user_id: str = "",
        configured_scopes: Sequence[str] = (),
    ) -> None:
        self.authenticator = authenticator
        self.user_id = user_id
        self.sender_user_id = sender_user_id
        self.configured_scopes = tuple(configured_scopes)

    def authenticate(
        self,
        scopes: Sequence[str],
        target_user_id: str = "",
        tenant_id: str = "",
    ) -> AuthContext:
        bundle = self.authenticator.request_access_token()
        resolved_user_id = str(target_user_id or self.user_id or "").strip()
        if not resolved_user_id:
            raise ValueError("DAY_CAPTAIN_GRAPH_USER_ID is required for app-only auth.")
        resolved_sender_user_id = str(self.sender_user_id or resolved_user_id).strip()
        granted_scopes = tuple(self.configured_scopes or scopes)
        return AuthContext(
            access_token=bundle.access_token,
            granted_scopes=granted_scopes,
            user_id=resolved_user_id,
            tenant_id=str(tenant_id or "").strip(),
            auth_mode="app_only",
            graph_root_path=_user_graph_root(resolved_user_id),
            sender_user_id=resolved_sender_user_id,
            sender_graph_root_path=_user_graph_root(resolved_sender_user_id),
        )


class GraphMailCollector:
    def __init__(self, api_client: GraphApiClient) -> None:
        self.api_client = api_client

    def collect_messages(
        self,
        auth_context: AuthContext,
        window_start: datetime,
        window_end: datetime,
    ) -> Sequence[MessageRecord]:
        filter_value = (
            "receivedDateTime ge {0} and receivedDateTime le {1}"
        ).format(window_start.isoformat(), window_end.isoformat())
        select_value = ",".join(
            (
                "id",
                "conversationId",
                "internetMessageId",
                "subject",
                "from",
                "toRecipients",
                "ccRecipients",
                "receivedDateTime",
                "bodyPreview",
                "categories",
                "flag",
                "isRead",
                "hasAttachments",
                "webLink",
            )
        )
        payloads = self.api_client.list_collection(
            "{0}/mailFolders/Inbox/messages".format(auth_context.graph_root_path),
            access_token=auth_context.access_token,
            params={
                "$filter": filter_value,
                "$select": select_value,
                "$orderby": "receivedDateTime desc",
                "$top": 100,
            },
        )
        return tuple(normalize_message(item) for item in payloads)


class GraphCalendarCollector:
    def __init__(self, api_client: GraphApiClient) -> None:
        self.api_client = api_client

    def collect_meetings(
        self,
        auth_context: AuthContext,
        window_start: datetime,
        window_end: datetime,
    ) -> Sequence[MeetingRecord]:
        payloads = self.api_client.list_collection(
            "{0}/calendar/calendarView".format(auth_context.graph_root_path),
            access_token=auth_context.access_token,
            params={
                "startDateTime": window_start.isoformat(),
                "endDateTime": window_end.isoformat(),
                "$top": 100,
                "$orderby": "start/dateTime",
            },
            headers={"Prefer": 'outlook.timezone="UTC"'},
        )
        return tuple(normalize_meeting(item) for item in payloads)


class GraphDigestDelivery:
    def __init__(self, api_client: GraphApiClient) -> None:
        self.api_client = api_client

    def deliver_digest(self, auth_context: AuthContext, payload) -> None:
        graph_message = payload.delivery_payload.get("graph_message")
        if not isinstance(graph_message, dict):
            raise ValueError("graph_send delivery requires a `graph_message` payload.")
        message_payload = dict(graph_message)
        recipients = message_payload.get("toRecipients")
        if not isinstance(recipients, list) or not recipients:
            profile = self.api_client.get_object(auth_context.graph_root_path, access_token=auth_context.access_token)
            mailbox_address = str(profile.get("mail") or profile.get("userPrincipalName") or "").strip()
            if not mailbox_address:
                raise ValueError("graph_send delivery could not determine a mailbox recipient from the Graph profile.")
            message_payload["toRecipients"] = [
                {
                    "emailAddress": {
                        "address": mailbox_address,
                    }
                }
            ]
        self.api_client.post_object(
            "{0}/sendMail".format(auth_context.sender_graph_root_path or auth_context.graph_root_path),
            access_token=auth_context.access_token,
            payload={
                "message": message_payload,
                "saveToSentItems": True,
            },
            expected_statuses=(202,),
        )

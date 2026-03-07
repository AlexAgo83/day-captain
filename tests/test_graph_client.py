from datetime import datetime
from datetime import timezone
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from day_captain.adapters.graph import GraphDelegatedAuthProvider
from day_captain.adapters.graph import GraphApiClient
from day_captain.adapters.graph import GraphDigestDelivery
from day_captain.adapters.graph import GraphMailCollector
from day_captain.adapters.graph import normalize_meeting
from day_captain.adapters.graph import normalize_message
from day_captain.models import AuthContext
from day_captain.models import DigestPayload


class FakeGraphApiClient:
    def __init__(self) -> None:
        self.calls = []

    def get_object(self, path, access_token, params=None, headers=None):
        self.calls.append((path, access_token))
        return {"id": "user-123", "userPrincipalName": "alex@example.com"}


class EmptyCollectionApiClient:
    def __init__(self) -> None:
        self.calls = []

    def get_object(self, path, access_token, params=None, headers=None):
        self.calls.append((path, access_token))
        return {"@odata.context": "https://graph.microsoft.com/v1.0/$metadata#empty", "value": []}


class CollectionRecorderApiClient:
    def __init__(self) -> None:
        self.calls = []

    def list_collection(self, path, access_token, params=None, headers=None):
        self.calls.append((path, access_token, params))
        return ()


class DeliveryRecorderApiClient:
    def __init__(self) -> None:
        self.calls = []

    def post_object(self, path, access_token, payload, headers=None, expected_statuses=(200, 201, 202, 204)):
        self.calls.append((path, access_token, payload, headers, expected_statuses))
        return {}


class GraphAdapterTest(unittest.TestCase):
    def test_auth_provider_uses_bearer_token_and_me_profile(self) -> None:
        api_client = FakeGraphApiClient()
        provider = GraphDelegatedAuthProvider(
            access_token="delegated-token",
            api_client=api_client,
        )

        context = provider.authenticate(("Mail.Read", "Calendars.Read"))

        self.assertEqual(context.access_token, "delegated-token")
        self.assertEqual(context.user_id, "user-123")
        self.assertEqual(api_client.calls, [("/me", "delegated-token")])

    def test_normalize_message_maps_graph_payload(self) -> None:
        payload = {
            "id": "msg-1",
            "conversationId": "thread-1",
            "internetMessageId": "<x@example.com>",
            "subject": "Urgent budget review",
            "from": {"emailAddress": {"address": "boss@example.com"}},
            "toRecipients": [{"emailAddress": {"address": "alex@example.com"}}],
            "ccRecipients": [{"emailAddress": {"address": "finance@example.com"}}],
            "receivedDateTime": "2026-03-07T07:45:00Z",
            "bodyPreview": "Please review before noon.",
            "categories": ["Finance"],
            "isRead": False,
            "hasAttachments": True,
        }

        message = normalize_message(payload)

        self.assertEqual(message.graph_message_id, "msg-1")
        self.assertEqual(message.thread_id, "thread-1")
        self.assertEqual(message.internet_message_id, "<x@example.com>")
        self.assertEqual(message.from_address, "boss@example.com")
        self.assertEqual(message.to_addresses, ("alex@example.com",))
        self.assertEqual(message.cc_addresses, ("finance@example.com",))
        self.assertEqual(message.received_at, datetime(2026, 3, 7, 7, 45, tzinfo=timezone.utc))
        self.assertTrue(message.is_unread)
        self.assertTrue(message.has_attachments)

    def test_normalize_meeting_maps_graph_payload(self) -> None:
        payload = {
            "id": "mtg-1",
            "subject": "Weekly leadership sync",
            "start": {"dateTime": "2026-03-07T10:00:00+00:00", "timeZone": "UTC"},
            "end": {"dateTime": "2026-03-07T10:30:00+00:00", "timeZone": "UTC"},
            "organizer": {"emailAddress": {"address": "ceo@example.com"}},
            "attendees": [
                {"emailAddress": {"address": "alex@example.com"}},
                {"emailAddress": {"address": "pm@example.com"}},
            ],
            "location": {"displayName": "Teams"},
            "onlineMeeting": {"joinUrl": "https://teams.example.com/join/1"},
            "bodyPreview": "Discuss weekly priorities.",
            "isOnlineMeeting": True,
        }

        meeting = normalize_meeting(payload)

        self.assertEqual(meeting.graph_event_id, "mtg-1")
        self.assertEqual(meeting.organizer_address, "ceo@example.com")
        self.assertEqual(meeting.attendees, ("alex@example.com", "pm@example.com"))
        self.assertEqual(meeting.location, "Teams")
        self.assertTrue(meeting.is_online_meeting)
        self.assertEqual(meeting.join_url, "https://teams.example.com/join/1")

    def test_list_collection_accepts_empty_value_list(self) -> None:
        client = GraphApiClient(
            base_url="https://graph.microsoft.com/v1.0",
            opener=None,
        )
        client.get_object = EmptyCollectionApiClient().get_object

        items = client.list_collection("/me/calendar/calendarView", access_token="token")

        self.assertEqual(items, ())

    def test_mail_collector_reads_from_inbox_only(self) -> None:
        api_client = CollectionRecorderApiClient()
        collector = GraphMailCollector(api_client)
        auth_context = AuthContext(
            access_token="delegated-token",
            granted_scopes=("User.Read", "Mail.Read"),
            user_id="user-123",
        )

        collector.collect_messages(
            auth_context,
            datetime(2026, 3, 6, 8, 0, tzinfo=timezone.utc),
            datetime(2026, 3, 7, 8, 0, tzinfo=timezone.utc),
        )

        self.assertEqual(len(api_client.calls), 1)
        path, access_token, params = api_client.calls[0]
        self.assertEqual(path, "/me/mailFolders/Inbox/messages")
        self.assertEqual(access_token, "delegated-token")
        self.assertEqual(params["$top"], 100)

    def test_graph_digest_delivery_posts_send_mail_request(self) -> None:
        api_client = DeliveryRecorderApiClient()
        delivery = GraphDigestDelivery(api_client)
        auth_context = AuthContext(
            access_token="delegated-token",
            granted_scopes=("User.Read", "Mail.Read", "Mail.Send"),
            user_id="user-123",
        )
        payload = DigestPayload(
            run_id="run-1",
            generated_at=datetime(2026, 3, 7, 8, 0, tzinfo=timezone.utc),
            window_start=datetime(2026, 3, 6, 8, 0, tzinfo=timezone.utc),
            window_end=datetime(2026, 3, 7, 8, 0, tzinfo=timezone.utc),
            delivery_mode="graph_send",
            delivery_payload={
                "graph_message": {
                    "subject": "Day Captain digest",
                    "body": {"contentType": "Text", "content": "Digest body"},
                }
            },
        )

        delivery.deliver_digest(auth_context, payload)

        self.assertEqual(len(api_client.calls), 1)
        path, access_token, posted_payload, _headers, expected_statuses = api_client.calls[0]
        self.assertEqual(path, "/me/sendMail")
        self.assertEqual(access_token, "delegated-token")
        self.assertEqual(posted_payload["message"]["subject"], "Day Captain digest")
        self.assertTrue(posted_payload["saveToSentItems"])
        self.assertEqual(expected_statuses, (202,))


if __name__ == "__main__":
    unittest.main()

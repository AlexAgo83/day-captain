from datetime import datetime
from datetime import timezone
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from day_captain.adapters.graph import GraphDelegatedAuthProvider
from day_captain.adapters.graph import GraphApiClient
from day_captain.adapters.graph import normalize_meeting
from day_captain.adapters.graph import normalize_message


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


if __name__ == "__main__":
    unittest.main()

from datetime import datetime
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from day_captain.adapters.news import ExternalNewsProviderError
from day_captain.adapters.news import RssExternalNewsProvider


class _StaticResponse:
    def __init__(self, payload: bytes) -> None:
        self.payload = payload

    def read(self) -> bytes:
        return self.payload

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        return None


class ExternalNewsProviderTest(unittest.TestCase):
    def test_rss_provider_returns_bounded_items_with_source_fields(self) -> None:
        xml = b"""<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0">
  <channel>
    <title>Example Feed</title>
    <item>
      <title>Headline One</title>
      <link>https://example.com/one</link>
      <description>Summary one for the first item.</description>
      <source url="https://example.com">Example Source</source>
    </item>
    <item>
      <title>Headline Two</title>
      <link>https://example.com/two</link>
      <description>Summary two for the second item.</description>
      <source url="https://example.com">Example Source</source>
    </item>
  </channel>
</rss>"""
        provider = RssExternalNewsProvider(
            feed_url="https://example.com/feed.xml",
            max_items=1,
            opener=lambda request, timeout=0: _StaticResponse(xml),
        )

        items = provider.get_news(datetime(2026, 3, 9))

        self.assertEqual(len(items), 1)
        self.assertEqual(items[0].headline, "Headline One")
        self.assertEqual(items[0].source_name, "Example Source")
        self.assertEqual(items[0].source_url, "https://example.com/one")

    def test_rss_provider_rejects_malformed_payload(self) -> None:
        provider = RssExternalNewsProvider(
            feed_url="https://example.com/feed.xml",
            opener=lambda request, timeout=0: _StaticResponse(b"not xml"),
        )

        with self.assertRaises(ExternalNewsProviderError):
            provider.get_news(datetime(2026, 3, 9))

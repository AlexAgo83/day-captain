"""External news providers for Day Captain."""

from datetime import datetime
from html import unescape
from typing import Optional
from typing import Sequence
from urllib.error import HTTPError
from urllib.error import URLError
from urllib.parse import urlparse
from urllib.request import Request
from urllib.request import urlopen
import xml.etree.ElementTree as ET

from day_captain.models import ExternalNewsItem


class ExternalNewsProviderError(ValueError):
    """Raised when an external news provider cannot return usable data."""


def _xml_text(node: Optional[ET.Element], path: str) -> str:
    if node is None:
        return ""
    child = node.find(path)
    if child is None or child.text is None:
        return ""
    return " ".join(unescape(child.text).split())


def _domain_label(url: str) -> str:
    parsed = urlparse(str(url or "").strip())
    return parsed.netloc.lower().lstrip("www.")


def _truncate_summary(value: str, max_chars: int = 180) -> str:
    text = " ".join(str(value or "").split())
    if len(text) <= max_chars:
        return text
    shortened = text[: max_chars - 1].rsplit(" ", 1)[0].strip()
    return "{0}…".format(shortened or text[: max_chars - 1].strip())


class RssExternalNewsProvider:
    def __init__(
        self,
        feed_url: str,
        timeout_seconds: int = 6,
        max_items: int = 3,
        opener=urlopen,
    ) -> None:
        self.feed_url = str(feed_url or "").strip()
        self.timeout_seconds = max(1, int(timeout_seconds))
        self.max_items = max(1, int(max_items))
        self.opener = opener

    def get_news(self, current_time: datetime) -> Sequence[ExternalNewsItem]:
        del current_time
        if not self.feed_url:
            return ()
        request = Request(
            self.feed_url,
            headers={"User-Agent": "day-captain/1.0 (+https://github.com/AlexAgo83/day-captain)"},
        )
        try:
            with self.opener(request, timeout=self.timeout_seconds) as response:
                payload = response.read()
        except (HTTPError, URLError) as exc:
            raise ExternalNewsProviderError("Unable to reach external news provider.") from exc
        try:
            root = ET.fromstring(payload)
        except ET.ParseError as exc:
            raise ExternalNewsProviderError("Expected RSS or Atom XML from external news provider.") from exc
        channel = root.find("./channel")
        if channel is None:
            raise ExternalNewsProviderError("Expected RSS channel payload from external news provider.")
        feed_title = _xml_text(channel, "title")
        items = []
        for item in channel.findall("item"):
            headline = _xml_text(item, "title")
            source_url = _xml_text(item, "link")
            source_name = _xml_text(item, "source") or feed_title or _domain_label(source_url)
            summary = _truncate_summary(_xml_text(item, "description"))
            if not headline or not source_url or not source_name:
                continue
            items.append(
                ExternalNewsItem(
                    headline=headline,
                    summary=summary,
                    source_name=source_name,
                    source_url=source_url,
                )
            )
            if len(items) >= self.max_items:
                break
        return tuple(items)

"""Business logic services for Day Captain."""

from datetime import datetime
from datetime import timedelta
from datetime import timezone
import re
from typing import Iterable
from typing import Mapping
from typing import Optional
from typing import Sequence
from zoneinfo import ZoneInfo

from day_captain.models import DigestEntry
from day_captain.models import DigestPayload
from day_captain.models import DigestRunRecord
from day_captain.models import FeedbackRecord
from day_captain.models import MeetingRecord
from day_captain.models import MessageRecord
from day_captain.models import UserPreference
from day_captain.ports import Storage


SECTION_NAMES = (
    "critical_topics",
    "actions_to_take",
    "watch_items",
    "upcoming_meetings",
)

STOPWORDS = {
    "a",
    "an",
    "and",
    "as",
    "at",
    "before",
    "by",
    "for",
    "from",
    "in",
    "is",
    "need",
    "needed",
    "new",
    "of",
    "on",
    "please",
    "re",
    "review",
    "the",
    "this",
    "to",
    "update",
    "with",
}

ACTION_PATTERNS = (
    "action needed",
    "please review",
    "please approve",
    "need your input",
    "follow up",
    "todo",
    "approval",
    "review before",
    "respond by",
    "feedback",
    "remarks",
    "remarques",
    "merci de",
    "please update",
    "a imprimer",
    "à imprimer",
    "piece jointe",
    "pièce jointe",
    "lien de telechargement",
    "lien de téléchargement",
    "download link",
)

CRITICAL_PATTERNS = (
    "urgent",
    "critical",
    "incident",
    "outage",
    "deadline",
    "escalation",
    "asap",
    "security",
    "breach",
    "production",
)

NEWSLETTER_PATTERNS = (
    "newsletter",
    "digest",
    "unsubscribe",
    "subscription",
    "daily news",
    "weekly update",
    "aggregate report",
    "report domain:",
    "submitter:",
    "dmarc",
    "rua tag",
)

SELF_DIGEST_PATTERNS = (
    "day captain digest for",
    "day captain morning digest",
)

AUTOMATED_SENDERS = (
    "noreply",
    "no-reply",
    "notification",
    "notifications",
    "automated",
    "daemon",
    "postmaster",
    "enterprise.protection.outlook.com",
    "protection.outlook.com",
)

COLD_OUTREACH_PATTERNS = (
    "we help",
    "key features",
    "connector and pinout",
    "logo printing",
    "oem support",
    "custom cable solutions",
    "commercial vehicles",
)

EXECUTIVE_HINTS = (
    "ceo",
    "cfo",
    "cto",
    "coo",
    "boss",
    "manager",
    "director",
    "vp",
    "head",
    "leadership",
)

SECTION_PRIORITY = {
    "critical_topics": 3,
    "actions_to_take": 2,
    "watch_items": 1,
}

TRIVIAL_PREVIEW_LINES = (
    "sent from outlook for mac",
    "sent from outlook for ios",
    "envoye a partir de outlook pour ios",
    "envoye a partir de outlook pour mac",
    "envoyé à partir de outlook pour ios",
    "envoyé à partir de outlook pour mac",
)

QUOTE_BOUNDARY_PREFIXES = (
    "from:",
    "de :",
    "de:",
    "date:",
    "to:",
    "a :",
    "a:",
    "à :",
    "à:",
    "subject:",
    "objet :",
    "objet:",
)


def _normalize_text(*parts: str) -> str:
    return " ".join(part.strip().lower() for part in parts if part).strip()


def _contains_any(text: str, patterns: Iterable[str]) -> bool:
    return any(pattern in text for pattern in patterns)


def _tokenize_subject(subject: str) -> Sequence[str]:
    tokens = []
    for token in re.findall(r"[a-z0-9]{3,}", subject.lower()):
        if token not in STOPWORDS:
            tokens.append(token)
    return tuple(tokens)


def _domain_from_email(address: str) -> str:
    if "@" not in address:
        return ""
    return address.split("@", 1)[1].lower()


def _clamp_weight(value: float) -> float:
    return max(-3.0, min(3.0, round(value, 2)))


def _clean_preview(preview: str) -> str:
    if not preview:
        return ""
    normalized = preview.replace("\r\n", "\n").replace("\r", "\n").strip()
    if not normalized:
        return ""

    selected_lines = []
    for raw_line in normalized.split("\n"):
        line = raw_line.strip()
        if not line:
            continue

        lowered = line.lower()
        if lowered in TRIVIAL_PREVIEW_LINES:
            if selected_lines:
                break
            continue
        if lowered.startswith("________________________________") or lowered.startswith("-----original message-----"):
            break
        if lowered.startswith(QUOTE_BOUNDARY_PREFIXES):
            if selected_lines:
                break
            continue

        selected_lines.append(line)
        if len(selected_lines) >= 3:
            break

    cleaned = " ".join(selected_lines).strip()
    return cleaned[:280]


def _is_self_digest_message(subject: str, preview: str) -> bool:
    normalized_subject = _normalize_text(subject)
    normalized_preview = _normalize_text(preview)
    if _contains_any(normalized_subject, SELF_DIGEST_PATTERNS):
        return True
    return _contains_any(normalized_preview, SELF_DIGEST_PATTERNS)


class DeterministicScoringEngine:
    def prioritize(
        self,
        messages: Sequence[MessageRecord],
        meetings: Sequence[MeetingRecord],
        preferences: Sequence[UserPreference],
        reference_time: Optional[datetime] = None,
    ) -> Sequence[DigestEntry]:
        now = reference_time or datetime.now(timezone.utc)
        preference_weights = {
            preference.preference_key: preference.weight for preference in preferences
        }
        prioritized = []
        thread_candidates = {}
        for message in messages:
            entry = self._score_message(message, preference_weights, now)
            if entry is not None:
                thread_key = self._thread_key(message)
                existing = thread_candidates.get(thread_key)
                if existing is None:
                    thread_candidates[thread_key] = (message, entry, 1)
                else:
                    kept_message, kept_entry, duplicate_count = existing
                    duplicate_count += 1
                    if self._message_rank(message, entry) > self._message_rank(kept_message, kept_entry):
                        thread_candidates[thread_key] = (message, entry, duplicate_count)
                    else:
                        thread_candidates[thread_key] = (kept_message, kept_entry, duplicate_count)
        for _message, entry, duplicate_count in thread_candidates.values():
            prioritized.append(self._with_thread_reason(entry, duplicate_count))
        for meeting in meetings:
            prioritized.append(self._score_meeting(meeting, now))
        return tuple(sorted(prioritized, key=lambda item: (-item.score, item.title.lower())))

    def _thread_key(self, message: MessageRecord) -> str:
        if message.thread_id:
            return message.thread_id
        subject = re.sub(r"^(re|fw|fwd)\s*:\s*", "", (message.subject or "").strip(), flags=re.IGNORECASE)
        return subject.lower() or message.graph_message_id

    def _message_rank(self, message: MessageRecord, entry: DigestEntry) -> tuple:
        return (
            SECTION_PRIORITY.get(entry.section_name, 0),
            entry.score,
            message.received_at.timestamp(),
            1 if message.is_unread else 0,
            1 if message.has_attachments else 0,
        )

    def _with_thread_reason(self, entry: DigestEntry, duplicate_count: int) -> DigestEntry:
        if duplicate_count <= 1:
            return entry
        return DigestEntry(
            title=entry.title,
            summary=entry.summary,
            section_name=entry.section_name,
            source_kind=entry.source_kind,
            source_id=entry.source_id,
            score=entry.score,
            reason_codes=tuple(entry.reason_codes) + ("thread_collapsed",),
            guardrail_applied=entry.guardrail_applied,
        )

    def _score_message(
        self,
        message: MessageRecord,
        preference_weights: Mapping[str, float],
        now: datetime,
    ) -> Optional[DigestEntry]:
        subject = message.subject or "(no subject)"
        cleaned_preview = _clean_preview(message.body_preview)
        combined_text = _normalize_text(subject, message.body_preview)
        sender = message.from_address.lower()
        reason_codes = []
        score = 0.0
        guardrail = False

        if not (message.subject or "").strip() and not cleaned_preview:
            return None
        if _is_self_digest_message(subject, cleaned_preview):
            return None

        sender_key = "sender:{0}".format(sender)
        domain = _domain_from_email(sender)
        domain_key = "domain:{0}".format(domain) if domain else ""
        keyword_bonus = 0.0
        for token in _tokenize_subject(subject):
            keyword_bonus += preference_weights.get("keyword:{0}".format(token), 0.0)

        preference_bonus = preference_weights.get(sender_key, 0.0)
        if domain_key:
            preference_bonus += preference_weights.get(domain_key, 0.0)
        preference_bonus += keyword_bonus
        if preference_bonus:
            score += preference_bonus
            reason_codes.append("preference_signal")

        if message.is_unread:
            score += 0.4
            reason_codes.append("unread")
        if message.has_attachments:
            score += 0.25
            reason_codes.append("attachment_present")
        if message.to_addresses:
            score += 1.0
            reason_codes.append("direct_recipient")
        elif message.cc_addresses:
            score -= 0.75
            reason_codes.append("cc_only")

        age_hours = max(0.0, (now - message.received_at).total_seconds() / 3600.0)
        if age_hours <= 2:
            score += 0.75
            reason_codes.append("recent")
        elif age_hours <= 8:
            score += 0.4
            reason_codes.append("same_day")

        if _contains_any(combined_text, ACTION_PATTERNS):
            score += 1.5
            reason_codes.append("action_keyword")
        if _contains_any(combined_text, CRITICAL_PATTERNS):
            score += 2.0
            guardrail = True
            reason_codes.append("critical_keyword")
        if _contains_any(sender, EXECUTIVE_HINTS):
            score += 1.0
            guardrail = True
            reason_codes.append("executive_sender")

        is_newsletter = _contains_any(combined_text, NEWSLETTER_PATTERNS)
        is_automated = _contains_any(sender, AUTOMATED_SENDERS)
        is_bulk_report = "report domain:" in combined_text and "submitter:" in combined_text
        is_cold_outreach = _contains_any(combined_text, COLD_OUTREACH_PATTERNS)
        low_signal_cc = bool(message.cc_addresses and not message.to_addresses and not guardrail and "action_keyword" not in reason_codes)
        if is_bulk_report:
            reason_codes.append("bulk_report")
        if is_cold_outreach:
            reason_codes.append("cold_outreach")
        if (is_newsletter or is_automated or is_bulk_report or is_cold_outreach or low_signal_cc) and not guardrail:
            reason_codes.append("noise_filtered")
            if is_newsletter or is_automated or is_bulk_report or is_cold_outreach:
                return None
            if score < 1.5:
                return None
        if score <= 0.0 and not guardrail:
            return None

        if "action_keyword" in reason_codes and (
            message.has_attachments or "download" in combined_text or "telechargement" in combined_text or "téléchargement" in combined_text
        ):
            score += 0.5
            reason_codes.append("deliverable_shared")

        if guardrail:
            section_name = "critical_topics"
        elif "action_keyword" in reason_codes:
            section_name = "actions_to_take"
        else:
            section_name = "watch_items"

        summary = self._summarize_message(message, cleaned_preview, reason_codes)
        return DigestEntry(
            title=subject,
            summary=summary,
            section_name=section_name,
            source_kind="message",
            source_id=message.graph_message_id,
            score=round(score, 2),
            reason_codes=tuple(reason_codes),
            guardrail_applied=guardrail,
        )

    def _score_meeting(self, meeting: MeetingRecord, now: datetime) -> DigestEntry:
        hours_until = (meeting.start_at - now).total_seconds() / 3600.0
        score = 1.0
        reason_codes = ["meeting_context"]
        if hours_until <= 2:
            score += 1.5
            reason_codes.append("meeting_soon")
        elif hours_until <= 6:
            score += 1.0
            reason_codes.append("meeting_today")
        if meeting.is_online_meeting:
            score += 0.25
            reason_codes.append("online_meeting")
        summary = "Starts {0} with {1}".format(
            meeting.start_at.strftime("%H:%M"),
            meeting.organizer_address or "organizer unknown",
        )
        if meeting.location:
            summary += " in {0}".format(meeting.location)
        return DigestEntry(
            title=meeting.subject or "(untitled meeting)",
            summary=summary,
            section_name="upcoming_meetings",
            source_kind="meeting",
            source_id=meeting.graph_event_id,
            score=round(score, 2),
            reason_codes=tuple(reason_codes),
            guardrail_applied=False,
        )

    def _summarize_message(
        self,
        message: MessageRecord,
        cleaned_preview: str,
        reason_codes: Sequence[str],
    ) -> str:
        preview = cleaned_preview or (message.body_preview or "").strip()
        base = preview if preview else "From {0}".format(message.from_address)
        if "critical_keyword" in reason_codes:
            return "Urgent: {0}".format(base)
        if "action_keyword" in reason_codes:
            return base
        return base


class StructuredDigestRenderer:
    def __init__(self, display_timezone: str = "UTC") -> None:
        self.display_timezone = display_timezone

    def render(
        self,
        run_id: str,
        generated_at: datetime,
        window_start: datetime,
        window_end: datetime,
        delivery_mode: str,
        prioritized_items: Sequence[DigestEntry],
    ) -> DigestPayload:
        sections = {name: [] for name in SECTION_NAMES}
        for item in prioritized_items:
            target_section = item.section_name if item.section_name in sections else "watch_items"
            sections[target_section].append(item)
        for name in SECTION_NAMES:
            sections[name] = sorted(sections[name], key=lambda item: (-item.score, item.title.lower()))[:5]

        delivery_subject = "Day Captain digest for {0}".format(generated_at.date().isoformat())
        delivery_body = self._build_delivery_body(generated_at, window_start, window_end, sections)
        delivery_html = self._build_delivery_html(generated_at, window_start, window_end, sections)
        delivery_payload = {
            "mode": delivery_mode,
            "run_id": run_id,
            "subject": delivery_subject,
            "body": delivery_body,
            "html_body": delivery_html,
            "sections": {
                name: [self._entry_payload(item) for item in sections[name]]
                for name in SECTION_NAMES
            },
        }
        if delivery_mode == "graph_send":
            delivery_payload["graph_message"] = {
                "subject": delivery_subject,
                "body": {
                    "contentType": "HTML",
                    "content": delivery_html,
                },
            }

        return DigestPayload(
            run_id=run_id,
            generated_at=generated_at,
            window_start=window_start,
            window_end=window_end,
            delivery_mode=delivery_mode,
            delivery_subject=delivery_subject,
            delivery_body=delivery_body,
            delivery_payload=delivery_payload,
            critical_topics=tuple(sections["critical_topics"]),
            actions_to_take=tuple(sections["actions_to_take"]),
            watch_items=tuple(sections["watch_items"]),
            upcoming_meetings=tuple(sections["upcoming_meetings"]),
        )

    def _entry_payload(self, item: DigestEntry) -> Mapping[str, object]:
        return {
            "title": item.title,
            "summary": item.summary,
            "source_kind": item.source_kind,
            "source_id": item.source_id,
            "score": item.score,
            "reason_codes": list(item.reason_codes),
            "guardrail_applied": item.guardrail_applied,
        }

    def _build_delivery_body(
        self,
        generated_at: datetime,
        window_start: datetime,
        window_end: datetime,
        sections: Mapping[str, Sequence[DigestEntry]],
    ) -> str:
        generated_label = self._format_timestamp(generated_at)
        window_label = "{0} to {1}".format(
            self._format_timestamp(window_start, include_zone=False),
            self._format_timestamp(window_end),
        )
        lines = [
            "Day Captain digest",
            "Generated {0}".format(generated_label),
            "Review window: {0}".format(window_label),
            "",
        ]
        labels = {
            "critical_topics": "Critical topics",
            "actions_to_take": "Actions to take",
            "watch_items": "Watch items",
            "upcoming_meetings": "Upcoming meetings",
        }
        for name in SECTION_NAMES:
            lines.append(labels[name])
            items = sections[name]
            if not items:
                lines.append("- None")
            else:
                for item in items:
                    lines.append("- {0}".format(item.title))
                    lines.append("  {0}".format(item.summary))
            lines.append("")
        return "\n".join(lines).strip()

    def _build_delivery_html(
        self,
        generated_at: datetime,
        window_start: datetime,
        window_end: datetime,
        sections: Mapping[str, Sequence[DigestEntry]],
    ) -> str:
        generated_label = self._format_timestamp(generated_at)
        window_label = "{0} to {1}".format(
            self._format_timestamp(window_start, include_zone=False),
            self._format_timestamp(window_end),
        )
        labels = {
            "critical_topics": "Critical topics",
            "actions_to_take": "Actions to take",
            "watch_items": "Watch items",
            "upcoming_meetings": "Upcoming meetings",
        }
        parts = [
            "<html><body style=\"font-family:Segoe UI,Helvetica,Arial,sans-serif;color:#1f2937;line-height:1.5;\">",
            "<div style=\"max-width:720px;margin:0 auto;padding:24px;\">",
            "<h1 style=\"margin:0 0 8px;font-size:28px;color:#0f172a;\">Day Captain digest</h1>",
            "<p style=\"margin:0 0 4px;color:#475569;\"><strong>Generated</strong> {0}</p>".format(generated_label),
            "<p style=\"margin:0 0 24px;color:#475569;\"><strong>Review window</strong> {0}</p>".format(window_label),
        ]
        for name in SECTION_NAMES:
            parts.append(
                "<section style=\"margin:0 0 24px;\"><h2 style=\"margin:0 0 10px;font-size:20px;color:#0f172a;\">{0}</h2>".format(
                    labels[name]
                )
            )
            items = sections[name]
            if not items:
                parts.append("<p style=\"margin:0;color:#64748b;\">None</p>")
            else:
                parts.append("<ul style=\"margin:0;padding-left:20px;\">")
                for item in items:
                    parts.append(
                        "<li style=\"margin:0 0 12px;\"><strong>{0}</strong><br><span style=\"color:#334155;\">{1}</span></li>".format(
                            self._html_escape(item.title),
                            self._html_escape(item.summary),
                        )
                    )
                parts.append("</ul>")
            parts.append("</section>")
        parts.append("</div></body></html>")
        return "".join(parts)

    def _format_timestamp(self, value: datetime, include_zone: bool = True) -> str:
        target = value
        try:
            zone = ZoneInfo(self.display_timezone)
            target = value.astimezone(zone)
        except Exception:
            zone = None
        rendered = target.strftime("%a %d %b %Y at %H:%M")
        if include_zone and zone is not None:
            rendered += " {0}".format(target.tzname() or self.display_timezone)
        elif include_zone:
            rendered += " UTC"
        return rendered

    def _html_escape(self, value: str) -> str:
        return (
            value.replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
        )


class IdentityDigestWordingEngine:
    def rewrite(
        self,
        prioritized_items: Sequence[DigestEntry],
    ) -> Sequence[DigestEntry]:
        return tuple(prioritized_items)


class LlmDigestWordingEngine:
    def __init__(
        self,
        provider,
        shortlist_limit: int = 5,
        enabled_sections: Optional[Sequence[str]] = None,
    ) -> None:
        self.provider = provider
        self.shortlist_limit = max(0, shortlist_limit)
        self.enabled_sections = tuple(enabled_sections or ())

    def rewrite(
        self,
        prioritized_items: Sequence[DigestEntry],
    ) -> Sequence[DigestEntry]:
        items = tuple(prioritized_items)
        if self.shortlist_limit <= 0 or not items:
            return items
        shortlisted = tuple(
            item
            for item in items
            if not self.enabled_sections or item.section_name in self.enabled_sections
        )[: self.shortlist_limit]
        if not shortlisted:
            return items
        try:
            rewritten = self.provider.rewrite_summaries(shortlisted)
        except Exception:
            return items
        updated_items = []
        for item in items:
            ref = "{0}:{1}".format(item.source_kind, item.source_id)
            summary = str(rewritten.get(ref) or "").strip()
            if not summary:
                updated_items.append(item)
                continue
            updated_items.append(
                DigestEntry(
                    title=item.title,
                    summary=summary,
                    section_name=item.section_name,
                    source_kind=item.source_kind,
                    source_id=item.source_id,
                    score=item.score,
                    reason_codes=item.reason_codes,
                    guardrail_applied=item.guardrail_applied,
                )
            )
        return tuple(updated_items)


class SnapshotRecallProvider:
    def build_recall(self, run: DigestRunRecord) -> DigestPayload:
        payload = run.summary
        if payload.delivery_body:
            return payload
        renderer = StructuredDigestRenderer()
        items = []
        for section_name in SECTION_NAMES:
            for entry in getattr(payload, section_name):
                items.append(entry)
        return renderer.render(
            run_id=payload.run_id,
            generated_at=payload.generated_at,
            window_start=payload.window_start,
            window_end=payload.window_end,
            delivery_mode=payload.delivery_mode,
            prioritized_items=tuple(items),
        )


class PreferenceFeedbackProcessor:
    def process_feedback(self, storage: Storage, feedback: FeedbackRecord) -> None:
        storage.save_feedback(feedback)
        if feedback.source_kind != "message":
            return
        message = storage.get_message(feedback.source_id)
        if message is None:
            return
        delta = self._feedback_delta(feedback)
        if delta == 0.0:
            return

        existing = {pref.preference_key: pref for pref in storage.load_preferences()}
        updates = []
        timestamp = feedback.recorded_at

        sender_key = "sender:{0}".format(message.from_address.lower())
        updates.append(self._updated_preference(existing.get(sender_key), sender_key, "sender", delta, timestamp))

        domain = _domain_from_email(message.from_address)
        if domain:
            domain_key = "domain:{0}".format(domain)
            updates.append(self._updated_preference(existing.get(domain_key), domain_key, "domain", delta * 0.5, timestamp))

        for token in _tokenize_subject(message.subject)[:3]:
            keyword_key = "keyword:{0}".format(token)
            updates.append(
                self._updated_preference(existing.get(keyword_key), keyword_key, "keyword", delta * 0.25, timestamp)
            )

        storage.upsert_preferences(tuple(updates))

    def _feedback_delta(self, feedback: FeedbackRecord) -> float:
        signal = feedback.signal_type.strip().lower()
        value = feedback.signal_value.strip().lower()
        positive = {"true", "1", "yes", "positive", "up", "useful"}
        negative = {"false", "0", "no", "negative", "down", "not_useful"}
        if signal in {"useful", "liked"}:
            return 0.75 if value in positive else -0.75
        if signal in {"not_useful", "dismissed"}:
            return -0.75 if value in positive else 0.0
        if value in positive:
            return 0.5
        if value in negative:
            return -0.5
        return 0.0

    def _updated_preference(
        self,
        existing: Optional[UserPreference],
        key: str,
        preference_type: str,
        delta: float,
        updated_at: datetime,
    ) -> UserPreference:
        current_weight = existing.weight if existing is not None else 0.0
        return UserPreference(
            preference_key=key,
            preference_type=preference_type,
            weight=_clamp_weight(current_weight + delta),
            source="feedback",
            updated_at=updated_at,
        )

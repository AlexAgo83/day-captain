"""Structured digest-oriented parsing helpers."""

from dataclasses import dataclass
from datetime import datetime
from typing import Mapping
from typing import Sequence
from zoneinfo import ZoneInfo

from day_captain.models import MeetingRecord
from day_captain.models import MessageRecord


ENGLISH_HINTS = {"please", "review", "need", "input", "thanks", "before", "confirm", "update"}
FRENCH_HINTS = {"bonjour", "merci", "retour", "besoin", "valider", "avant", "aujourd", "demain"}
SUSPICIOUS_URGENCY = ("urgent", "immediately", "asap", "final notice", "account suspended", "account suspension")
SENSITIVE_REQUESTS = (
    "bank account",
    "wire transfer",
    "payment",
    "invoice",
    "gift card",
    "password",
    "credential",
    "login",
    "mfa",
)


def _display_zone(name: str):
    try:
        return ZoneInfo(name)
    except Exception:
        return ZoneInfo("UTC")


def _normalize_text(*values: str) -> str:
    return " ".join(" ".join(str(value or "").strip().lower().split()) for value in values if str(value or "").strip())


def _domain_from_email(value: str) -> str:
    candidate = str(value or "").strip().lower()
    if "@" not in candidate:
        return ""
    return candidate.split("@", 1)[1]


def _same_identity(left: str, right: str) -> bool:
    return str(left or "").strip().lower() == str(right or "").strip().lower()


def _humanize_identifier(value: str) -> str:
    candidate = str(value or "").strip()
    if not candidate:
        return ""
    local = candidate.split("@", 1)[0]
    cleaned = local.replace(".", " ").replace("_", " ").replace("-", " ")
    return " ".join(part.capitalize() for part in cleaned.split())


def _language_hint_for_text(value: str) -> str:
    normalized = _normalize_text(value)
    if not normalized:
        return ""
    tokens = [token.strip("'") for token in normalized.replace(",", " ").replace(".", " ").split()]
    english_score = sum(1 for token in tokens if token in ENGLISH_HINTS)
    french_score = sum(1 for token in tokens if token in FRENCH_HINTS)
    if english_score >= 2 and english_score > french_score:
        return "en"
    if french_score >= 2 and french_score > english_score:
        return "fr"
    return ""


def _target_recipient_display_name(message: MessageRecord) -> str:
    target_user = str(message.user_id or "").strip()
    if not target_user:
        return ""
    raw_payload = message.raw_payload if isinstance(message.raw_payload, Mapping) else {}
    recipients = list(raw_payload.get("toRecipients") or ()) + list(raw_payload.get("ccRecipients") or ())
    for recipient in recipients:
        if not isinstance(recipient, Mapping):
            continue
        email = recipient.get("emailAddress") or {}
        if not isinstance(email, Mapping):
            continue
        address = str(email.get("address") or "").strip()
        if not _same_identity(address, target_user):
            continue
        display_name = " ".join(str(email.get("name") or "").split())
        if display_name:
            return display_name
    return _humanize_identifier(target_user)


def _other_owner_display_name(message: MessageRecord) -> str:
    target_user = str(message.user_id or "").strip().lower()
    for address in message.to_addresses:
        if not _same_identity(address, target_user):
            return _humanize_identifier(address) or str(address)
    return ""


@dataclass(frozen=True)
class MailThreadDigestInput:
    thread_id: str
    message_count: int
    participants: Sequence[str]
    latest_sender_display_name: str
    latest_is_unread: bool
    target_recipient_display_name: str
    source_language_hint: str
    action_owner: str
    action_owner_display_name: str
    action_expected_from_user: bool
    relevance_to_user: bool
    risk_level: str
    risk_reasons: Sequence[str]
    trust_signals: Sequence[str]
    messages: Sequence[Mapping[str, str]]


@dataclass(frozen=True)
class AgendaDigestInput:
    event_kind: str
    recurrence_label: str
    related_messages: Sequence[Mapping[str, str]]
    local_sort_date: str


def build_mail_thread_digest_input(
    message: MessageRecord,
    thread_messages: Sequence[MessageRecord],
    *,
    display_timezone: str,
    action_detected: bool,
) -> MailThreadDigestInput:
    ordered = sorted(thread_messages, key=lambda item: item.received_at)
    zone = _display_zone(display_timezone)
    participants = []
    rendered_messages = []
    for candidate in ordered[-4:]:
        sender_name = _humanize_identifier(candidate.from_address) or candidate.from_address
        if sender_name and sender_name not in participants:
            participants.append(sender_name)
        rendered_messages.append(
            {
                "sender": sender_name,
                "received_at": candidate.received_at.astimezone(zone).isoformat(),
                "preview": " ".join(str(candidate.body_preview or "").split())[:180],
            }
        )
    normalized_text = _normalize_text(message.subject, message.body_preview)
    target_in_to = any(_same_identity(address, message.user_id) for address in message.to_addresses)
    target_in_cc = any(_same_identity(address, message.user_id) for address in message.cc_addresses)
    relevance_to_user = bool(target_in_to or target_in_cc or not message.user_id)
    action_owner = ""
    action_owner_display_name = ""
    action_expected_from_user = False
    if action_detected:
        if target_in_to and len(message.to_addresses) <= 1:
            action_owner = "user"
            action_expected_from_user = True
        elif target_in_to:
            action_owner = "shared"
            action_expected_from_user = True
        elif target_in_cc:
            action_owner = "other"
            action_owner_display_name = _other_owner_display_name(message)
        else:
            action_owner = "unclear"
    risk_score = 0
    risk_reasons = []
    trust_signals = []
    sender_domain = _domain_from_email(message.from_address)
    user_domain = _domain_from_email(message.user_id)
    if user_domain and sender_domain and sender_domain == user_domain:
        trust_signals.append("internal_sender")
    if len(ordered) > 1:
        trust_signals.append("thread_continuity")
    if target_in_to:
        trust_signals.append("direct_target")
    if any(phrase in normalized_text for phrase in SUSPICIOUS_URGENCY):
        risk_score += 1
        risk_reasons.append("urgency_cues")
    if any(phrase in normalized_text for phrase in SENSITIVE_REQUESTS):
        risk_score += 2
        risk_reasons.append("sensitive_request")
    if "http://" in normalized_text or "https://" in normalized_text:
        for token in normalized_text.split():
            if token.startswith("http://") or token.startswith("https://"):
                if sender_domain and sender_domain not in token:
                    risk_score += 1
                    risk_reasons.append("link_domain_mismatch")
                    break
    if message.has_attachments and ("password" in normalized_text or "invoice" in normalized_text):
        risk_score += 1
        risk_reasons.append("attachment_with_sensitive_request")
    if risk_score >= 3:
        risk_level = "high"
    elif risk_score >= 1:
        risk_level = "medium"
    else:
        risk_level = "low"
    return MailThreadDigestInput(
        thread_id=str(message.thread_id or message.graph_message_id),
        message_count=len(thread_messages),
        participants=tuple(participants[:4]),
        latest_sender_display_name=_humanize_identifier(message.from_address) or message.from_address,
        latest_is_unread=bool(message.is_unread),
        target_recipient_display_name=_target_recipient_display_name(message),
        source_language_hint=_language_hint_for_text("{0} {1}".format(message.subject or "", message.body_preview or "")),
        action_owner=action_owner,
        action_owner_display_name=action_owner_display_name,
        action_expected_from_user=action_expected_from_user,
        relevance_to_user=relevance_to_user,
        risk_level=risk_level,
        risk_reasons=tuple(risk_reasons),
        trust_signals=tuple(trust_signals),
        messages=tuple(rendered_messages),
    )


def build_agenda_digest_input(
    meeting: MeetingRecord,
    *,
    event_kind: str,
    recurrence_label: str,
    related_messages: Sequence[Mapping[str, str]],
    display_timezone: str,
) -> AgendaDigestInput:
    local_sort_date = meeting.start_at.astimezone(_display_zone(display_timezone)).date().isoformat()
    return AgendaDigestInput(
        event_kind=event_kind,
        recurrence_label=recurrence_label,
        related_messages=tuple(related_messages),
        local_sort_date=local_sort_date,
    )

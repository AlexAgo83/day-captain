"""Business logic services for Day Captain."""

from datetime import date
from datetime import datetime
from datetime import timedelta
from datetime import timezone
import re
from typing import Iterable
from typing import Mapping
from typing import Optional
from typing import Sequence
from urllib.parse import quote
from zoneinfo import ZoneInfo

from day_captain.models import DigestEntry
from day_captain.models import DigestOverview
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
    "your day captain brief",
    "votre brief day captain",
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

LANGUAGE_COPY = {
    "en": {
        "digest_title": "Your Day Captain brief",
        "subject": "Your Day Captain brief for {date}",
        "prepared": "As of {date}",
        "coverage_label": "Window",
        "coverage_separator": ": ",
        "coverage_value": "From {start} to {end}",
        "sections": {
            "critical_topics": "Critical topics",
            "actions_to_take": "Actions to take",
            "watch_items": "Watch items",
            "upcoming_meetings": "Upcoming meetings",
        },
        "empty": {
            "critical_topics": "Nothing urgent right now.",
            "actions_to_take": "No follow-up is waiting on you.",
            "watch_items": "Nothing else needs a flag right now.",
            "upcoming_meetings": "No meetings are lined up for {day}.",
        },
        "meeting_notes": {
            "weekend_monday": "Looking ahead to {day}.",
            "next_day": "Nothing else is scheduled for today, so here is {day}.",
        },
        "footer": {
            "label": "Quick actions",
            "hint": "Opens a Day Captain draft.",
            "recall": "Recall this brief",
            "recall_today": "Recall today",
            "recall_week": "Recall week",
        },
        "overview": {
            "label": "In brief",
            "clear": "Nothing urgent stands out right now.",
            "critical_one": "Top priority: {first}.",
            "critical_many": "Top priorities: {first}; {second}.",
            "action_one": "Main follow-up: {first}.",
            "action_many": "Main follow-ups: {first}; {second}.",
            "watch_one": "Worth keeping in view: {first}.",
            "watch_many": "Worth keeping in view: {first}; {second}.",
            "meeting": "Upcoming meeting: {text}.",
        },
        "summary": {
            "critical": "Needs attention: {text}",
            "action": "Likely needs your follow-up: {text}",
            "watch": "Worth noting: {text}",
            "file_shared": "Shared a file or document for your review.",
            "download_shared": "Shared a download link for the latest version.",
            "from_sender": "From {sender}",
            "meeting_today": "Today, {time} | {organizer}",
            "meeting_day": "{day}, {time} | {organizer}",
            "meeting_today_self": "Today, {time}",
            "meeting_day_self": "{day}, {time}",
            "meeting_location": " | {location}",
            "unknown_organizer": "an unknown organizer",
        },
    },
    "fr": {
        "digest_title": "Votre brief Day Captain",
        "subject": "Votre brief Day Captain du {date}",
        "prepared": "À jour au {date}",
        "coverage_label": "Périmètre",
        "coverage_separator": " : ",
        "coverage_value": "Du {start} au {end}",
        "sections": {
            "critical_topics": "Points critiques",
            "actions_to_take": "Actions à mener",
            "watch_items": "À surveiller",
            "upcoming_meetings": "Réunions à venir",
        },
        "empty": {
            "critical_topics": "Rien d'urgent pour l'instant.",
            "actions_to_take": "Aucun suivi immédiat.",
            "watch_items": "Rien d'autre à signaler.",
            "upcoming_meetings": "Aucune réunion n'est prévue pour {day}.",
        },
        "meeting_notes": {
            "weekend_monday": "Aperçu des réunions de {day}.",
            "next_day": "Rien d'autre n'est prévu aujourd'hui, voici {day}.",
        },
        "footer": {
            "label": "Actions rapides",
            "hint": "Ouvre un brouillon Day Captain.",
            "recall": "Rappeler ce brief",
            "recall_today": "Rappel aujourd'hui",
            "recall_week": "Rappel semaine",
        },
        "overview": {
            "label": "En bref",
            "clear": "Rien d'urgent ne remonte pour l'instant.",
            "critical_one": "Priorité du moment : {first}.",
            "critical_many": "Priorités du moment : {first} ; {second}.",
            "action_one": "Suivi principal : {first}.",
            "action_many": "Suivis principaux : {first} ; {second}.",
            "watch_one": "À garder en tête : {first}.",
            "watch_many": "À garder en tête : {first} ; {second}.",
            "meeting": "Réunion à venir : {text}.",
        },
        "summary": {
            "critical": "À surveiller de près : {text}",
            "action": "Demande probablement un suivi de votre part : {text}",
            "watch": "À garder en tête : {text}",
            "file_shared": "Un fichier ou document a été partagé pour consultation.",
            "download_shared": "Un lien de téléchargement a été partagé pour la dernière version.",
            "from_sender": "De la part de {sender}",
            "meeting_today": "Aujourd'hui, {time} | {organizer}",
            "meeting_day": "{day}, {time} | {organizer}",
            "meeting_today_self": "Aujourd'hui, {time}",
            "meeting_day_self": "{day}, {time}",
            "meeting_location": " | {location}",
            "unknown_organizer": "un organisateur inconnu",
        },
    },
}

WEEKDAY_NAMES = {
    "en": {
        "short": ("Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"),
        "long": ("Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"),
    },
    "fr": {
        "short": ("lun.", "mar.", "mer.", "jeu.", "ven.", "sam.", "dim."),
        "long": ("lundi", "mardi", "mercredi", "jeudi", "vendredi", "samedi", "dimanche"),
    },
}

MONTH_NAMES = {
    "en": {
        "short": ("Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"),
        "long": ("January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"),
    },
    "fr": {
        "short": ("janv.", "févr.", "mars", "avr.", "mai", "juin", "juil.", "août", "sept.", "oct.", "nov.", "déc."),
        "long": ("janvier", "février", "mars", "avril", "mai", "juin", "juillet", "août", "septembre", "octobre", "novembre", "décembre"),
    },
}


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


def _humanize_identifier(value: str) -> str:
    candidate = " ".join((value or "").strip().split())
    if not candidate:
        return ""
    if "@" not in candidate:
        return candidate
    local_part = candidate.split("@", 1)[0].strip()
    local_part = re.sub(r"[._-]+", " ", local_part)
    local_part = re.sub(r"\b(ext|external|intern|interne)\b", "", local_part, flags=re.IGNORECASE)
    local_part = re.sub(r"\s+", " ", local_part).strip()
    if not local_part:
        return candidate
    words = []
    for raw_word in local_part.split():
        lower = raw_word.lower()
        if lower in {"ceo", "cto", "cfo", "coo", "hr", "it", "ops"}:
            words.append(lower.upper())
            continue
        words.append(lower.capitalize())
    rendered = " ".join(words).strip()
    return rendered or candidate


def _normalize_display_title(value: str) -> str:
    candidate = " ".join((value or "").strip().split())
    if not candidate:
        return ""
    lowered = candidate.lower()
    if lowered == "a imprimer":
        return "À imprimer"
    candidate = re.sub(r"(?<=\w)-\s+(?=\w)", " ", candidate)
    candidate = re.sub(r"\s+", " ", candidate).strip()
    return candidate


def _identity_tokens(value: str) -> Sequence[str]:
    candidate = str(value or "").strip().lower()
    if not candidate:
        return ()
    tokens = {candidate}
    if "@" in candidate:
        local_part = candidate.split("@", 1)[0].strip()
        if local_part:
            tokens.add(local_part)
    humanized = _humanize_identifier(candidate).lower()
    if humanized:
        tokens.add(re.sub(r"[^a-z0-9]+", " ", humanized).strip())
    normalized = re.sub(r"[^a-z0-9]+", " ", candidate).strip()
    if normalized:
        tokens.add(normalized)
    return tuple(token for token in tokens if token)


def _same_identity(left: str, right: str) -> bool:
    left_tokens = set(_identity_tokens(left))
    right_tokens = set(_identity_tokens(right))
    if not left_tokens or not right_tokens:
        return False
    return not left_tokens.isdisjoint(right_tokens)


def _first_non_self_attendee(meeting: MeetingRecord) -> str:
    for attendee in meeting.attendees:
        if not _same_identity(attendee, meeting.user_id):
            return _humanize_identifier(attendee)
    return ""


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


def _normalize_language(value: str) -> str:
    candidate = (value or "").strip().lower()
    if candidate in LANGUAGE_COPY:
        return candidate
    return "en"


def _language_copy(language: str) -> Mapping[str, object]:
    return LANGUAGE_COPY[_normalize_language(language)]


def _clean_overview_fragment(value: str) -> str:
    cleaned = " ".join((value or "").strip().split())
    return cleaned.rstrip(" .!?:;,\n\t") or cleaned


def _truncate_sentence(value: str, max_chars: int = 220) -> str:
    cleaned = " ".join((value or "").strip().split())
    if len(cleaned) <= max_chars:
        return cleaned
    truncated = cleaned[:max_chars].rstrip()
    if " " in truncated:
        truncated = truncated.rsplit(" ", 1)[0].rstrip()
    return truncated.rstrip(" .!?:;,\n\t") + "..."


def _polish_top_summary_phrase(value: str) -> str:
    cleaned = " ".join((value or "").strip().split())
    cleaned = re.sub(r"\bla prochaine a lieu\b", "la plus proche est", cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r"\bthe next one is\b", "the nearest one is", cleaned, flags=re.IGNORECASE)
    return cleaned


def _normalize_top_summary(value: str, max_sentences: int = 2, max_chars: int = 220) -> str:
    cleaned = " ".join((value or "").strip().split())
    if not cleaned:
        return ""
    if max_sentences > 0:
        sentence_candidates = re.split(r"(?<=[.!?])\s+", cleaned)
        selected = [sentence.strip() for sentence in sentence_candidates if sentence.strip()][:max_sentences]
        if selected:
            cleaned = " ".join(selected).strip()
    cleaned = _polish_top_summary_phrase(cleaned)
    return _truncate_sentence(cleaned, max_chars=max_chars)


def _strip_redundant_title_prefix(title: str, summary: str) -> str:
    cleaned = " ".join((summary or "").strip().split())
    if not cleaned:
        return ""
    normalized_title = " ".join((title or "").strip().split())
    prefixes = []
    if normalized_title:
        prefixes.append(normalized_title)
    for separator in (" - ", " — ", ": "):
        if separator in normalized_title:
            prefixes.append(normalized_title.split(separator, 1)[0].strip())
    for prefix in prefixes:
        if not prefix:
            continue
        cleaned = re.sub(
            r"^{0}\s*[:\-—]\s*".format(re.escape(prefix)),
            "",
            cleaned,
            count=1,
            flags=re.IGNORECASE,
        ).strip()
    return cleaned


def _normalize_item_summary(title: str, summary: str, max_chars: int = 220) -> str:
    cleaned = _strip_redundant_title_prefix(title, summary)
    cleaned = re.sub(r"\baction attendue\s*:", "Suivi :", cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r"\bexpected action\s*:", "Next step:", cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r"\s*[—-]\s*(Suivi:|Next step:)", r" \1", cleaned, flags=re.IGNORECASE)
    cleaned = " ".join(cleaned.split())
    candidate_compact = _compact_candidate_profile_summary(title, cleaned)
    if candidate_compact:
        cleaned = candidate_compact
    for marker in ("Suivi :", "Next step:"):
        if marker in cleaned and len(cleaned) > max_chars:
            prefix, suffix = cleaned.split(marker, 1)
            suffix = suffix.strip()
            suffix_text = "{0} {1}".format(marker, suffix).strip()
            reserved = min(max(40, len(suffix_text) + 1), max_chars - 20)
            prefix_limit = max(20, max_chars - reserved)
            prefix_text = _truncate_sentence(prefix.strip(), max_chars=prefix_limit).rstrip(".")
            return "{0} {1}".format(prefix_text, suffix_text).strip()
    return _truncate_sentence(cleaned, max_chars=max_chars)


def _item_summary_limit(item: DigestEntry) -> int:
    if item.source_kind == "meeting":
        return 110
    if item.section_name == "critical_topics":
        return 160
    if item.section_name == "actions_to_take":
        return 170
    if item.section_name == "watch_items":
        return 180
    return 200


def _compact_candidate_profile_summary(title: str, summary: str) -> str:
    normalized = _normalize_text(title, summary)
    candidate_markers = ("candidature", "candidate", "designer", "opportunit", "opportunity", "bachelor", "master")
    if not any(marker in normalized for marker in candidate_markers):
        return ""
    follow_up = ""
    for marker in ("Suivi :", "Next step:"):
        if marker in summary:
            follow_up = marker + " " + summary.split(marker, 1)[1].strip()
            break
    company_match = re.search(r"\bchez\s+([A-Z][A-Za-z0-9&' -]+)", summary)
    if not company_match:
        company_match = re.search(r"\bat\s+([A-Z][A-Za-z0-9&' -]+)", summary)
    company = company_match.group(1).strip() if company_match else ""
    if company:
        company = re.split(r"\b(depuis|for)\b|,", company, maxsplit=1)[0].strip()
    role = ""
    title_lower = title.lower()
    if "designer" in title_lower:
        role = "Profil designer"
    elif "design" in normalized:
        role = "Profil design"
    elif "candidate" in normalized or "candidature" in normalized:
        role = "Profil candidat"
    if company:
        base = "{0} chez {1}.".format(role or "Profil", company).strip()
    else:
        base = "{0} à examiner.".format(role or _normalize_display_title(title) or "Profil").strip()
    if follow_up:
        return "{0} {1}".format(base, follow_up).strip()
    return base


def _normalized_place(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", (value or "").strip().lower()).strip()


def _display_zone(name: str):
    try:
        return ZoneInfo(name)
    except Exception:
        return timezone.utc


def _local_date(value: datetime, display_timezone: str) -> date:
    return value.astimezone(_display_zone(display_timezone)).date()


def _weekday_name(target_day: date, language: str, short: bool = False) -> str:
    key = "short" if short else "long"
    return WEEKDAY_NAMES[_normalize_language(language)][key][target_day.weekday()]


def _month_name(target_day: date, language: str, short: bool = False) -> str:
    key = "short" if short else "long"
    return MONTH_NAMES[_normalize_language(language)][key][target_day.month - 1]


def _format_day_label(target_day: date, language: str, short: bool = False, include_year: bool = False) -> str:
    weekday = _weekday_name(target_day, language, short=short)
    month = _month_name(target_day, language, short=short)
    if _normalize_language(language) == "fr":
        base = "{0} {1:02d} {2}".format(weekday, target_day.day, month)
    else:
        base = "{0} {1:02d} {2}".format(weekday, target_day.day, month)
    if include_year:
        base += " {0}".format(target_day.year)
    return base


def _format_localized_timestamp(
    value: datetime,
    display_timezone: str,
    language: str,
    include_zone: bool = True,
) -> str:
    target = value.astimezone(_display_zone(display_timezone))
    day_label = _format_day_label(target.date(), language, short=True, include_year=True)
    if _normalize_language(language) == "fr":
        rendered = "{0} à {1}".format(day_label, target.strftime("%H:%M"))
    else:
        rendered = "{0} at {1}".format(day_label, target.strftime("%H:%M"))
    if include_zone:
        rendered += " {0}".format(target.tzname() or display_timezone)
    return rendered


def _meeting_day_reference(target_day: date, source_day: date, language: str) -> str:
    normalized = _normalize_language(language)
    if target_day == source_day:
        return "today" if normalized == "en" else "aujourd'hui"
    if target_day == source_day + timedelta(days=1):
        return "tomorrow" if normalized == "en" else "demain"
    return _weekday_name(target_day, normalized, short=False)


class DeterministicScoringEngine:
    def __init__(self, digest_language: str = "en", display_timezone: str = "UTC") -> None:
        self.digest_language = _normalize_language(digest_language)
        self.display_timezone = display_timezone

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
        subject = _normalize_display_title(message.subject or "(no subject)")
        cleaned_preview = _clean_preview(message.body_preview)
        combined_text = _normalize_text(message.subject, message.body_preview)
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
        copy = _language_copy(self.digest_language)["summary"]
        local_start = meeting.start_at.astimezone(_display_zone(self.display_timezone))
        local_now = now.astimezone(_display_zone(self.display_timezone))
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
        organizer = _humanize_identifier(meeting.organizer_address) or copy["unknown_organizer"]
        organizer_is_target_user = _same_identity(meeting.organizer_address, meeting.user_id)
        fallback_person = _first_non_self_attendee(meeting) if organizer_is_target_user else ""
        displayed_person = fallback_person or organizer
        if local_start.date() == local_now.date():
            if organizer_is_target_user and not fallback_person:
                summary = copy["meeting_today_self"].format(time=local_start.strftime("%H:%M"))
            else:
                summary = copy["meeting_today"].format(
                    time=local_start.strftime("%H:%M"),
                    organizer=displayed_person,
                )
        else:
            day_label = _meeting_day_reference(local_start.date(), local_now.date(), self.digest_language)
            if day_label:
                day_label = day_label[:1].upper() + day_label[1:]
            if organizer_is_target_user and not fallback_person:
                summary = copy["meeting_day_self"].format(
                    day=day_label,
                    time=local_start.strftime("%H:%M"),
                )
            else:
                summary = copy["meeting_day"].format(
                    day=day_label,
                    time=local_start.strftime("%H:%M"),
                    organizer=displayed_person,
                )
        if meeting.location and _normalized_place(meeting.location) != _normalized_place(meeting.subject):
            summary += copy["meeting_location"].format(location=meeting.location)
        return DigestEntry(
            title=_normalize_display_title(meeting.subject or "(untitled meeting)"),
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
        copy = _language_copy(self.digest_language)["summary"]
        preview = cleaned_preview or (message.body_preview or "").strip()
        normalized_preview = _normalize_text(preview)
        base = preview if preview else copy["from_sender"].format(sender=message.from_address)
        if "deliverable_shared" in reason_codes:
            if "download" in normalized_preview or "telechargement" in normalized_preview or "téléchargement" in normalized_preview:
                return copy["download_shared"]
            return copy["file_shared"]
        if "critical_keyword" in reason_codes:
            return copy["critical"].format(text=base)
        if "action_keyword" in reason_codes:
            return copy["action"].format(text=base)
        return copy["watch"].format(text=base)


class StructuredDigestRenderer:
    def __init__(self, display_timezone: str = "UTC", digest_language: str = "en") -> None:
        self.display_timezone = display_timezone
        self.digest_language = _normalize_language(digest_language)

    def render(
        self,
        run_id: str,
        generated_at: datetime,
        window_start: datetime,
        window_end: datetime,
        delivery_mode: str,
        prioritized_items: Sequence[DigestEntry],
        tenant_id: str = "",
        user_id: str = "",
        command_mailbox: str = "",
        top_summary: str = "",
        top_summary_source: str = "none",
        meeting_horizon: Optional[Mapping[str, str]] = None,
    ) -> DigestPayload:
        sections = {name: [] for name in SECTION_NAMES}
        for item in prioritized_items:
            target_section = item.section_name if item.section_name in sections else "watch_items"
            sections[target_section].append(item)
        for name in SECTION_NAMES:
            sections[name] = sorted(sections[name], key=lambda item: (-item.score, item.title.lower()))[:5]

        localized = _language_copy(self.digest_language)
        normalized_top_summary = _normalize_top_summary(top_summary)
        delivery_subject = localized["subject"].format(
            date=_format_day_label(
                _local_date(generated_at, self.display_timezone),
                self.digest_language,
                short=True,
                include_year=False,
            )
        )
        delivery_body = self._build_delivery_body(
            generated_at,
            window_start,
            window_end,
            sections,
            normalized_top_summary,
            command_mailbox,
            meeting_horizon or {},
        )
        delivery_html = self._build_delivery_html(
            generated_at,
            window_start,
            window_end,
            sections,
            normalized_top_summary,
            command_mailbox,
            meeting_horizon or {},
        )
        delivery_payload = {
            "mode": delivery_mode,
            "run_id": run_id,
            "tenant_id": tenant_id,
            "user_id": user_id,
            "subject": delivery_subject,
            "body": delivery_body,
            "html_body": delivery_html,
            "top_summary": normalized_top_summary,
            "top_summary_source": top_summary_source,
            "command_mailbox": command_mailbox,
            "meeting_horizon": dict(meeting_horizon or {}),
            "digest_language": self.digest_language,
            "sections": {
                name: [self._entry_payload(item) for item in sections[name]]
                for name in SECTION_NAMES
            },
        }
        if delivery_mode == "graph_send":
            graph_message = {
                "subject": delivery_subject,
                "body": {
                    "contentType": "HTML",
                    "content": delivery_html,
                },
            }
            if "@" in str(user_id or ""):
                graph_message["toRecipients"] = [
                    {
                        "emailAddress": {
                            "address": str(user_id),
                        }
                    }
                ]
            delivery_payload["graph_message"] = graph_message

        return DigestPayload(
            run_id=run_id,
            generated_at=generated_at,
            window_start=window_start,
            window_end=window_end,
            delivery_mode=delivery_mode,
            tenant_id=tenant_id,
            user_id=user_id,
            delivery_subject=delivery_subject,
            delivery_body=delivery_body,
            top_summary=normalized_top_summary,
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
        top_summary: str,
        command_mailbox: str,
        meeting_horizon: Mapping[str, str],
    ) -> str:
        localized = _language_copy(self.digest_language)
        generated_label = _format_localized_timestamp(generated_at, self.display_timezone, self.digest_language)
        coverage_text = localized["coverage_value"].format(
            start=_format_localized_timestamp(window_start, self.display_timezone, self.digest_language, include_zone=False),
            end=_format_localized_timestamp(window_end, self.display_timezone, self.digest_language),
        )
        lines = [
            localized["digest_title"],
            localized["prepared"].format(date=generated_label),
            "{0}{1}{2}".format(
                localized["coverage_label"],
                localized.get("coverage_separator", ": "),
                coverage_text,
            ),
            "",
        ]
        if top_summary.strip():
            lines.append(localized["overview"]["label"])
            lines.append(top_summary.strip())
            lines.append("")
        labels = localized["sections"]
        for name in SECTION_NAMES:
            lines.append(labels[name])
            meeting_note = self._meeting_note(name, meeting_horizon)
            if meeting_note:
                lines.append(meeting_note)
            items = sections[name]
            if not items:
                lines.append(self._empty_state(name, meeting_horizon))
            else:
                for item in items:
                    lines.extend(self._body_item_lines(item))
            lines.append("")
        footer_lines = self._footer_body_lines(command_mailbox)
        if footer_lines:
            lines.extend(footer_lines)
            lines.append("")
        return "\n".join(lines).strip()

    def _build_delivery_html(
        self,
        generated_at: datetime,
        window_start: datetime,
        window_end: datetime,
        sections: Mapping[str, Sequence[DigestEntry]],
        top_summary: str,
        command_mailbox: str,
        meeting_horizon: Mapping[str, str],
    ) -> str:
        localized = _language_copy(self.digest_language)
        generated_label = _format_localized_timestamp(generated_at, self.display_timezone, self.digest_language)
        coverage_text = localized["coverage_value"].format(
            start=_format_localized_timestamp(window_start, self.display_timezone, self.digest_language, include_zone=False),
            end=_format_localized_timestamp(window_end, self.display_timezone, self.digest_language),
        )
        coverage_label = str(localized.get("coverage_label") or "")
        parts = [
            "<html><body style=\"margin:0;padding:0;background:transparent;font-family:Segoe UI,Helvetica,Arial,sans-serif;color:#1f2937;line-height:1.5;\">",
            "<div style=\"max-width:720px;margin:0 auto;padding:18px 18px 28px;\">",
            "<section style=\"margin:0 0 22px;padding:0 0 14px;border-bottom:1px solid #dbe4ee;\">",
            "<h1 style=\"margin:0 0 8px;font-size:28px;color:#0f172a;\">{0}</h1>".format(self._html_escape(localized["digest_title"])),
            "<p style=\"margin:0 0 8px;font-size:14px;color:#475569;\">{0}</p>".format(self._html_escape(localized["prepared"].format(date=generated_label))),
            "<table role=\"presentation\" style=\"margin:0;border-collapse:collapse;\"><tr>"
            "<td style=\"padding:0 10px 0 0;vertical-align:top;\">"
            "<span style=\"display:inline-block;padding:4px 8px;border:1px solid #dbe4ee;border-radius:999px;font-size:11px;font-weight:700;letter-spacing:0.08em;text-transform:uppercase;color:#64748b;\">{0}</span>"
            "</td>"
            "<td style=\"padding:2px 0 0;vertical-align:top;font-size:13px;color:#475569;\">{1}</td>"
            "</tr></table>".format(
                self._html_escape(coverage_label),
                self._html_escape(coverage_text),
            ),
            "</section>",
        ]
        if top_summary.strip():
            parts.append(
                "<section style=\"margin:10px 0 24px;padding:0 0 0 14px;border-left:3px solid #94a3b8;\">"
            )
            parts.append(
                "<p style=\"margin:0 0 6px;font-size:12px;font-weight:700;letter-spacing:0.08em;text-transform:uppercase;color:#64748b;\">{0}</p>".format(
                    self._html_escape(localized["overview"]["label"])
                )
            )
            parts.append(
                "<p style=\"margin:0 0 2px;font-size:17px;color:#0f172a;\">{0}</p></section>".format(
                    self._html_escape(top_summary.strip())
                )
            )
        labels = localized["sections"]
        for name in SECTION_NAMES:
            parts.append(
                "<section style=\"margin:0 0 16px;\"><h2 style=\"margin:0 0 8px;font-size:19px;color:#0f172a;\">{0}</h2>".format(
                    self._html_escape(labels[name])
                )
            )
            meeting_note = self._meeting_note(name, meeting_horizon)
            if meeting_note:
                parts.append("<p style=\"margin:0 0 8px;font-size:13px;color:#64748b;\">{0}</p>".format(self._html_escape(meeting_note)))
            items = sections[name]
            if not items:
                parts.append(
                    "<div style=\"margin:0;padding:10px 12px;border:1px dashed #cbd5e1;border-radius:10px;color:#64748b;\">{0}</div>".format(
                        self._html_escape(self._empty_state(name, meeting_horizon))
                    )
                )
            else:
                for item in items:
                    parts.append(self._html_item(item))
            parts.append("</section>")
        footer_html = self._footer_html(command_mailbox)
        if footer_html:
            parts.append(footer_html)
        parts.append("</div></body></html>")
        return "".join(parts)

    def _body_item_lines(self, item: DigestEntry) -> Sequence[str]:
        if item.source_kind == "meeting":
            return ("- {0} - {1}".format(item.title, item.summary),)
        return (
            "- {0}".format(item.title),
            "  {0}".format(item.summary),
        )

    def _html_item(self, item: DigestEntry) -> str:
        if item.source_kind == "meeting":
            return (
                "<div style=\"margin:0 0 8px;padding:10px 12px;border:1px solid #cbd5e1;border-radius:10px;\">"
                "<p style=\"margin:0;font-size:15px;font-weight:600;color:#0f172a;\">{0}</p>"
                "<p style=\"margin:4px 0 0;font-size:13px;color:#475569;\">{1}</p>"
                "</div>"
            ).format(
                self._html_escape(item.title),
                self._html_escape(item.summary),
            )
        return (
            "<div style=\"margin:0 0 10px;padding:12px 14px;border:1px solid #cbd5e1;border-radius:12px;\">"
            "<p style=\"margin:0 0 4px;font-size:15px;font-weight:600;color:#0f172a;\">{0}</p>"
            "<p style=\"margin:0;font-size:14px;color:#334155;\">{1}</p>"
            "</div>"
        ).format(
            self._html_escape(item.title),
            self._html_escape(item.summary),
        )

    def _footer_body_lines(self, command_mailbox: str) -> Sequence[str]:
        mailbox = str(command_mailbox or "").strip()
        if "@" not in mailbox:
            return ()
        footer = _language_copy(self.digest_language)["footer"]
        return (
            str(footer["label"]),
            str(footer["hint"]),
            "- {0}: {1} (subject/body: recall)".format(footer["recall"], mailbox),
            "- {0}: {1} (subject/body: recall-today)".format(footer["recall_today"], mailbox),
            "- {0}: {1} (subject/body: recall-week)".format(footer["recall_week"], mailbox),
        )

    def _footer_html(self, command_mailbox: str) -> str:
        mailbox = str(command_mailbox or "").strip()
        if "@" not in mailbox:
            return ""
        footer = _language_copy(self.digest_language)["footer"]
        links = (
            ("recall", str(footer["recall"])),
            ("recall-today", str(footer["recall_today"])),
            ("recall-week", str(footer["recall_week"])),
        )
        parts = [
            "<section style=\"margin:10px 0 0;padding-top:14px;border-top:1px solid #dbe4ee;\">",
            "<p style=\"margin:0 0 8px;font-size:12px;font-weight:700;letter-spacing:0.08em;text-transform:uppercase;color:#64748b;\">{0}</p>".format(
                self._html_escape(str(footer["label"]))
            ),
            "<p style=\"margin:0 0 10px;font-size:13px;color:#64748b;\">{0}</p>".format(
                self._html_escape(str(footer["hint"]))
            ),
            "<table role=\"presentation\" style=\"margin:0;border-collapse:separate;border-spacing:0 8px;\"><tr>",
        ]
        for command, label in links:
            href = "mailto:{0}?subject={1}&body={2}".format(mailbox, quote(command), quote(command))
            parts.append(
                "<td style=\"padding:0 8px 0 0;\">"
                "<a href=\"{0}\" style=\"display:inline-block;padding:8px 12px;border:1px solid #cbd5e1;border-radius:999px;color:#0f172a;text-decoration:none;font-size:13px;white-space:nowrap;\">{1}</a>"
                "</td>".format(self._html_escape(href), self._html_escape(label))
            )
        parts.append("</tr></table></section>")
        return "".join(parts)

    def _meeting_note(self, section_name: str, meeting_horizon: Mapping[str, str]) -> str:
        if section_name != "upcoming_meetings":
            return ""
        mode = str(meeting_horizon.get("mode") or "same_day")
        if mode not in {"weekend_monday", "next_day"}:
            return ""
        localized = _language_copy(self.digest_language)
        target_day = self._meeting_target_day(meeting_horizon)
        if target_day is None:
            return ""
        return localized["meeting_notes"][mode].format(
            day=self._meeting_horizon_day_label(mode, target_day, self._meeting_source_day(meeting_horizon) or target_day)
        )

    def _empty_state(self, section_name: str, meeting_horizon: Mapping[str, str]) -> str:
        localized = _language_copy(self.digest_language)
        if section_name != "upcoming_meetings":
            return localized["empty"][section_name]
        target_day = self._meeting_target_day(meeting_horizon)
        source_day = self._meeting_source_day(meeting_horizon)
        if target_day is None:
            target_day = datetime.now(_display_zone(self.display_timezone)).date()
        if source_day is None:
            source_day = target_day
        return localized["empty"]["upcoming_meetings"].format(
            day=self._meeting_horizon_day_label(str(meeting_horizon.get("mode") or "same_day"), target_day, source_day)
        )

    def _meeting_target_day(self, meeting_horizon: Mapping[str, str]) -> Optional[date]:
        raw = str(meeting_horizon.get("target_date") or "").strip()
        if not raw:
            return None
        return date.fromisoformat(raw)

    def _meeting_source_day(self, meeting_horizon: Mapping[str, str]) -> Optional[date]:
        raw = str(meeting_horizon.get("source_date") or "").strip()
        if not raw:
            return None
        return date.fromisoformat(raw)

    def _meeting_horizon_day_label(self, mode: str, target_day: date, source_day: date) -> str:
        if mode == "weekend_monday":
            return _weekday_name(target_day, self.digest_language, short=False)
        return _meeting_day_reference(target_day, source_day, self.digest_language)

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


class DeterministicDigestOverviewEngine:
    def summarize(
        self,
        payload: DigestPayload,
    ) -> DigestOverview:
        language = _normalize_language(str(payload.delivery_payload.get("digest_language") or "en"))
        localized = _language_copy(language)["overview"]
        sections = {
            "critical_topics": tuple(payload.critical_topics),
            "actions_to_take": tuple(payload.actions_to_take),
            "watch_items": tuple(payload.watch_items),
            "upcoming_meetings": tuple(payload.upcoming_meetings),
        }
        sentences = []
        for section_name in ("critical_topics", "actions_to_take", "watch_items"):
            items = sections[section_name]
            if not items:
                continue
            sentences.append(self._section_sentence(section_name, items, localized))
            if len(sentences) >= 2:
                break
        meetings = sections["upcoming_meetings"]
        if meetings and len(sentences) < 2:
            meeting_text = _normalize_item_summary(meetings[0].title, meetings[0].summary, max_chars=110)
            sentences.append(localized["meeting"].format(text=_clean_overview_fragment(meeting_text)))
        if not sentences:
            sentences.append(localized["clear"])
        return DigestOverview(
            summary=" ".join(sentence.strip() for sentence in sentences if sentence.strip()),
            source="deterministic",
        )

    def _section_sentence(
        self,
        section_name: str,
        items: Sequence[DigestEntry],
        localized: Mapping[str, str],
    ) -> str:
        first = _clean_overview_fragment(items[0].title)
        second = _clean_overview_fragment(items[1].title) if len(items) > 1 else ""
        if section_name == "critical_topics":
            key = "critical_many" if second else "critical_one"
        elif section_name == "actions_to_take":
            key = "action_many" if second else "action_one"
        else:
            key = "watch_many" if second else "watch_one"
        return localized[key].format(first=first, second=second)


class LlmDigestOverviewEngine:
    def __init__(self, provider, fallback_engine: Optional[DeterministicDigestOverviewEngine] = None) -> None:
        self.provider = provider
        self.fallback_engine = fallback_engine or DeterministicDigestOverviewEngine()

    def summarize(
        self,
        payload: DigestPayload,
    ) -> DigestOverview:
        language = _normalize_language(str(payload.delivery_payload.get("digest_language") or "en"))
        labels = _language_copy(language)["sections"]
        sections = self._overview_sections(payload)
        if not any(sections[name] for name in SECTION_NAMES):
            return self.fallback_engine.summarize(payload)
        try:
            summary = self.provider.summarize_digest(
                sections=sections,
                labels=labels,
                meeting_note=self._overview_meeting_note(payload, language),
            )
        except Exception:
            return self.fallback_engine.summarize(payload)
        summary = str(summary or "").strip()
        if not summary:
            return self.fallback_engine.summarize(payload)
        return DigestOverview(summary=_normalize_top_summary(summary, max_chars=200), source="llm")

    def _overview_sections(self, payload: DigestPayload) -> Mapping[str, Sequence[DigestEntry]]:
        return {
            "critical_topics": self._compact_overview_items(tuple(payload.critical_topics[:1])),
            "actions_to_take": self._compact_overview_items(tuple(payload.actions_to_take[:1])),
            "watch_items": self._compact_overview_items(tuple(payload.watch_items[:1])),
            "upcoming_meetings": self._compact_overview_items(tuple(payload.upcoming_meetings[:1])),
        }

    def _compact_overview_items(self, items: Sequence[DigestEntry]) -> Sequence[DigestEntry]:
        compacted = []
        for item in items:
            compacted.append(
                DigestEntry(
                    title=item.title,
                    summary=_normalize_item_summary(item.title, item.summary, max_chars=self._overview_summary_limit(item)),
                    section_name=item.section_name,
                    source_kind=item.source_kind,
                    source_id=item.source_id,
                    score=item.score,
                    reason_codes=item.reason_codes,
                    guardrail_applied=item.guardrail_applied,
                )
            )
        return tuple(compacted)

    def _overview_summary_limit(self, item: DigestEntry) -> int:
        if item.source_kind == "meeting":
            return 90
        if item.section_name == "critical_topics":
            return 110
        if item.section_name == "actions_to_take":
            return 120
        if item.section_name == "watch_items":
            return 120
        return 120

    def _overview_meeting_note(self, payload: DigestPayload, language: str) -> str:
        meetings = tuple(payload.upcoming_meetings)
        if len(meetings) <= 1:
            return ""
        if language == "fr":
            return (
                "{0} réunions sont prévues. Résume-les brièvement sans toutes les lister. "
                "Si elles sont demain ou lundi, dis-le ainsi plutôt que 'la semaine prochaine'. "
                "Si tu mentionnes une réunion, cite la plus proche avec un horaire concret et évite les formulations vagues."
            ).format(len(meetings))
        return (
            "{0} meetings are scheduled. Summarize them briefly without listing them all. "
            "If they are tomorrow or Monday, say that instead of 'next week'. "
            "If you mention a meeting, cite the nearest one with a concrete time and avoid vague phrasing."
        ).format(len(meetings))


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
            summary = _normalize_item_summary(item.title, summary, max_chars=_item_summary_limit(item))
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
            tenant_id=payload.tenant_id,
            user_id=payload.user_id,
            command_mailbox=str(payload.delivery_payload.get("command_mailbox") or ""),
            top_summary=payload.top_summary,
            top_summary_source=str(payload.delivery_payload.get("top_summary_source") or "none"),
        )


class PreferenceFeedbackProcessor:
    def process_feedback(self, storage: Storage, feedback: FeedbackRecord) -> None:
        storage.save_feedback(feedback, tenant_id=feedback.tenant_id, user_id=feedback.user_id)
        if feedback.source_kind != "message":
            return
        message = storage.get_message(feedback.source_id, tenant_id=feedback.tenant_id, user_id=feedback.user_id)
        if message is None:
            return
        delta = self._feedback_delta(feedback)
        if delta == 0.0:
            return

        existing = {
            pref.preference_key: pref
            for pref in storage.load_preferences(tenant_id=feedback.tenant_id, user_id=feedback.user_id)
        }
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

        storage.upsert_preferences(tuple(updates), tenant_id=feedback.tenant_id, user_id=feedback.user_id)

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

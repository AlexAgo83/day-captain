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
from day_captain.models import DigestCard
from day_captain.models import DigestOverview
from day_captain.models import DigestPayload
from day_captain.models import DigestRunRecord
from day_captain.models import ExternalNewsItem
from day_captain.models import FeedbackRecord
from day_captain.models import MeetingRecord
from day_captain.models import MessageRecord
from day_captain.models import UserPreference
from day_captain.models import WeatherSnapshot
from day_captain.models import parse_datetime
from day_captain.digest_parsing import build_agenda_digest_input
from day_captain.digest_parsing import build_mail_thread_digest_input
from day_captain.ports import Storage


SECTION_NAMES = (
    "critical_topics",
    "actions_to_take",
    "watch_items",
    "daily_presence",
    "upcoming_meetings",
)

PROJECT_REPOSITORY_URL = "https://github.com/AlexAgo83/day-captain"

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

PROMOTIONAL_ACTION_PATTERNS = (
    "book now",
    "buy now",
    "shop now",
    "reserve now",
    "reservez des maintenant",
    "réservez dès maintenant",
    "discover the offer",
    "decouvrez l offre",
    "découvrez l'offre",
)

PROMOTIONAL_OFFER_PATTERNS = (
    "ticket",
    "tickets",
    "billet",
    "billets",
    "promotion",
    "promo",
    "special offer",
    "offre speciale",
    "offre spéciale",
    "discount",
    "sale",
    "soldes",
    "version en ligne",
    "available online",
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

LOW_SIGNAL_WATCH_PATTERNS = (
    "how to ",
    "guide to ",
    "practical look at",
    "best practices",
    "playbook",
    "whitepaper",
    "ebook",
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

ENGLISH_LANGUAGE_HINTS = (
    "account",
    "approve",
    "attached",
    "before",
    "feedback",
    "input",
    "invoice",
    "join",
    "keep",
    "milestones",
    "need",
    "noon",
    "please",
    "review",
    "same",
    "thanks",
    "update",
)

FRENCH_LANGUAGE_HINTS = (
    "aujourd",
    "besoin",
    "bonjour",
    "candidature",
    "demain",
    "disponible",
    "jointe",
    "merci",
    "pièce",
    "piece",
    "réunion",
    "reunion",
    "retour",
    "suivi",
    "votre",
    "vous",
)

SECTION_PRIORITY = {
    "critical_topics": 3,
    "actions_to_take": 2,
    "watch_items": 1,
    "daily_presence": 1,
}

THREAD_CONTEXT_MESSAGE_LIMIT = 12
THREAD_CONTEXT_PREVIEW_LIMIT = 180
MEETING_CONTEXT_MESSAGE_LIMIT = 3
LOW_CONFIDENCE_THRESHOLD = 60
HIGH_CONFIDENCE_THRESHOLD = 80

PRESENCE_PATTERNS = (
    "bureau",
    "office",
    "onsite",
    "on site",
    "sur site",
    "teletravail",
    "télétravail",
    "remote",
    "wfh",
    "home office",
    "home-office",
)

TRIVIAL_PREVIEW_LINES = (
    "sent from outlook for mac",
    "sent from outlook for ios",
    "envoye a partir de outlook pour ios",
    "envoye a partir de outlook pour mac",
    "envoyé à partir de outlook pour ios",
    "envoyé à partir de outlook pour mac",
)

SUBJECT_PREFIX_PATTERN = re.compile(r"^\s*((re|fw|fwd|tr)\s*:\s*)+", flags=re.IGNORECASE)
SUBJECT_TAG_PREFIX_PATTERN = re.compile(
    r"^\s*\[((request\s+received)|(external)|(ext)|(ticket[^\]]*)|(notification)|(action\s+required))\]\s*",
    flags=re.IGNORECASE,
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
        "weather": {
            "label": "Today's weather",
            "warmer": "Warmer than yesterday.",
            "cooler": "Cooler than yesterday.",
            "same": "Close to yesterday.",
            "dry_day": "Dry day.",
            "rain_risk": "Rain risk.",
            "showers_likely": "Showers likely.",
            "rain_likely": "Rain likely.",
            "storm_risk": "Storm risk.",
            "snow_likely": "Snow likely.",
        },
        "external_news": {
            "label": "External news",
            "source_prefix": "Source",
            "link_label": "Open article",
        },
        "sections": {
            "critical_topics": "Critical topics",
            "actions_to_take": "Actions to take",
            "watch_items": "Watch items",
            "daily_presence": "Daily presence",
            "upcoming_meetings": "Upcoming meetings",
        },
        "empty": {
            "critical_topics": "Nothing urgent right now.",
            "actions_to_take": "No follow-up is waiting on you.",
            "watch_items": "Nothing else needs a flag right now.",
            "daily_presence": "No all-day presence signal is set for {day}.",
            "upcoming_meetings": "No meetings are lined up for {day}.",
        },
        "meeting_notes": {
            "weekend_monday": "Looking ahead to {day}.",
            "next_day": "Nothing else is scheduled for today, so here is {day}.",
            "two_day_span": "Light meeting day, so this section also includes {day}.",
            "next_two_days": "Nothing else is scheduled for today, so here are {first_day} and {second_day}.",
        },
        "footer": {
            "label": "Quick actions",
            "hint": "Use these buttons to ask Day Captain for this brief again, today's brief, or this week's brief.",
            "recall": "Recall this brief",
            "recall_today": "Recall today",
            "recall_week": "Recall week",
            "copyright": "Day Captain © {year}",
        },
        "item_actions": {
            "open_mail": "Open in Outlook",
            "open_meeting": "Open meeting",
            "open_mail_desktop": "Open in Outlook desktop",
            "open_meeting_desktop": "Open meeting in Outlook desktop",
        },
        "badges": {
            "unread": "Unread",
            "flagged": "Flagged",
            "promotional": "Promo",
            "verify": "Verify",
            "suspicious": "Suspicious",
            "seen_before": "Seen",
            "still_open": "Still open",
            "changed": "Changed",
            "meeting_cancelled": "Cancelled",
            "meeting_new": "New",
            "meeting_updated": "Updated",
            "meeting_recurring": "Recurring",
            "meeting_daily": "Daily",
            "meeting_weekly": "Weekly",
            "meeting_monthly": "Monthly",
            "meeting_yearly": "Yearly",
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
            "presence": "Today's location signal: {text}.",
            "meeting": "Upcoming meeting: {text}.",
        },
        "item_meta": {
            "status": "Status",
            "received": "Received",
            "status_unread": "Unread",
            "status_read": "Read",
            "sender": "Sender",
            "next_step": "Next step",
            "confidence": "Confidence",
            "confidence_high": "High",
            "confidence_medium": "Medium",
            "confidence_low": "Low",
        },
        "summary": {
            "critical": "Needs attention: {text}",
            "action": "Likely needs your follow-up: {text}",
            "action_other": "Action appears to sit with {owner}: {text}",
            "action_shared": "Shared follow-up: {text}",
            "watch": "Worth noting: {text}",
            "direct_target": "You're expected on this point: {text}",
            "direct_target_named": "Directly addressed to {name}: {text}",
            "candidate_profile": "Candidate profile: {text}",
            "candidate_follow_up": "Review the candidate or decide on follow-up.",
            "file_shared": "Shared a file or document for your review.",
            "download_shared": "Shared a download link for the latest version.",
            "from_sender": "From {sender}",
            "meeting_today": "Today, {time} | {organizer}",
            "meeting_day": "{day}, {time} | {organizer}",
            "meeting_today_self": "Today, {time}",
            "meeting_day_self": "{day}, {time}",
            "meeting_location": " | {location}",
            "meeting_context_note": "Context: {text}",
            "unknown_organizer": "an unknown organizer",
            "meeting_status_summary": "{status}: {text}",
            "presence_location": "Location signal for the day: {text}",
            "presence_remote": "Remote-work signal for the day: {text}",
            "thread_context": "Thread on {title}: {text}",
        },
        "actions": {
            "critical": "Review or intervene quickly.",
            "deliverable": "Review the shared file or link and reply if needed.",
            "reply": "Reply or confirm the requested point.",
            "reply_other": "Track this thread; the next action appears to belong to {owner}.",
            "reply_shared": "Coordinate with the thread participants before acting.",
            "verify_sender": "Verify the sender before acting.",
            "watch": "Keep this in view; no explicit action is confirmed yet.",
            "meeting_prepare": "Prepare the key points before it starts.",
            "meeting_watch": "Keep this meeting in view; context is still limited.",
            "meeting_cancelled": "Adjust the day plan; this meeting is no longer happening.",
            "meeting_updated": "Reconfirm the new timing or scope before it starts.",
            "meeting_new": "Check whether preparation is needed for this new meeting.",
            "presence": "Use this as the day's location or presence signal.",
        },
    },
    "fr": {
        "digest_title": "Votre brief Day Captain",
        "subject": "Votre brief Day Captain du {date}",
        "prepared": "À jour au {date}",
        "coverage_label": "Périmètre",
        "coverage_separator": " : ",
        "coverage_value": "Du {start} au {end}",
        "weather": {
            "label": "Météo du jour",
            "warmer": "Plus doux qu'hier.",
            "cooler": "Plus frais qu'hier.",
            "same": "Proche d'hier.",
            "dry_day": "Temps sec.",
            "rain_risk": "Risque de pluie.",
            "showers_likely": "Averses probables.",
            "rain_likely": "Pluie probable.",
            "storm_risk": "Risque d'orages.",
            "snow_likely": "Risque de neige.",
        },
        "external_news": {
            "label": "Actualités externes",
            "source_prefix": "Source",
            "link_label": "Ouvrir l'article",
        },
        "sections": {
            "critical_topics": "Points critiques",
            "actions_to_take": "Actions à mener",
            "watch_items": "À surveiller",
            "daily_presence": "Présence du jour",
            "upcoming_meetings": "Réunions à venir",
        },
        "empty": {
            "critical_topics": "Rien d'urgent pour l'instant.",
            "actions_to_take": "Aucun suivi immédiat.",
            "watch_items": "Rien d'autre à signaler.",
            "daily_presence": "Aucun événement journalier de présence pour {day}.",
            "upcoming_meetings": "Aucune réunion n'est prévue pour {day}.",
        },
        "meeting_notes": {
            "weekend_monday": "Aperçu des réunions de {day}.",
            "next_day": "Rien d'autre n'est prévu aujourd'hui, voici {day}.",
            "two_day_span": "Journée légère côté réunions, cette section inclut aussi {day}.",
            "next_two_days": "Rien d'autre n'est prévu aujourd'hui, voici {first_day} et {second_day}.",
        },
        "footer": {
            "label": "Actions rapides",
            "hint": "Utilisez ces boutons pour redemander ce brief, celui d'aujourd'hui ou celui de la semaine.",
            "recall": "Rappeler ce brief",
            "recall_today": "Rappel aujourd'hui",
            "recall_week": "Rappel semaine",
            "copyright": "Day Captain © {year}",
        },
        "item_actions": {
            "open_mail": "Ouvrir dans Outlook",
            "open_meeting": "Ouvrir la réunion",
            "open_mail_desktop": "Ouvrir dans Outlook bureau",
            "open_meeting_desktop": "Ouvrir la réunion dans Outlook bureau",
        },
        "badges": {
            "unread": "Non lu",
            "flagged": "Marqué",
            "promotional": "Promotion",
            "verify": "Vérifier",
            "suspicious": "Suspect",
            "seen_before": "Déjà vu",
            "still_open": "Toujours ouvert",
            "changed": "Évolue",
            "meeting_cancelled": "Annulé",
            "meeting_new": "Nouvelle réunion",
            "meeting_updated": "Déplacée",
            "meeting_recurring": "Récurrent",
            "meeting_daily": "Quotidien",
            "meeting_weekly": "Hebdo",
            "meeting_monthly": "Mensuel",
            "meeting_yearly": "Annuel",
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
            "presence": "Signal de présence du jour : {text}.",
            "meeting": "Réunion à venir : {text}.",
        },
        "item_meta": {
            "status": "Statut",
            "received": "Reçu",
            "status_unread": "Non lu",
            "status_read": "Lu",
            "sender": "Expéditeur",
            "next_step": "À faire",
            "confidence": "Confiance",
            "confidence_high": "Élevée",
            "confidence_medium": "Moyenne",
            "confidence_low": "Faible",
        },
        "summary": {
            "critical": "À surveiller de près : {text}",
            "action": "Demande probablement un suivi de votre part : {text}",
            "action_other": "L'action semble surtout attendue de {owner} : {text}",
            "action_shared": "Suivi partagé : {text}",
            "watch": "À noter : {text}",
            "direct_target": "Vous êtes attendu sur ce point : {text}",
            "direct_target_named": "Directement adressé à {name} : {text}",
            "candidate_profile": "Profil candidat : {text}",
            "candidate_follow_up": "Examiner la candidature ou proposer un suivi.",
            "file_shared": "Un fichier ou document a été partagé pour consultation.",
            "download_shared": "Un lien de téléchargement a été partagé pour la dernière version.",
            "from_sender": "De la part de {sender}",
            "meeting_today": "Aujourd'hui, {time} | {organizer}",
            "meeting_day": "{day}, {time} | {organizer}",
            "meeting_today_self": "Aujourd'hui, {time}",
            "meeting_day_self": "{day}, {time}",
            "meeting_location": " | {location}",
            "meeting_context_note": "Contexte : {text}",
            "unknown_organizer": "un organisateur inconnu",
            "meeting_status_summary": "{status} : {text}",
            "presence_location": "Signal de présence pour la journée : {text}",
            "presence_remote": "Signal de télétravail pour la journée : {text}",
            "thread_context": "Fil sur {title} : {text}",
        },
        "actions": {
            "critical": "Examiner ou traiter rapidement.",
            "deliverable": "Consulter le fichier ou le lien partagé puis répondre si besoin.",
            "reply": "Répondre ou confirmer le point demandé.",
            "reply_other": "Suivre ce fil ; l'action semble surtout attendue de {owner}.",
            "reply_shared": "Coordonner le suivi avec les participants du fil avant d'agir.",
            "verify_sender": "Vérifier l'expéditeur avant d'agir.",
            "watch": "Garder ce sujet en vue ; aucune action explicite n'est encore certaine.",
            "meeting_prepare": "Préparer les points clés avant le début.",
            "meeting_watch": "Garder cette réunion en vue ; le contexte reste limité.",
            "meeting_cancelled": "Ajuster la journée ; cette réunion n'a plus lieu.",
            "meeting_updated": "Reconfirmer l'horaire ou le périmètre avant le début.",
            "meeting_new": "Vérifier si une préparation est nécessaire pour cette nouvelle réunion.",
            "presence": "Utiliser cet élément comme signal de présence ou de lieu pour la journée.",
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

WEATHER_LABELS = {
    "en": {
        "clear": "Clear",
        "partly_cloudy": "Partly cloudy",
        "cloudy": "Cloudy",
        "fog": "Fog",
        "drizzle": "Drizzle",
        "rain": "Rain",
        "snow": "Snow",
        "showers": "Showers",
        "storm": "Thunderstorms",
        "mixed": "Mixed conditions",
    },
    "fr": {
        "clear": "Eclaircies",
        "partly_cloudy": "Partiellement nuageux",
        "cloudy": "Couvert",
        "fog": "Brouillard",
        "drizzle": "Bruine",
        "rain": "Pluie",
        "snow": "Neige",
        "showers": "Averses",
        "storm": "Orages",
        "mixed": "Temps variable",
    },
}


def _normalize_text(*parts: str) -> str:
    return " ".join(part.strip().lower() for part in parts if part).strip()


def _weather_kind(weather_code: int) -> str:
    if weather_code == 0:
        return "clear"
    if weather_code in {1, 2}:
        return "partly_cloudy"
    if weather_code == 3:
        return "cloudy"
    if weather_code in {45, 48}:
        return "fog"
    if weather_code in {51, 53, 55, 56, 57}:
        return "drizzle"
    if weather_code in {61, 63, 65, 66, 67}:
        return "rain"
    if weather_code in {71, 73, 75, 77, 85, 86}:
        return "snow"
    if weather_code in {80, 81, 82}:
        return "showers"
    if weather_code in {95, 96, 99}:
        return "storm"
    return "mixed"


def _weather_label(weather_code: int, language: str) -> str:
    localized = WEATHER_LABELS.get(_normalize_language(language), WEATHER_LABELS["en"])
    return str(localized.get(_weather_kind(weather_code)) or localized["mixed"])


def _format_temperature(value: float) -> str:
    return "{0}C".format(int(round(value)))


def _contains_any(text: str, patterns: Iterable[str]) -> bool:
    return any(pattern in text for pattern in patterns)


def _language_hint_for_text(value: str) -> str:
    normalized = " ".join((value or "").strip().lower().split())
    if not normalized:
        return ""
    tokens = tuple(token.strip("'") for token in re.findall(r"[a-zA-ZÀ-ÿ']+", normalized))
    if not tokens:
        return ""
    english_score = sum(1 for token in tokens if token in ENGLISH_LANGUAGE_HINTS)
    french_score = sum(1 for token in tokens if token in FRENCH_LANGUAGE_HINTS)
    for phrase in ("please review", "need your input", "thank you", "before noon"):
        if phrase in normalized:
            english_score += 2
    for phrase in ("bonjour", "merci", "je vous", "votre retour"):
        if phrase in normalized:
            french_score += 2
    if english_score >= 2 and english_score > french_score:
        return "en"
    if french_score >= 2 and french_score > english_score:
        return "fr"
    return ""


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
    previous = None
    while candidate and candidate != previous:
        previous = candidate
        candidate = SUBJECT_PREFIX_PATTERN.sub("", candidate).strip()
        candidate = SUBJECT_TAG_PREFIX_PATTERN.sub("", candidate).strip()
    candidate = candidate.strip(" -_")
    lowered = candidate.lower()
    if lowered == "a imprimer":
        return "À imprimer"
    if lowered.startswith("a imprimer "):
        return "À imprimer"
    candidate = re.sub(r"(?<=\w)-\s+(?=\w)", " ", candidate)
    candidate = re.sub(r"\s*[-–—]\s*$", "", candidate)
    candidate = re.sub(r"\s+", " ", candidate).strip()
    return candidate


def _safe_source_url(value: str) -> str:
    candidate = str(value or "").strip()
    if candidate.startswith("https://") or candidate.startswith("http://"):
        return candidate
    return ""


def _safe_desktop_source_url(value: str) -> str:
    candidate = str(value or "").strip()
    if candidate.startswith("ms-outlook://") or candidate.startswith("outlook://") or candidate.startswith("olk://"):
        return candidate
    return ""


def _message_source_url(message: MessageRecord) -> str:
    return _safe_source_url(str(message.raw_payload.get("webLink") or ""))


def _message_desktop_source_url(message: MessageRecord) -> str:
    return _safe_desktop_source_url(
        str(message.raw_payload.get("outlookDesktopLink") or message.raw_payload.get("desktopLink") or "")
    )


def _meeting_source_url(meeting: MeetingRecord) -> str:
    web_link = _safe_source_url(str(meeting.raw_payload.get("webLink") or ""))
    if web_link:
        return web_link
    return _safe_source_url(meeting.join_url)


def _meeting_desktop_source_url(meeting: MeetingRecord) -> str:
    return _safe_desktop_source_url(
        str(meeting.raw_payload.get("outlookDesktopLink") or meeting.raw_payload.get("desktopLink") or "")
    )


def _message_is_flagged(message: MessageRecord) -> bool:
    flag_payload = message.raw_payload.get("flag") or {}
    if not isinstance(flag_payload, Mapping):
        return False
    return str(flag_payload.get("flagStatus") or "").strip().lower() == "flagged"


def _matched_patterns(text: str, patterns: Sequence[str]) -> Sequence[str]:
    normalized = str(text or "").strip().lower()
    if not normalized:
        return ()
    return tuple(pattern for pattern in patterns if pattern in normalized)


def _message_promotional_signal(message: MessageRecord, combined_text: str) -> str:
    offer_matches = _matched_patterns(combined_text, PROMOTIONAL_OFFER_PATTERNS)
    action_matches = _matched_patterns(combined_text, PROMOTIONAL_ACTION_PATTERNS)
    if not offer_matches:
        return ""
    sender = str(message.from_address or "").strip().lower()
    sender_local = sender.split("@", 1)[0] if "@" in sender else sender
    if action_matches:
        return "promotional"
    if len(offer_matches) >= 2 and sender_local in {"info", "newsletter", "news", "marketing"}:
        return "promotional"
    if len(offer_matches) >= 2:
        return "promotional_candidate"
    return ""


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


def _address_list_contains_identity(addresses: Sequence[str], identity: str) -> bool:
    if not identity:
        return False
    return any(_same_identity(address, identity) for address in addresses)


def _first_non_self_attendee(meeting: MeetingRecord) -> str:
    for attendee in meeting.attendees:
        if not _same_identity(attendee, meeting.user_id):
            return _humanize_identifier(attendee)
    return ""


def _target_recipient_display_name(message: MessageRecord) -> str:
    target_user = str(message.user_id or "").strip()
    if not target_user or "@" not in target_user:
        return _humanize_identifier(target_user)
    recipients = []
    raw_payload = message.raw_payload if isinstance(message.raw_payload, Mapping) else {}
    recipients.extend(raw_payload.get("toRecipients") or ())
    recipients.extend(raw_payload.get("ccRecipients") or ())
    for recipient in recipients:
        if not isinstance(recipient, Mapping):
            continue
        email = (recipient.get("emailAddress") or {}) if isinstance(recipient.get("emailAddress"), Mapping) else {}
        address = str(email.get("address") or "").strip()
        if not _same_identity(address, target_user):
            continue
        display_name = str(email.get("name") or "").strip()
        if display_name:
            return " ".join(display_name.split())
    return _humanize_identifier(target_user)


def _parse_optional_datetime(value: object) -> Optional[datetime]:
    candidate = str(value or "").strip()
    if not candidate:
        return None
    try:
        parsed = parse_datetime(candidate)
    except Exception:
        return None
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=timezone.utc)
    return parsed


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


def _strip_leading_salutation(sentence: str) -> str:
    cleaned = " ".join((sentence or "").strip().split())
    if not cleaned:
        return ""
    patterns = (
        r"^(bonjour|bonsoir|hello|hi|dear)\b[^,:\-]{0,80}[,:\-]\s*",
        r"^(madame,\s*monsieur|madame|monsieur)\b[,:\-]?\s*",
    )
    for pattern in patterns:
        cleaned = re.sub(pattern, "", cleaned, flags=re.IGNORECASE).strip()
    return cleaned


def _is_courtesy_sentence(sentence: str) -> bool:
    cleaned = _normalize_text(sentence)
    if not cleaned:
        return True
    return cleaned.startswith(
        (
            "merci pour",
            "merci beaucoup",
            "thank you for",
            "thanks for",
            "best regards",
            "kind regards",
            "cordialement",
            "bien a vous",
            "bien à vous",
            "bien a toi",
            "bien à toi",
        )
    )


def _decision_ready_preview(preview: str) -> str:
    cleaned = " ".join((preview or "").strip().split())
    if not cleaned:
        return ""
    sentences = []
    for raw in re.split(r"(?<=[.!?])\s+", cleaned):
        sentence = _strip_leading_salutation(raw)
        sentence = re.sub(r"\s+", " ", sentence).strip(" -")
        if not sentence:
            continue
        if _is_courtesy_sentence(sentence) and len(sentences) == 0:
            continue
        sentences.append(sentence)
        if len(sentences) >= 2:
            break
    if not sentences:
        fallback = _strip_leading_salutation(cleaned)
        return fallback.strip() or cleaned
    return " ".join(sentences).strip()


def _is_low_information_reply(preview: str) -> bool:
    cleaned = " ".join((preview or "").strip().split())
    if not cleaned:
        return True
    normalized = _normalize_text(cleaned)
    if len(cleaned) <= 18:
        return True
    if len(normalized.split()) <= 3 and normalized in {
        "ok",
        "okay",
        "bien recu",
        "bien reçu",
        "merci",
        "thanks",
        "thank you",
        "voici",
        "voici !",
        "done",
        "noted",
    }:
        return True
    return normalized in {
        "voici",
        "voici !",
        "ok merci",
        "ok, merci",
        "best",
        "thanks",
        "thank you",
    }


def _looks_like_fragment_start(text: str) -> bool:
    cleaned = " ".join((text or "").strip().split())
    if not cleaned:
        return False
    if cleaned[:1].islower():
        return True
    lowered = cleaned.lower()
    return lowered.startswith(
        (
            "qui ",
            "which ",
            "that ",
            "et ",
            "and ",
            "mais ",
            "but ",
            "ou ",
            "or ",
            "ainsi ",
        )
    )


def _thread_reinforced_preview(
    message: MessageRecord,
    thread_messages: Sequence[MessageRecord],
    cleaned_preview: str,
) -> str:
    latest_preview = _decision_ready_preview(cleaned_preview)
    if len(thread_messages) <= 1:
        return latest_preview
    candidates = []
    for candidate in sorted(thread_messages, key=lambda item: item.received_at):
        preview = _decision_ready_preview(_clean_preview(candidate.body_preview))
        if not preview:
            continue
        candidates.append((candidate.graph_message_id, preview))
    supporting = ""
    for graph_message_id, preview in reversed(candidates):
        if graph_message_id == message.graph_message_id:
            continue
        if preview == latest_preview:
            continue
        if _is_low_information_reply(preview):
            continue
        supporting = preview
        break
    if not supporting:
        return latest_preview
    if not latest_preview or _is_low_information_reply(latest_preview) or _looks_like_fragment_start(latest_preview):
        return supporting
    return latest_preview


def _is_candidate_profile_message(subject: str, preview: str) -> bool:
    normalized = _normalize_text(subject, preview)
    strong_markers = (
        "candidature",
        "candidate",
        "curriculum vitae",
        "cv ",
        "resume",
        "résumé",
        "job application",
        "application spontan",
        "candidature spontan",
        "alternance",
        "stage",
    )
    if any(marker in normalized for marker in strong_markers):
        return True
    profile_context_markers = (
        "je suis",
        "i am",
        "designer chez",
        "working at",
        "currently at",
        "cherche une nouvelle opportunit",
        "looking for a new opportunity",
    )
    profile_background_markers = (
        "bachelor",
        "master",
        "designer",
    )
    return any(marker in normalized for marker in profile_context_markers) and any(
        marker in normalized for marker in profile_background_markers
    )


def _is_low_signal_watch_message(subject: str, preview: str) -> bool:
    normalized_subject = _normalize_text(subject)
    normalized_preview = _normalize_text(preview)
    if normalized_subject.startswith("how to ") or normalized_subject.startswith("guide to "):
        return True
    return _contains_any(normalized_subject, LOW_SIGNAL_WATCH_PATTERNS) or _contains_any(
        normalized_preview,
        LOW_SIGNAL_WATCH_PATTERNS,
    )


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


def _overview_item_fragment(item: DigestEntry, language: str, max_chars: int = 90) -> str:
    if item.source_kind == "message":
        summary = _strip_known_summary_prefix(item.summary, language)
        if summary:
            return _clean_overview_fragment(_truncate_sentence(summary, max_chars=max_chars))
    return _clean_overview_fragment(_truncate_sentence(item.title, max_chars=max_chars))


def _truncate_sentence(value: str, max_chars: int = 220) -> str:
    cleaned = " ".join((value or "").strip().split())
    if len(cleaned) <= max_chars:
        return cleaned
    forward_window = cleaned[max_chars : max_chars + 28]
    forward_match = re.search(r"[.!?](?:\s|$)", forward_window)
    if forward_match:
        return cleaned[: max_chars + forward_match.end()].strip()
    backward_window = cleaned[:max_chars]
    backward_matches = list(re.finditer(r"[.!?](?:\s|$)", backward_window))
    if backward_matches:
        last_match = backward_matches[-1]
        if last_match.end() >= int(max_chars * 0.65):
            return backward_window[: last_match.end()].strip()
    truncated = cleaned[:max_chars].rstrip()
    if " " in truncated:
        truncated = truncated.rsplit(" ", 1)[0].rstrip()
    return truncated.rstrip(" .!?:;,\n\t") + "..."


def _polish_top_summary_phrase(value: str) -> str:
    cleaned = " ".join((value or "").strip().split())
    cleaned = re.sub(r"\bla prochaine a lieu\b", "la plus proche est", cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r"\bthe next one is\b", "the nearest one is", cleaned, flags=re.IGNORECASE)
    return cleaned


def _normalize_top_summary(value: str) -> str:
    cleaned = " ".join((value or "").strip().split())
    if not cleaned:
        return ""
    cleaned = _polish_top_summary_phrase(cleaned)
    return cleaned


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


def _strip_known_summary_prefix(summary: str, language: str) -> str:
    cleaned = " ".join((summary or "").strip().split())
    if not cleaned:
        return ""
    prefixes = {
        "en": (
            "Needs attention:",
            "Likely needs your follow-up:",
            "Critical:",
            "Action:",
            "Worth noting:",
            "You're expected on this point:",
            "Candidate profile:",
        ),
        "fr": (
            "À surveiller de près :",
            "Demande probablement un suivi de votre part :",
            "Urgent :",
            "Action :",
            "À noter :",
            "Vous êtes attendu sur ce point :",
            "Profil candidat :",
        ),
    }
    for prefix in prefixes[_normalize_language(language)]:
        if cleaned.lower().startswith(prefix.lower()):
            return cleaned[len(prefix) :].strip()
    return cleaned


def _item_summary_limit(item: DigestEntry) -> int:
    if item.source_kind == "meeting":
        return 130
    if item.section_name == "critical_topics":
        return 190
    if item.section_name == "actions_to_take":
        return 220
    if item.section_name == "watch_items":
        return 220
    return 240


def _normalized_confidence_label(value: str, score: int, language: str) -> str:
    candidate = str(value or "").strip().lower()
    localized = _language_copy(language)["item_meta"]
    if candidate in {"high", "elevated", "élevée", "elevee"} or score >= HIGH_CONFIDENCE_THRESHOLD:
        return str(localized["confidence_high"])
    if candidate in {"medium", "moyenne"} or score >= LOW_CONFIDENCE_THRESHOLD:
        return str(localized["confidence_medium"])
    return str(localized["confidence_low"])


def _confidence_score_bounds(value: object) -> int:
    try:
        score = int(round(float(value)))
    except Exception:
        score = 0
    return max(0, min(100, score))


def _confidence_reason(value: str, fallback: str) -> str:
    candidate = " ".join((value or "").strip().split())
    return candidate or fallback


def _display_confidence_reason(value: str, language: str) -> str:
    normalized = " ".join((value or "").strip().split())
    compact_map = {
        "en": {
            "Explicit request or urgency is visible in the latest thread update.": "Explicit request in the latest thread update.",
            "The message preview is readable, but the broader thread context is limited.": "Readable preview; broader thread context is limited.",
            "Calendar details are supported by extra context for this briefing.": "Calendar details reinforced by extra context.",
            "This all-day agenda entry explicitly looks like a location or presence signal.": "Clear all-day location or presence signal.",
        },
        "fr": {
            "Une demande explicite ou une urgence apparaît dans la dernière mise à jour du fil.": "Demande explicite visible dans la dernière mise à jour.",
            "L'aperçu du message est exploitable, mais le contexte plus large du fil reste limité.": "Aperçu exploitable ; contexte plus large limité.",
            "Les détails calendrier sont soutenus par du contexte supplémentaire pour ce compte rendu.": "Détails calendrier renforcés par du contexte supplémentaire.",
            "Cet événement agenda sur la journée ressemble explicitement à un signal de lieu ou de présence.": "Signal clair de lieu ou de présence sur la journée.",
        },
    }
    localized = compact_map.get(_normalize_language(language), {})
    return _truncate_sentence(localized.get(normalized) or normalized, max_chars=95)


def _handling_bucket_from_section(section_name: str) -> str:
    if section_name in SECTION_NAMES:
        return section_name
    return "watch_items"


def _with_digest_entry_updates(item: DigestEntry, **changes) -> DigestEntry:
    payload = {
        "title": item.title,
        "summary": item.summary,
        "section_name": item.section_name,
        "source_kind": item.source_kind,
        "source_id": item.source_id,
        "score": item.score,
        "recommended_action": item.recommended_action,
        "handling_bucket": item.handling_bucket,
        "confidence_score": item.confidence_score,
        "confidence_label": item.confidence_label,
        "confidence_reason": item.confidence_reason,
        "context_metadata": dict(item.context_metadata),
        "source_url": item.source_url,
        "desktop_source_url": item.desktop_source_url,
        "sort_at": item.sort_at,
        "reason_codes": item.reason_codes,
        "guardrail_applied": item.guardrail_applied,
        "card": item.card,
    }
    payload.update(changes)
    return DigestEntry(**payload)


def _is_promotional_item(item: DigestEntry) -> bool:
    codes = set(item.reason_codes)
    return "promotional" in codes


def _promotional_reason(value: str, language: str) -> str:
    cleaned = " ".join(str(value or "").split())
    if cleaned:
        return cleaned
    if language == "fr":
        return "Le contenu ressemble surtout à une sollicitation commerciale plutôt qu'à un suivi opérationnel."
    return "The content looks primarily promotional rather than operational."


def _preview_snippet(value: str, limit: int = THREAD_CONTEXT_PREVIEW_LIMIT) -> str:
    return _truncate_sentence(_decision_ready_preview(_clean_preview(value)), max_chars=limit)


def _thread_context_payload(messages: Sequence[MessageRecord], display_timezone: str) -> Mapping[str, object]:
    zone = _display_zone(display_timezone)
    ordered = sorted(messages, key=lambda item: item.received_at)
    participants = []
    thread_messages = []
    for message in ordered[:THREAD_CONTEXT_MESSAGE_LIMIT]:
        sender_name = _humanize_identifier(message.from_address) or message.from_address
        if sender_name and sender_name not in participants:
            participants.append(sender_name)
        thread_messages.append(
            {
                "sender": sender_name,
                "received_at": message.received_at.astimezone(zone).isoformat(),
                "preview": _preview_snippet(message.body_preview),
            }
        )
    return {
        "thread_id": ordered[-1].thread_id if ordered else "",
        "message_count": len(messages),
        "participants": participants[:4],
        "latest_sender_display_name": _humanize_identifier(ordered[-1].from_address) or ordered[-1].from_address if ordered else "",
        "latest_is_unread": bool(ordered[-1].is_unread) if ordered else False,
        "target_recipient_display_name": _target_recipient_display_name(ordered[-1]) if ordered else "",
        "source_language_hint": (
            _language_hint_for_text("{0} {1}".format(ordered[-1].subject or "", ordered[-1].body_preview or ""))
            if ordered
            else ""
        ),
        "messages": thread_messages,
    }


def _message_thread_briefing(
    message: MessageRecord,
    cleaned_preview: str,
    reason_codes: Sequence[str],
    digest_language: str,
    *,
    duplicate_count: int = 1,
    thread_messages: Sequence[MessageRecord] = (),
) -> str:
    reinforced_preview = _thread_reinforced_preview(
        message,
        thread_messages or (message,),
        cleaned_preview,
    )
    summary = DeterministicScoringEngine(digest_language=digest_language)._summarize_message(
        message,
        reinforced_preview,
        reason_codes,
    )
    if duplicate_count <= 1:
        return summary
    copy = _language_copy(digest_language)["summary"]
    base = _strip_known_summary_prefix(summary, digest_language)
    threaded = str(copy["thread_context"]).format(
        title=_normalize_display_title(message.subject or ""),
        text=base,
    )
    return _normalize_item_summary(message.subject or "", threaded, max_chars=220)


def _message_summary_for_thread_input(summary: str, thread_input, digest_language: str) -> str:
    if thread_input is None:
        return summary
    copy = _language_copy(digest_language)["summary"]
    base = _strip_known_summary_prefix(summary, digest_language)
    if thread_input.action_owner == "other":
        owner = thread_input.action_owner_display_name or (
            "someone else" if digest_language == "en" else "quelqu'un d'autre"
        )
        return _normalize_item_summary("", str(copy["action_other"]).format(owner=owner, text=base), max_chars=220)
    if thread_input.action_owner == "shared":
        return _normalize_item_summary("", str(copy["action_shared"]).format(text=base), max_chars=220)
    return summary


def _message_recommended_action(message: MessageRecord, reason_codes: Sequence[str], digest_language: str, thread_input=None) -> str:
    actions = _language_copy(digest_language)["actions"]
    if thread_input is not None and thread_input.risk_level in {"medium", "high"}:
        return str(actions["verify_sender"])
    if "promotional" in reason_codes:
        return ""
    if "promotional_candidate" in reason_codes:
        return str(actions["watch"])
    if "critical_keyword" in reason_codes:
        return str(actions["critical"])
    normalized_preview = _normalize_text(message.subject, message.body_preview)
    if "deliverable_shared" in reason_codes or "download" in normalized_preview or "telechargement" in normalized_preview or "téléchargement" in normalized_preview:
        return str(actions["deliverable"])
    if "action_keyword" in reason_codes or "direct_target_recipient" in reason_codes or "flagged" in reason_codes:
        if thread_input is not None and thread_input.action_owner == "other":
            owner = thread_input.action_owner_display_name or (
                "someone else" if digest_language == "en" else "quelqu'un d'autre"
            )
            return str(actions["reply_other"]).format(owner=owner)
        if thread_input is not None and thread_input.action_owner == "shared":
            return str(actions["reply_shared"])
        return str(actions["reply"])
    return str(actions["watch"])


def _message_confidence(message: MessageRecord, reason_codes: Sequence[str], duplicate_count: int, preview: str, digest_language: str, thread_input=None) -> tuple[int, str]:
    if thread_input is not None and thread_input.risk_level == "high":
        return 38, (
            "The message shows several suspicious signals, so it should not be trusted without manual verification."
            if digest_language == "en"
            else "Plusieurs signaux suspects sont visibles ; il ne faut pas faire confiance à ce message sans vérification manuelle."
        )
    if thread_input is not None and thread_input.risk_level == "medium":
        return 49, (
            "Some suspicious signals are visible, so the sender should be verified before acting."
            if digest_language == "en"
            else "Quelques signaux suspects sont visibles ; l'expéditeur doit être vérifié avant d'agir."
        )
    if "promotional" in reason_codes:
        return 52, (
            "The content reads primarily like a promotional message rather than a concrete operational request."
            if digest_language == "en"
            else "Le contenu ressemble surtout à un message promotionnel plutôt qu'à une demande opérationnelle concrète."
        )
    if "promotional_candidate" in reason_codes:
        return 46, (
            "Some marketing cues are visible, so this item should be treated cautiously."
            if digest_language == "en"
            else "Des indices marketing sont visibles, donc cet élément doit être traité avec prudence."
        )
    if "critical_keyword" in reason_codes or "action_keyword" in reason_codes:
        return 88, (
            "Explicit request or urgency is visible in the latest thread update."
            if digest_language == "en"
            else "Une demande explicite ou une urgence apparaît dans la dernière mise à jour du fil."
        )
    if duplicate_count > 1 and preview:
        return 78, (
            "Several messages are available in the thread and the latest update is readable."
            if digest_language == "en"
            else "Plusieurs messages sont disponibles dans le fil et la dernière mise à jour est lisible."
        )
    if preview:
        return 67, (
            "The message preview is readable, but the broader thread context is limited."
            if digest_language == "en"
            else "L'aperçu du message est exploitable, mais le contexte plus large du fil reste limité."
        )
    return 48, (
        "Only thin message context is available for this briefing."
        if digest_language == "en"
        else "Le contexte disponible pour ce compte rendu reste très limité."
    )


def _meeting_is_all_day(meeting: MeetingRecord) -> bool:
    raw_payload = meeting.raw_payload if isinstance(meeting.raw_payload, Mapping) else {}
    if bool(raw_payload.get("isAllDay")):
        return True
    duration = meeting.end_at - meeting.start_at
    return duration >= timedelta(hours=20)


def _looks_like_presence_signal(meeting: MeetingRecord) -> bool:
    normalized = _normalize_text(meeting.subject, meeting.location)
    return _contains_any(normalized, PRESENCE_PATTERNS)


def _presence_summary(meeting: MeetingRecord, digest_language: str) -> str:
    copy = _language_copy(digest_language)["summary"]
    location_text = _normalize_display_title(meeting.location or meeting.subject or "")
    if _contains_any(_normalize_text(meeting.subject, meeting.location), ("teletravail", "télétravail", "remote", "wfh", "home office", "home-office")):
        return str(copy["presence_remote"]).format(text=location_text or _normalize_display_title(meeting.subject or ""))
    return str(copy["presence_location"]).format(text=location_text or _normalize_display_title(meeting.subject or ""))


def _presence_confidence(digest_language: str) -> tuple[int, str]:
    return 92, (
        "This all-day agenda entry explicitly looks like a location or presence signal."
        if digest_language == "en"
        else "Cet événement agenda sur la journée ressemble explicitement à un signal de lieu ou de présence."
    )


def _related_messages_for_meeting(
    meeting: MeetingRecord,
    messages: Sequence[MessageRecord],
) -> Sequence[Mapping[str, str]]:
    if not messages:
        return ()
    meeting_tokens = set(_tokenize_subject(_normalize_display_title(meeting.subject or "")))
    related = []
    for message in messages:
        score = 0
        if meeting_tokens and meeting_tokens.intersection(_tokenize_subject(_normalize_display_title(message.subject or ""))):
            score += 2
        if _same_identity(message.from_address, meeting.organizer_address):
            score += 1
        if score <= 0:
            continue
        related.append(
            (
                score,
                message.received_at,
                {
                    "subject": _normalize_display_title(message.subject or ""),
                    "sender": _humanize_identifier(message.from_address) or message.from_address,
                    "preview": _preview_snippet(message.body_preview, limit=140),
                },
            )
        )
    related = sorted(related, key=lambda item: (-item[0], -item[1].timestamp()))
    return tuple(item[2] for item in related[:MEETING_CONTEXT_MESSAGE_LIMIT])


def _meeting_recommended_action(reason_codes: Sequence[str], digest_language: str, *, has_related_context: bool = False) -> str:
    actions = _language_copy(digest_language)["actions"]
    if "meeting_cancelled" in reason_codes:
        return str(actions["meeting_cancelled"])
    if "meeting_updated" in reason_codes:
        return str(actions["meeting_updated"])
    if "meeting_new" in reason_codes:
        return str(actions["meeting_new"])
    if "meeting_soon" in reason_codes or has_related_context:
        return str(actions["meeting_prepare"])
    return str(actions["meeting_watch"])


def _meeting_confidence(meeting: MeetingRecord, reason_codes: Sequence[str], has_related_context: bool, digest_language: str) -> tuple[int, str]:
    if _meeting_is_all_day(meeting) and _looks_like_presence_signal(meeting):
        return _presence_confidence(digest_language)
    if has_related_context or meeting.body_preview.strip():
        return 81, (
            "Calendar details are supported by extra context for this briefing."
            if digest_language == "en"
            else "Les détails calendrier sont soutenus par du contexte supplémentaire pour ce compte rendu."
        )
    if "meeting_cancelled" in reason_codes or "meeting_updated" in reason_codes or "meeting_new" in reason_codes:
        return 76, (
            "Calendar metadata clearly shows a recent schedule change."
            if digest_language == "en"
            else "Les métadonnées calendrier montrent clairement un changement récent du planning."
        )
    return 58, (
        "This meeting briefing mainly relies on basic calendar metadata."
        if digest_language == "en"
        else "Ce compte rendu repose surtout sur les métadonnées de base du calendrier."
    )


def _meeting_related_context_summary(related_messages: Sequence[Mapping[str, str]], digest_language: str) -> str:
    if not related_messages:
        return ""
    first = dict(related_messages[0] or {})
    preview = " ".join(str(first.get("preview") or "").split())
    subject = " ".join(str(first.get("subject") or "").split())
    sender = " ".join(str(first.get("sender") or "").split())
    if not preview and not subject:
        return ""
    if preview:
        text = preview
    elif subject and sender:
        text = "{0} ({1})".format(subject, sender)
    else:
        text = subject or sender
    return str(_language_copy(digest_language)["summary"]["meeting_context_note"]).format(
        text=_truncate_sentence(text, max_chars=90)
    )


def _compact_candidate_profile_summary(title: str, summary: str) -> str:
    normalized = _normalize_text(title, summary)
    if not _is_candidate_profile_message(title, summary):
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


def _deterministic_candidate_profile_summary(title: str, preview: str, language: str) -> str:
    normalized = _normalize_text(title, preview)
    if not _is_candidate_profile_message(title, preview):
        return ""
    copy = _language_copy(language)["summary"]
    preview_text = " ".join((preview or "").strip().split())
    company_match = re.search(r"\bchez\s+([A-Z][A-Za-z0-9&' -]+)", preview_text)
    if not company_match:
        company_match = re.search(r"\bat\s+([A-Z][A-Za-z0-9&' -]+)", preview_text)
    company = company_match.group(1).strip() if company_match else ""
    if company:
        company = re.split(r"\b(depuis|for)\b|,", company, maxsplit=1)[0].strip()
    role_text = ""
    title_lower = title.lower()
    if "designer" in title_lower or "designer" in normalized:
        role_text = "designer chez {0}".format(company).strip() if company else "designer"
    elif company:
        role_text = company
    else:
        role_text = _normalize_display_title(title)
    profile = str(copy["candidate_profile"]).format(text=role_text).strip()
    if profile and profile[-1] not in ".!?":
        profile += "."
    follow_up = str(copy["candidate_follow_up"]).strip()
    return "{0} {1}".format(profile, follow_up).strip()


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


def _meeting_change_reason_codes(
    meeting: MeetingRecord,
    *,
    now: datetime,
    window_start: Optional[datetime],
) -> Sequence[str]:
    raw_payload = meeting.raw_payload if isinstance(meeting.raw_payload, Mapping) else {}
    reason_codes = []
    boundary = window_start or (now - timedelta(hours=18))
    created_at = _parse_optional_datetime(raw_payload.get("createdDateTime"))
    modified_at = _parse_optional_datetime(raw_payload.get("lastModifiedDateTime"))
    if bool(raw_payload.get("isCancelled")):
        reason_codes.append("meeting_cancelled")
    if created_at is not None and created_at >= boundary:
        reason_codes.append("meeting_new")
    elif (
        modified_at is not None
        and modified_at >= boundary
        and (created_at is None or modified_at > created_at + timedelta(minutes=5))
    ):
        reason_codes.append("meeting_updated")
    return tuple(reason_codes)


def _meeting_status_reason(reason_codes: Sequence[str]) -> str:
    for code in ("meeting_cancelled", "meeting_new", "meeting_updated"):
        if code in reason_codes:
            return code
    return ""


def _meeting_recurrence_kind(meeting: MeetingRecord) -> str:
    raw_payload = meeting.raw_payload if isinstance(meeting.raw_payload, Mapping) else {}
    recurrence = raw_payload.get("recurrence") or {}
    if isinstance(recurrence, Mapping):
        pattern = recurrence.get("pattern") or {}
        if isinstance(pattern, Mapping):
            pattern_type = str(pattern.get("type") or "").strip().lower()
            if pattern_type in {"daily", "weekly", "absoluteMonthly".lower(), "relativeMonthly".lower(), "absoluteYearly".lower(), "relativeYearly".lower()}:
                if "daily" in pattern_type:
                    return "daily"
                if "weekly" in pattern_type:
                    return "weekly"
                if "monthly" in pattern_type:
                    return "monthly"
                if "yearly" in pattern_type:
                    return "yearly"
    event_type = str(raw_payload.get("type") or "").strip().lower()
    if event_type in {"seriesmaster", "occurrence", "exception"} or raw_payload.get("seriesMasterId"):
        return "recurring"
    return ""


def _meeting_recurrence_label(meeting: MeetingRecord, digest_language: str) -> str:
    kind = _meeting_recurrence_kind(meeting)
    if not kind:
        return ""
    badges = _language_copy(digest_language)["badges"]
    return str(badges.get("meeting_{0}".format(kind)) or badges["meeting_recurring"])


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
        window_start: Optional[datetime] = None,
    ) -> Sequence[DigestEntry]:
        now = reference_time or datetime.now(timezone.utc)
        preference_weights = {
            preference.preference_key: preference.weight for preference in preferences
        }
        prioritized = []
        thread_candidates = {}
        thread_messages = {}
        for message in messages:
            entry = self._score_message(message, preference_weights, now)
            thread_key = self._thread_key(message)
            thread_messages.setdefault(thread_key, []).append(message)
            if entry is not None:
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
        for thread_key, (message, entry, duplicate_count) in thread_candidates.items():
            prioritized.append(
                self._finalize_message_entry(
                    message,
                    entry,
                    duplicate_count,
                    thread_messages=tuple(thread_messages.get(thread_key) or (message,)),
                )
            )
        for meeting in meetings:
            prioritized.append(
                self._score_meeting(
                    meeting,
                    now,
                    messages=messages,
                    window_start=window_start,
                )
            )
        return tuple(sorted(prioritized, key=lambda item: (-item.score, item.title.lower())))

    def _thread_key(self, message: MessageRecord) -> str:
        if message.thread_id:
            return message.thread_id
        subject = _normalize_display_title(message.subject or "")
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
        return _with_digest_entry_updates(
            entry,
            reason_codes=tuple(entry.reason_codes) + ("thread_collapsed",),
        )

    def _finalize_message_entry(
        self,
        message: MessageRecord,
        entry: DigestEntry,
        duplicate_count: int,
        *,
        thread_messages: Sequence[MessageRecord],
    ) -> DigestEntry:
        base_entry = self._with_thread_reason(entry, duplicate_count)
        thread_input = build_mail_thread_digest_input(
            message,
            thread_messages,
            display_timezone=self.display_timezone,
            action_detected=bool(
                {"action_keyword", "direct_target_recipient", "flagged"} & set(base_entry.reason_codes)
            ),
        )
        adjusted_reason_codes = tuple(base_entry.reason_codes)
        adjusted_entry = base_entry
        if thread_input.risk_level in {"medium", "high"} and "suspicious_mail" not in adjusted_reason_codes:
            adjusted_reason_codes = adjusted_reason_codes + ("suspicious_mail",)
        if thread_input.risk_level == "high" and adjusted_entry.section_name != "watch_items":
            adjusted_entry = _with_digest_entry_updates(
                adjusted_entry,
                section_name="watch_items",
                score=round(max(0.1, adjusted_entry.score - 1.5), 2),
                reason_codes=adjusted_reason_codes,
            )
        elif thread_input.action_owner == "other" and adjusted_entry.section_name == "actions_to_take" and "critical_keyword" not in adjusted_entry.reason_codes:
            adjusted_entry = _with_digest_entry_updates(
                adjusted_entry,
                section_name="watch_items",
                score=round(max(0.1, adjusted_entry.score - 0.5), 2),
                reason_codes=adjusted_reason_codes,
            )
        elif adjusted_reason_codes != tuple(adjusted_entry.reason_codes):
            adjusted_entry = _with_digest_entry_updates(adjusted_entry, reason_codes=adjusted_reason_codes)
        cleaned_preview = _clean_preview(message.body_preview)
        reinforced_preview = _thread_reinforced_preview(message, thread_messages, cleaned_preview)
        summary = _message_thread_briefing(
            message,
            cleaned_preview,
            adjusted_entry.reason_codes,
            self.digest_language,
            duplicate_count=duplicate_count,
            thread_messages=thread_messages,
        )
        summary = _message_summary_for_thread_input(summary, thread_input, self.digest_language)
        confidence_score, confidence_reason = _message_confidence(
            message,
            adjusted_entry.reason_codes,
            duplicate_count,
            reinforced_preview,
            self.digest_language,
            thread_input=thread_input,
        )
        context_metadata = dict(_thread_context_payload(thread_messages, self.display_timezone))
        context_metadata.update(
            {
                "action_owner": thread_input.action_owner,
                "action_owner_display_name": thread_input.action_owner_display_name,
                "action_expected_from_user": thread_input.action_expected_from_user,
                "relevance_to_user": thread_input.relevance_to_user,
                "risk_level": thread_input.risk_level,
                "risk_reasons": list(thread_input.risk_reasons),
                "trust_signals": list(thread_input.trust_signals),
            }
        )
        return _with_digest_entry_updates(
            adjusted_entry,
            summary=summary,
            recommended_action=_message_recommended_action(
                message,
                adjusted_entry.reason_codes,
                self.digest_language,
                thread_input=thread_input,
            ),
            handling_bucket=_handling_bucket_from_section(adjusted_entry.section_name),
            confidence_score=confidence_score,
            confidence_label=_normalized_confidence_label("", confidence_score, self.digest_language),
            confidence_reason=confidence_reason,
            context_metadata=context_metadata,
            card=DigestCard(
                sender_display_name=thread_input.latest_sender_display_name,
                is_unread=thread_input.latest_is_unread,
                target_recipient_display_name=thread_input.target_recipient_display_name,
                source_language_hint=thread_input.source_language_hint,
                action_owner=thread_input.action_owner,
                action_owner_display_name=thread_input.action_owner_display_name,
                action_expected_from_user=thread_input.action_expected_from_user,
                relevance_to_user=thread_input.relevance_to_user,
                risk_level=thread_input.risk_level,
                risk_reasons=thread_input.risk_reasons,
                trust_signals=thread_input.trust_signals,
            ),
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
        is_candidate_profile = _is_candidate_profile_message(subject, cleaned_preview)

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
        if _message_is_flagged(message):
            score += 1.75
            reason_codes.append("flagged")
        if message.has_attachments:
            score += 0.25
            reason_codes.append("attachment_present")
        target_in_to = _address_list_contains_identity(message.to_addresses, message.user_id)
        target_in_cc = _address_list_contains_identity(message.cc_addresses, message.user_id)
        if target_in_to:
            score += 1.35
            reason_codes.append("direct_target_recipient")
        elif target_in_cc:
            score += 0.3
            reason_codes.append("target_cc")
        elif message.to_addresses:
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

        promotional_signal = _message_promotional_signal(message, combined_text)
        if promotional_signal == "promotional":
            score -= 2.25
            reason_codes.append("promotional")
        elif promotional_signal == "promotional_candidate":
            score -= 0.75
            reason_codes.append("promotional_candidate")

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
        elif "promotional" in reason_codes:
            section_name = "watch_items"
        elif (
            "action_keyword" in reason_codes
            or "flagged" in reason_codes
            or (
                "direct_target_recipient" in reason_codes
                and not _is_low_signal_watch_message(subject, cleaned_preview)
            )
        ):
            section_name = "actions_to_take"
        else:
            section_name = "watch_items"

        if section_name == "watch_items" and not guardrail:
            internal_domain = _domain_from_email(message.user_id)
            internal_sender = bool(internal_domain and domain == internal_domain)
            strong_watch_signal = (
                "preference_signal" in reason_codes
                or "attachment_present" in reason_codes
                or "executive_sender" in reason_codes
                or ("direct_recipient" in reason_codes and internal_sender)
                or is_candidate_profile
            )
            if "promotional" in reason_codes and not strong_watch_signal and score < 1.5:
                return None
            if _is_low_signal_watch_message(subject, cleaned_preview) and not strong_watch_signal:
                return None
            if not strong_watch_signal and score < 1.75:
                return None

        summary = self._summarize_message(message, cleaned_preview, reason_codes)
        return DigestEntry(
            title=subject,
            summary=summary,
            section_name=section_name,
            source_kind="message",
            source_id=message.graph_message_id,
            score=round(score, 2),
            source_url=_message_source_url(message),
            desktop_source_url=_message_desktop_source_url(message),
            sort_at=message.received_at,
            reason_codes=tuple(reason_codes),
            guardrail_applied=guardrail,
        )

    def _score_meeting(
        self,
        meeting: MeetingRecord,
        now: datetime,
        *,
        messages: Sequence[MessageRecord] = (),
        window_start: Optional[datetime] = None,
    ) -> DigestEntry:
        hours_until = (meeting.start_at - now).total_seconds() / 3600.0
        copy = _language_copy(self.digest_language)["summary"]
        local_start = meeting.start_at.astimezone(_display_zone(self.display_timezone))
        local_now = now.astimezone(_display_zone(self.display_timezone))
        score = 1.0
        reason_codes = ["meeting_context"]
        related_messages = _related_messages_for_meeting(meeting, messages)
        if related_messages:
            reason_codes.append("meeting_related_context")
        recurrence_label = _meeting_recurrence_label(meeting, self.digest_language)
        if recurrence_label:
            reason_codes.append("meeting_recurring")
        agenda_kind = "presence" if _meeting_is_all_day(meeting) and _looks_like_presence_signal(meeting) else "meeting"
        agenda_input = build_agenda_digest_input(
            meeting,
            event_kind=agenda_kind,
            recurrence_label=recurrence_label,
            related_messages=related_messages,
            display_timezone=self.display_timezone,
        )
        if _meeting_is_all_day(meeting) and _looks_like_presence_signal(meeting):
            summary = _presence_summary(meeting, self.digest_language)
            confidence_score, confidence_reason = _presence_confidence(self.digest_language)
            return DigestEntry(
                title=_normalize_display_title(meeting.location or meeting.subject or "(presence event)"),
                summary=summary,
                section_name="daily_presence",
                source_kind="meeting",
                source_id=meeting.graph_event_id,
                score=round(score + 0.2, 2),
                recommended_action=str(_language_copy(self.digest_language)["actions"]["presence"]),
                handling_bucket="daily_presence",
                confidence_score=confidence_score,
                confidence_label=_normalized_confidence_label("", confidence_score, self.digest_language),
                confidence_reason=confidence_reason,
                context_metadata={
                    "is_all_day": True,
                    "location": meeting.location,
                    "related_messages": list(agenda_input.related_messages),
                    "is_recurring": bool(agenda_input.recurrence_label),
                    "recurrence_label": agenda_input.recurrence_label,
                },
                source_url=_meeting_source_url(meeting),
                desktop_source_url=_meeting_desktop_source_url(meeting),
                sort_at=meeting.start_at,
                reason_codes=tuple(reason_codes) + ("all_day_presence",),
                guardrail_applied=False,
                card=DigestCard(recurrence_label=agenda_input.recurrence_label),
            )
        if hours_until <= 2:
            score += 1.5
            reason_codes.append("meeting_soon")
        elif hours_until <= 6:
            score += 1.0
            reason_codes.append("meeting_today")
        if meeting.is_online_meeting:
            score += 0.25
            reason_codes.append("online_meeting")
        change_reason_codes = _meeting_change_reason_codes(meeting, now=now, window_start=window_start)
        if "meeting_cancelled" in change_reason_codes:
            score += 1.6
        elif "meeting_new" in change_reason_codes:
            score += 1.0
        elif "meeting_updated" in change_reason_codes:
            score += 0.8
        reason_codes.extend(change_reason_codes)
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
        related_context_note = _meeting_related_context_summary(related_messages, self.digest_language)
        if related_context_note:
            summary = "{0}. {1}".format(summary.rstrip("."), related_context_note)
        status_reason = _meeting_status_reason(reason_codes)
        if status_reason:
            status_text = str(_language_copy(self.digest_language)["badges"][status_reason])
            summary = str(copy["meeting_status_summary"]).format(status=status_text, text=summary)
        confidence_score, confidence_reason = _meeting_confidence(
            meeting,
            reason_codes,
            bool(related_messages),
            self.digest_language,
        )
        return DigestEntry(
            title=_normalize_display_title(meeting.subject or "(untitled meeting)"),
            summary=summary,
            section_name="upcoming_meetings",
            source_kind="meeting",
            source_id=meeting.graph_event_id,
            score=round(score, 2),
            recommended_action=_meeting_recommended_action(
                reason_codes,
                self.digest_language,
                has_related_context=bool(related_messages),
            ),
            handling_bucket="upcoming_meetings",
            confidence_score=confidence_score,
            confidence_label=_normalized_confidence_label("", confidence_score, self.digest_language),
            confidence_reason=confidence_reason,
            context_metadata={
                "is_all_day": _meeting_is_all_day(meeting),
                "organizer": organizer,
                "attendees": list(meeting.attendees[:6]),
                "location": meeting.location,
                "body_preview": _preview_snippet(meeting.body_preview),
                "related_messages": list(agenda_input.related_messages),
                "is_recurring": bool(agenda_input.recurrence_label),
                "recurrence_label": agenda_input.recurrence_label,
            },
            source_url=_meeting_source_url(meeting),
            desktop_source_url=_meeting_desktop_source_url(meeting),
            sort_at=meeting.start_at,
            reason_codes=tuple(reason_codes),
            guardrail_applied=False,
            card=DigestCard(recurrence_label=agenda_input.recurrence_label),
        )

    def _summarize_message(
        self,
        message: MessageRecord,
        cleaned_preview: str,
        reason_codes: Sequence[str],
    ) -> str:
        copy = _language_copy(self.digest_language)["summary"]
        preview = _decision_ready_preview(cleaned_preview or (message.body_preview or "").strip())
        normalized_preview = _normalize_text(preview)
        base = preview if preview else copy["from_sender"].format(sender=message.from_address)
        source_language_hint = _language_hint_for_text("{0} {1}".format(message.subject or "", preview))
        mixed_english_source = self.digest_language == "fr" and source_language_hint == "en"
        candidate_summary = _deterministic_candidate_profile_summary(message.subject or "", preview, self.digest_language)
        if candidate_summary and "critical_keyword" not in reason_codes and "action_keyword" not in reason_codes:
            return candidate_summary
        if "deliverable_shared" in reason_codes:
            if "download" in normalized_preview or "telechargement" in normalized_preview or "téléchargement" in normalized_preview:
                return copy["download_shared"]
            return copy["file_shared"]
        if "critical_keyword" in reason_codes:
            template = "Urgent : {text}" if mixed_english_source else str(copy["critical"])
            return _normalize_item_summary(message.subject or "", template.format(text=base), max_chars=190)
        if "direct_target_recipient" in reason_codes:
            return _normalize_item_summary(message.subject or "", copy["direct_target"].format(text=base), max_chars=210)
        if "action_keyword" in reason_codes:
            template = "Action : {text}" if mixed_english_source else str(copy["action"])
            return _normalize_item_summary(message.subject or "", template.format(text=base), max_chars=210)
        return _normalize_item_summary(message.subject or "", copy["watch"].format(text=base), max_chars=210)


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
        weather: Optional[WeatherSnapshot] = None,
        external_news: Sequence[ExternalNewsItem] = (),
        meeting_horizon: Optional[Mapping[str, str]] = None,
    ) -> DigestPayload:
        sections = {name: [] for name in SECTION_NAMES}
        for item in prioritized_items:
            target_section = item.section_name if item.section_name in sections else "watch_items"
            sections[target_section].append(item)
        source_day = self._meeting_source_day(meeting_horizon or {})
        if source_day is not None:
            sections["daily_presence"] = [
                item
                for item in sections["daily_presence"]
                if item.sort_at is not None and item.sort_at.astimezone(_display_zone(self.display_timezone)).date() == source_day
            ]
        for name in SECTION_NAMES:
            if name == "upcoming_meetings":
                sections[name] = sorted(
                    sections[name],
                    key=lambda item: (
                        item.sort_at or datetime.max.replace(tzinfo=timezone.utc),
                        -item.score,
                        item.title.lower(),
                    ),
                )[:5]
            else:
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
            weather,
            external_news,
            meeting_horizon or {},
        )
        delivery_html = self._build_delivery_html(
            generated_at,
            window_start,
            window_end,
            sections,
            normalized_top_summary,
            command_mailbox,
            weather,
            external_news,
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
            "weather": {
                "forecast_date": weather.forecast_date.isoformat(),
                "weather_code": weather.weather_code,
                "temperature_max_c": weather.temperature_max_c,
                "temperature_min_c": weather.temperature_min_c,
                "location_name": weather.location_name,
                "previous_temperature_max_c": weather.previous_temperature_max_c,
            }
            if weather is not None
            else None,
            "external_news": [
                {
                    "headline": item.headline,
                    "summary": item.summary,
                    "source_name": item.source_name,
                    "source_url": item.source_url,
                }
                for item in external_news
            ],
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
            weather=weather,
            external_news=tuple(external_news),
            delivery_payload=delivery_payload,
            critical_topics=tuple(sections["critical_topics"]),
            actions_to_take=tuple(sections["actions_to_take"]),
            watch_items=tuple(sections["watch_items"]),
            daily_presence=tuple(sections["daily_presence"]),
            upcoming_meetings=tuple(sections["upcoming_meetings"]),
        )

    def _entry_payload(self, item: DigestEntry) -> Mapping[str, object]:
        return {
            "title": item.title,
            "summary": item.summary,
            "source_kind": item.source_kind,
            "source_id": item.source_id,
            "score": item.score,
            "recommended_action": item.recommended_action,
            "handling_bucket": item.handling_bucket,
            "confidence_score": item.confidence_score,
            "confidence_label": item.confidence_label,
            "confidence_reason": item.confidence_reason,
            "context_metadata": dict(item.context_metadata),
            "source_url": item.source_url,
            "desktop_source_url": item.desktop_source_url,
            "sort_at": item.sort_at.isoformat() if item.sort_at is not None else "",
            "reason_codes": list(item.reason_codes),
            "guardrail_applied": item.guardrail_applied,
            "card": {
                "sender_display_name": item.card.sender_display_name,
                "is_unread": item.card.is_unread,
                "target_recipient_display_name": item.card.target_recipient_display_name,
                "source_language_hint": item.card.source_language_hint,
                "recurrence_label": item.card.recurrence_label,
                "action_owner": item.card.action_owner,
                "action_owner_display_name": item.card.action_owner_display_name,
                "action_expected_from_user": item.card.action_expected_from_user,
                "relevance_to_user": item.card.relevance_to_user,
                "risk_level": item.card.risk_level,
                "risk_reasons": list(item.card.risk_reasons),
                "trust_signals": list(item.card.trust_signals),
                "continuity_state": item.card.continuity_state,
                "continuity_previous_date": item.card.continuity_previous_date,
                "continuity_reason": item.card.continuity_reason,
            }
            if item.card is not None
            else None,
        }

    def _build_delivery_body(
        self,
        generated_at: datetime,
        window_start: datetime,
        window_end: datetime,
        sections: Mapping[str, Sequence[DigestEntry]],
        top_summary: str,
        command_mailbox: str,
        weather: Optional[WeatherSnapshot],
        external_news: Sequence[ExternalNewsItem],
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
        weather_lines = self._weather_body_lines(weather)
        if weather_lines:
            lines.extend(weather_lines)
            lines.append("")
        news_lines = self._external_news_body_lines(external_news)
        if news_lines:
            lines.extend(news_lines)
            lines.append("")
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
        footer_lines = self._footer_body_lines(command_mailbox, generated_at)
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
        weather: Optional[WeatherSnapshot],
        external_news: Sequence[ExternalNewsItem],
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
        weather_html = self._weather_html(weather)
        if weather_html:
            parts.append(weather_html)
        news_html = self._external_news_html(external_news)
        if news_html:
            parts.append(news_html)
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
        footer_html = self._footer_html(command_mailbox, generated_at)
        if footer_html:
            parts.append(footer_html)
        parts.append("</div></body></html>")
        return "".join(parts)

    def _body_item_lines(self, item: DigestEntry) -> Sequence[str]:
        action_label, action_url = self._item_action(item)
        rendered_title = self._rendered_item_title(item)
        lines = [
            "- {0}{1}".format(self._body_badge_prefix(item), rendered_title),
            "  {0}".format(item.summary),
        ]
        meta_lines = self._body_meta_lines(item)
        lines.extend(meta_lines)
        if action_url:
            lines.append("  {0}: {1}".format(action_label, action_url))
        return tuple(lines)

    def _html_item(self, item: DigestEntry) -> str:
        action_html = self._item_action_html(item)
        rendered_title = self._rendered_item_title(item)
        return (
            "<div style=\"margin:0 0 10px;padding:12px 14px;border:1px solid #cbd5e1;border-radius:12px;\">"
            "<p style=\"margin:0 0 4px;font-size:15px;font-weight:600;color:#0f172a;\">{0}{1}</p>"
            "<p style=\"margin:0;font-size:14px;color:#334155;\">{2}</p>"
            "{3}{4}"
            "</div>"
        ).format(
            self._item_badges_html(item),
            self._html_escape(rendered_title),
            self._html_escape(item.summary),
            self._item_meta_html(item),
            action_html,
        )

    def _body_meta_lines(self, item: DigestEntry) -> Sequence[str]:
        localized = _language_copy(self.digest_language)["item_meta"]
        lines = []
        message_status = self._entry_message_status(item)
        if message_status:
            lines.append("  {0}: {1}".format(localized["status"], message_status))
        received_label = self._entry_received_label(item)
        if received_label:
            lines.append("  {0}: {1}".format(localized["received"], received_label))
        sender_name = self._entry_sender_name(item)
        if sender_name:
            lines.append("  {0}: {1}".format(localized["sender"], sender_name))
        recommended_action = " ".join((item.recommended_action or "").split())
        if recommended_action:
            lines.append("  {0}: {1}".format(localized["next_step"], recommended_action))
        confidence_label = self._entry_confidence_label(item)
        confidence_reason = _display_confidence_reason(item.confidence_reason, self.digest_language)
        if item.confidence_score > 0 or confidence_label or confidence_reason:
            confidence_bits = []
            if item.confidence_score > 0:
                confidence_bits.append(str(item.confidence_score))
            if confidence_label:
                confidence_bits.append(confidence_label)
            confidence_text = " / ".join(confidence_bits) if confidence_bits else confidence_label
            if confidence_reason:
                confidence_text = "{0} - {1}".format(confidence_text, confidence_reason).strip(" -")
            lines.append("  {0}: {1}".format(localized["confidence"], confidence_text))
        return tuple(lines)

    def _item_meta_html(self, item: DigestEntry) -> str:
        localized = _language_copy(self.digest_language)["item_meta"]
        parts = []
        message_status = self._entry_message_status(item)
        if message_status:
            parts.append(
                "<p style=\"margin:6px 0 0;font-size:12px;color:#475569;\"><strong>{0}:</strong> {1}</p>".format(
                    self._html_escape(str(localized["status"])),
                    self._html_escape(message_status),
                )
            )
        received_label = self._entry_received_label(item)
        if received_label:
            parts.append(
                "<p style=\"margin:6px 0 0;font-size:12px;color:#64748b;\"><strong>{0}:</strong> {1}</p>".format(
                    self._html_escape(str(localized["received"])),
                    self._html_escape(received_label),
                )
            )
        sender_name = self._entry_sender_name(item)
        if sender_name:
            parts.append(
                "<p style=\"margin:6px 0 0;font-size:12px;color:#475569;\"><strong>{0}:</strong> {1}</p>".format(
                    self._html_escape(str(localized["sender"])),
                    self._html_escape(sender_name),
                )
            )
        recommended_action = " ".join((item.recommended_action or "").split())
        if recommended_action:
            parts.append(
                "<p style=\"margin:6px 0 0;font-size:12px;color:#475569;\"><strong>{0}:</strong> {1}</p>".format(
                    self._html_escape(str(localized["next_step"])),
                    self._html_escape(recommended_action),
                )
            )
        confidence_label = self._entry_confidence_label(item)
        confidence_reason = _display_confidence_reason(item.confidence_reason, self.digest_language)
        if item.confidence_score > 0 or confidence_label or confidence_reason:
            confidence_bits = []
            if item.confidence_score > 0:
                confidence_bits.append(str(item.confidence_score))
            if confidence_label:
                confidence_bits.append(confidence_label)
            confidence_text = " / ".join(confidence_bits) if confidence_bits else confidence_label
            if confidence_reason:
                confidence_text = "{0} - {1}".format(confidence_text, confidence_reason).strip(" -")
            parts.append(
                "<p style=\"margin:6px 0 0;font-size:12px;color:#64748b;\"><strong>{0}:</strong> {1}</p>".format(
                    self._html_escape(str(localized["confidence"])),
                    self._html_escape(confidence_text),
                )
            )
        return "".join(parts)

    def _entry_sender_name(self, item: DigestEntry) -> str:
        if item.source_kind != "message":
            return ""
        if item.card is not None and item.card.sender_display_name:
            return " ".join(item.card.sender_display_name.split())
        metadata = item.context_metadata or {}
        sender_name = " ".join(str(metadata.get("latest_sender_display_name") or "").split())
        return sender_name

    def _entry_message_status(self, item: DigestEntry) -> str:
        if item.source_kind != "message":
            return ""
        if item.card is not None and item.card.is_unread is not None:
            localized = _language_copy(self.digest_language)["item_meta"]
            return str(localized["status_unread"] if bool(item.card.is_unread) else localized["status_read"])
        metadata = item.context_metadata or {}
        if "latest_is_unread" not in metadata:
            return ""
        localized = _language_copy(self.digest_language)["item_meta"]
        return str(localized["status_unread"] if bool(metadata.get("latest_is_unread")) else localized["status_read"])

    def _entry_received_label(self, item: DigestEntry) -> str:
        if item.source_kind != "message" or item.sort_at is None:
            return ""
        return _format_localized_timestamp(item.sort_at, self.display_timezone, self.digest_language)

    def _entry_confidence_label(self, item: DigestEntry) -> str:
        return _normalized_confidence_label(item.confidence_label, item.confidence_score, self.digest_language)

    def _item_action(self, item: DigestEntry) -> tuple[str, str]:
        desktop_source_url = _safe_desktop_source_url(item.desktop_source_url)
        source_url = _safe_source_url(item.source_url)
        if not desktop_source_url and not source_url:
            return ("", "")
        actions = _language_copy(self.digest_language)["item_actions"]
        if desktop_source_url:
            if item.source_kind == "meeting":
                return (str(actions["open_meeting_desktop"]), desktop_source_url)
            return (str(actions["open_mail_desktop"]), desktop_source_url)
        if item.source_kind == "meeting":
            return (str(actions["open_meeting"]), source_url)
        return (str(actions["open_mail"]), source_url)

    def _item_action_html(self, item: DigestEntry) -> str:
        action_label, action_url = self._item_action(item)
        if not action_url:
            return ""
        return (
            "<p style=\"margin:8px 0 0;\">"
            "<a href=\"{0}\" style=\"font-size:12px;font-weight:600;color:#334155;text-decoration:none;\">{1}</a>"
            "</p>"
        ).format(
            self._html_escape(action_url),
            self._html_escape(action_label),
        )

    def _body_badge_prefix(self, item: DigestEntry) -> str:
        labels = self._item_badge_labels(item)
        if not labels:
            return ""
        return "".join("[{0}] ".format(label) for label, _tone in labels)

    def _item_badges_html(self, item: DigestEntry) -> str:
        labels = self._item_badge_labels(item)
        if not labels:
            return ""
        parts = []
        for badge, tone in labels:
            if tone == "warning":
                background = "#fff3cd"
                border = "#facc15"
                color = "#854d0e"
            elif tone == "info":
                background = "#e0f2fe"
                border = "#7dd3fc"
                color = "#075985"
            else:
                background = "#f8fafc"
                border = "#cbd5e1"
                color = "#475569"
            parts.append(
                "<span style=\"display:inline-block;margin:0 8px 0 0;padding:2px 7px;border-radius:999px;"
                "background:{0};border:1px solid {1};color:{2};font-size:11px;font-weight:700;"
                "letter-spacing:0.04em;text-transform:uppercase;vertical-align:middle;\">{3}</span>".format(
                    background,
                    border,
                    color,
                    self._html_escape(badge),
                )
            )
        return "".join(parts)

    def _item_badge_labels(self, item: DigestEntry) -> Sequence[tuple[str, str]]:
        localized = _language_copy(self.digest_language)["badges"]
        labels = []
        if item.source_kind == "message" and (
            (item.card is not None and bool(item.card.is_unread))
            or bool((item.context_metadata or {}).get("latest_is_unread"))
        ):
            labels.append((str(localized["unread"]), "info"))
        if "flagged" in item.reason_codes:
            labels.append((str(localized["flagged"]), "warning"))
        if "promotional" in item.reason_codes:
            labels.append((str(localized["promotional"]), "neutral"))
        if item.card is not None:
            if item.card.risk_level == "high":
                labels.append((str(localized["suspicious"]), "warning"))
            elif item.card.risk_level == "medium":
                labels.append((str(localized["verify"]), "warning"))
            if item.card.continuity_state == "already_surfaced":
                labels.append((str(localized["seen_before"]), "neutral"))
            elif item.card.continuity_state == "still_open":
                labels.append((str(localized["still_open"]), "warning"))
            elif item.card.continuity_state == "changed":
                labels.append((str(localized["changed"]), "info"))
        recurrence_label = " ".join(
            str((item.card.recurrence_label if item.card is not None else "") or (item.context_metadata or {}).get("recurrence_label") or "").split()
        )
        if recurrence_label:
            labels.append((recurrence_label, "neutral"))
        return tuple(labels)

    def _rendered_item_title(self, item: DigestEntry) -> str:
        if item.source_kind != "meeting":
            return item.title
        status_reason = _meeting_status_reason(item.reason_codes)
        if not status_reason:
            return item.title
        status_label = str(_language_copy(self.digest_language)["badges"][status_reason])
        return "{0} : {1}".format(status_label, item.title)

    def _weather_body_lines(self, weather: Optional[WeatherSnapshot]) -> Sequence[str]:
        if weather is None:
            return ()
        localized = _language_copy(self.digest_language)["weather"]
        return (
            str(localized["label"]),
            self._weather_summary(weather),
        )

    def _weather_html(self, weather: Optional[WeatherSnapshot]) -> str:
        if weather is None:
            return ""
        localized = _language_copy(self.digest_language)["weather"]
        return (
            "<section style=\"margin:0 0 18px;padding:10px 12px;border:1px solid #dbe4ee;border-radius:12px;\">"
            "<p style=\"margin:0 0 4px;font-size:12px;font-weight:700;letter-spacing:0.08em;text-transform:uppercase;color:#64748b;\">{0}</p>"
            "<p style=\"margin:0;font-size:14px;color:#334155;\">{1}</p>"
            "</section>"
        ).format(
            self._html_escape(str(localized["label"])),
            self._html_escape(self._weather_summary(weather)),
        )

    def _weather_summary(self, weather: WeatherSnapshot) -> str:
        localized = _language_copy(self.digest_language)["weather"]
        condition = _weather_label(weather.weather_code, self.digest_language)
        headline = "{0}, {1} max / {2} min".format(
            condition,
            _format_temperature(weather.temperature_max_c),
            _format_temperature(weather.temperature_min_c),
        )
        if weather.location_name.strip():
            headline = "{0}: {1}".format(weather.location_name.strip(), headline)
        rain_signal = self._weather_rain_text(weather, localized)
        trend = self._weather_trend_text(weather, localized)
        if rain_signal and trend:
            return "{0}. {1} {2}".format(headline, rain_signal, trend)
        if rain_signal:
            return "{0}. {1}".format(headline, rain_signal)
        if trend:
            return "{0}. {1}".format(headline, trend)
        return headline

    def _external_news_body_lines(self, external_news: Sequence[ExternalNewsItem]) -> Sequence[str]:
        if not external_news:
            return ()
        localized = _language_copy(self.digest_language)["external_news"]
        lines = [str(localized["label"])]
        for item in external_news:
            lines.append("- {0}".format(item.headline))
            if item.summary:
                lines.append("  {0}".format(item.summary))
            lines.append(
                "  {0}: {1} ({2})".format(
                    str(localized["source_prefix"]),
                    item.source_name,
                    item.source_url,
                )
            )
        return tuple(lines)

    def _external_news_html(self, external_news: Sequence[ExternalNewsItem]) -> str:
        if not external_news:
            return ""
        localized = _language_copy(self.digest_language)["external_news"]
        parts = [
            "<section style=\"margin:0 0 18px;padding:10px 12px;border:1px solid #dbe4ee;border-radius:12px;\">",
            "<p style=\"margin:0 0 8px;font-size:12px;font-weight:700;letter-spacing:0.08em;text-transform:uppercase;color:#64748b;\">{0}</p>".format(
                self._html_escape(str(localized["label"]))
            ),
        ]
        for item in external_news:
            parts.append("<div style=\"margin:0 0 10px;\">")
            parts.append(
                "<p style=\"margin:0 0 4px;font-size:14px;font-weight:600;color:#0f172a;\">{0}</p>".format(
                    self._html_escape(item.headline)
                )
            )
            if item.summary:
                parts.append(
                    "<p style=\"margin:0 0 4px;font-size:13px;color:#334155;\">{0}</p>".format(
                        self._html_escape(item.summary)
                    )
                )
            parts.append(
                "<p style=\"margin:0;font-size:12px;color:#64748b;\">{0}: {1} · <a href=\"{2}\" style=\"color:#334155;text-decoration:none;\">{3}</a></p>".format(
                    self._html_escape(str(localized["source_prefix"])),
                    self._html_escape(item.source_name),
                    self._html_escape(item.source_url),
                    self._html_escape(str(localized["link_label"])),
                )
            )
            parts.append("</div>")
        parts.append("</section>")
        return "".join(parts)

    def _weather_rain_text(self, weather: WeatherSnapshot, localized: Mapping[str, str]) -> str:
        kind = _weather_kind(weather.weather_code)
        if kind in {"clear", "partly_cloudy", "cloudy", "fog"}:
            return str(localized["dry_day"])
        if kind == "drizzle":
            return str(localized["rain_risk"])
        if kind == "showers":
            return str(localized["showers_likely"])
        if kind == "rain":
            return str(localized["rain_likely"])
        if kind == "storm":
            return str(localized["storm_risk"])
        if kind == "snow":
            return str(localized["snow_likely"])
        return ""

    def _weather_trend_text(self, weather: WeatherSnapshot, localized: Mapping[str, str]) -> str:
        previous_temperature = weather.previous_temperature_max_c
        if previous_temperature is None:
            return ""
        delta = weather.temperature_max_c - previous_temperature
        if delta >= 1.0:
            return str(localized["warmer"])
        if delta <= -1.0:
            return str(localized["cooler"])
        return str(localized["same"])

    def _footer_body_lines(self, command_mailbox: str, generated_at: datetime) -> Sequence[str]:
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
            "{0}: {1}".format(str(footer["copyright"]).format(year=generated_at.year), PROJECT_REPOSITORY_URL),
        )

    def _footer_html(self, command_mailbox: str, generated_at: datetime) -> str:
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
        copyright_html = self._html_escape(str(footer["copyright"]).format(year=generated_at.year))
        parts.append("</tr></table>")
        parts.append(
            "<p style=\"margin:12px 0 0;font-size:12px;color:#94a3b8;\">"
            "<a href=\"{0}\" style=\"color:#94a3b8;text-decoration:none;\">{1}</a>"
            "</p>".format(
                self._html_escape(PROJECT_REPOSITORY_URL),
                copyright_html,
            )
        )
        parts.append("</section>")
        return "".join(parts)

    def _meeting_note(self, section_name: str, meeting_horizon: Mapping[str, str]) -> str:
        if section_name != "upcoming_meetings":
            return ""
        mode = str(meeting_horizon.get("mode") or "same_day")
        if mode not in {"weekend_monday", "next_day", "two_day_span", "next_two_days"}:
            return ""
        localized = _language_copy(self.digest_language)
        target_day = self._meeting_target_day(meeting_horizon)
        if target_day is None:
            return ""
        source_day = self._meeting_source_day(meeting_horizon) or target_day
        if mode == "next_two_days":
            first_day = source_day + timedelta(days=1)
            return localized["meeting_notes"][mode].format(
                first_day=self._meeting_horizon_day_label("next_day", first_day, source_day),
                second_day=self._meeting_horizon_day_label("next_day", target_day, source_day),
            )
        return localized["meeting_notes"][mode].format(
            day=self._meeting_horizon_day_label(mode, target_day, source_day)
        )

    def _empty_state(self, section_name: str, meeting_horizon: Mapping[str, str]) -> str:
        localized = _language_copy(self.digest_language)
        if section_name == "daily_presence":
            target_day = self._meeting_target_day(meeting_horizon)
            source_day = self._meeting_source_day(meeting_horizon)
            if target_day is None:
                target_day = datetime.now(_display_zone(self.display_timezone)).date()
            if source_day is None:
                source_day = target_day
            return localized["empty"]["daily_presence"].format(
                day=self._meeting_horizon_day_label(str(meeting_horizon.get("mode") or "same_day"), target_day, source_day)
            )
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
            .replace("\"", "&quot;")
        )


class IdentityDigestWordingEngine:
    def __init__(self, digest_language: str = "en") -> None:
        self.digest_language = _normalize_language(digest_language)

    def rewrite(
        self,
        prioritized_items: Sequence[DigestEntry],
    ) -> Sequence[DigestEntry]:
        localized = _language_copy(self.digest_language)["summary"]
        rewritten = []
        for item in prioritized_items:
            if item.source_kind != "message" or "direct_target_recipient" not in item.reason_codes:
                rewritten.append(item)
                continue
            base = _strip_known_summary_prefix(item.summary, self.digest_language)
            rewritten_summary = str(localized["direct_target"]).format(text=base)
            summary = _normalize_item_summary(
                item.title,
                rewritten_summary,
                max_chars=_item_summary_limit(item),
            )
            rewritten.append(_with_digest_entry_updates(item, summary=summary))
        return tuple(rewritten)


class DeterministicDigestOverviewEngine:
    def summarize(
        self,
        payload: DigestPayload,
    ) -> DigestOverview:
        language = _normalize_language(str(payload.delivery_payload.get("digest_language") or "en"))
        localized = _language_copy(language)["overview"]
        sections = {
            "critical_topics": tuple(item for item in payload.critical_topics if not _is_promotional_item(item)),
            "actions_to_take": tuple(item for item in payload.actions_to_take if not _is_promotional_item(item)),
            "watch_items": tuple(item for item in payload.watch_items if not _is_promotional_item(item)),
            "daily_presence": tuple(payload.daily_presence),
            "upcoming_meetings": tuple(payload.upcoming_meetings),
        }
        sentences = []
        for section_name in ("critical_topics", "actions_to_take", "watch_items"):
            items = sections[section_name]
            if not items:
                continue
            sentences.append(self._section_sentence(section_name, items, localized, language))
            if len(sentences) >= 2:
                break
        presence_items = sections["daily_presence"]
        if presence_items and len(sentences) < 2:
            presence_text = _normalize_item_summary(presence_items[0].title, presence_items[0].summary, max_chars=90)
            sentences.append(localized["presence"].format(text=_clean_overview_fragment(presence_text)))
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
        language: str,
    ) -> str:
        first = _overview_item_fragment(items[0], language)
        second = _overview_item_fragment(items[1], language, max_chars=72) if len(items) > 1 else ""
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
        return DigestOverview(summary=_normalize_top_summary(summary), source="llm")

    def _overview_sections(self, payload: DigestPayload) -> Mapping[str, Sequence[DigestEntry]]:
        return {
            "critical_topics": self._compact_overview_items(tuple(item for item in payload.critical_topics if not _is_promotional_item(item))[:1]),
            "actions_to_take": self._compact_overview_items(tuple(item for item in payload.actions_to_take if not _is_promotional_item(item))[:1]),
            "watch_items": self._compact_overview_items(tuple(item for item in payload.watch_items if not _is_promotional_item(item))[:1]),
            "daily_presence": self._compact_overview_items(tuple(payload.daily_presence[:1])),
            "upcoming_meetings": self._compact_overview_items(tuple(payload.upcoming_meetings[:1])),
        }

    def _compact_overview_items(self, items: Sequence[DigestEntry]) -> Sequence[DigestEntry]:
        compacted = []
        for item in items:
            compacted.append(
                _with_digest_entry_updates(
                    item,
                    summary=_normalize_item_summary(item.title, item.summary, max_chars=self._overview_summary_limit(item)),
                    recommended_action=_truncate_sentence(item.recommended_action, max_chars=110),
                    confidence_reason=_truncate_sentence(item.confidence_reason, max_chars=110),
                )
            )
        return tuple(compacted)

    def _overview_summary_limit(self, item: DigestEntry) -> int:
        if item.section_name == "daily_presence":
            return 115
        if item.source_kind == "meeting":
            return 110
        if item.section_name == "critical_topics":
            return 130
        if item.section_name == "actions_to_take":
            return 135
        if item.section_name == "watch_items":
            return 135
        return 135

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
            rewritten_payload = rewritten.get(ref)
            if isinstance(rewritten_payload, str):
                summary = rewritten_payload.strip()
                recommended_action = ""
                confidence_score = item.confidence_score
                confidence_label = item.confidence_label
                confidence_reason = item.confidence_reason
                promotional_label = ""
                promotional_reason = ""
            elif isinstance(rewritten_payload, Mapping):
                summary = str(rewritten_payload.get("summary") or "").strip()
                recommended_action = " ".join(str(rewritten_payload.get("recommended_action") or "").split())
                confidence_score = _confidence_score_bounds(
                    rewritten_payload.get("confidence_score") if rewritten_payload.get("confidence_score") not in (None, "") else item.confidence_score
                )
                confidence_label = str(rewritten_payload.get("confidence_label") or item.confidence_label)
                confidence_reason = _confidence_reason(
                    str(rewritten_payload.get("confidence_reason") or ""),
                    item.confidence_reason,
                )
                promotional_label = " ".join(str(rewritten_payload.get("promotional_label") or "").split()).lower()
                promotional_reason = _promotional_reason(
                    str(rewritten_payload.get("promotional_reason") or ""),
                    getattr(self.provider, "language", "en"),
                )
            else:
                summary = ""
                recommended_action = ""
                confidence_score = item.confidence_score
                confidence_label = item.confidence_label
                confidence_reason = item.confidence_reason
                promotional_label = ""
                promotional_reason = ""
            if not summary:
                updated_items.append(item)
                continue
            reason_codes = list(item.reason_codes)
            context_metadata = dict(item.context_metadata)
            section_name = item.section_name
            handling_bucket = item.handling_bucket
            score = item.score
            final_recommended_action = (
                _truncate_sentence(recommended_action, max_chars=160)
                if recommended_action
                else item.recommended_action
            )
            if item.source_kind == "message":
                if promotional_label == "promotional":
                    reason_codes = [code for code in reason_codes if code != "promotional_candidate"]
                    if "promotional" not in reason_codes:
                        reason_codes.append("promotional")
                    context_metadata["promotional_reason"] = promotional_reason
                    section_name = "watch_items"
                    handling_bucket = "watch_items"
                    score = min(score, 0.8)
                    final_recommended_action = ""
                elif promotional_label in {"not_promotional", "non_promotional"}:
                    reason_codes = [code for code in reason_codes if code != "promotional_candidate"]
            summary = _normalize_item_summary(item.title, summary, max_chars=_item_summary_limit(item))
            updated_items.append(
                _with_digest_entry_updates(
                    item,
                    summary=summary,
                    section_name=section_name,
                    score=score,
                    recommended_action=final_recommended_action,
                    handling_bucket=handling_bucket,
                    confidence_score=confidence_score,
                    confidence_label=_normalized_confidence_label(confidence_label, confidence_score, getattr(self.provider, "language", "en")),
                    confidence_reason=_truncate_sentence(confidence_reason, max_chars=110),
                    reason_codes=tuple(reason_codes),
                    context_metadata=context_metadata,
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
            weather=payload.weather,
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

"""LLM adapters for bounded Day Captain digest wording."""

import json
from typing import Any
from typing import Callable
from typing import Dict
from typing import Mapping
from typing import Optional
from typing import Sequence
from urllib import error
from urllib import request

from day_captain.models import DigestEntry


class LlmProviderError(RuntimeError):
    """Raised when an LLM provider request or response is invalid."""


def _item_ref(item: DigestEntry) -> str:
    return "{0}:{1}".format(item.source_kind, item.source_id)


def _response_text(content: Any) -> str:
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts = []
        for item in content:
            if not isinstance(item, dict):
                continue
            text = item.get("text")
            if isinstance(text, str):
                parts.append(text)
        return "\n".join(part for part in parts if part).strip()
    return ""


class OpenAICompatibleDigestWordingProvider:
    def __init__(
        self,
        api_key: str,
        model: str,
        base_url: str = "https://api.openai.com/v1",
        timeout_seconds: int = 30,
        max_output_tokens: int = 300,
        temperature: float = 0.2,
        language: str = "en",
        style_prompt: str = "Write like a concise executive assistant.",
        opener: Optional[Callable[..., Any]] = None,
    ) -> None:
        self.api_key = api_key
        self.model = model
        self.base_url = base_url.rstrip("/")
        self.timeout_seconds = timeout_seconds
        self.max_output_tokens = max_output_tokens
        self.temperature = temperature
        self.language = (language or "en").strip().lower() or "en"
        self.style_prompt = style_prompt.strip() or "Write like a concise executive assistant."
        self._opener = opener or request.urlopen

    def _supports_custom_temperature(self) -> bool:
        return not self.model.strip().lower().startswith("gpt-5")

    def _reasoning_effort(self) -> Optional[str]:
        if self.model.strip().lower().startswith("gpt-5"):
            return "minimal"
        return None

    def rewrite_summaries(
        self,
        items: Sequence[DigestEntry],
    ) -> Mapping[str, Any]:
        payload = {
            "model": self.model,
            "max_completion_tokens": self.max_output_tokens,
            "response_format": {"type": "json_object"},
            "messages": (
                {
                    "role": "system",
                    "content": (
                        "Generate a short assistant briefing for each digest item. "
                        "Write the output in {0}. "
                        "{1} "
                        "Do not repeat the title at the start of the summary. "
                        "Prefer crisp assistant-style phrasing over compressed raw notes. "
                        "Prefer decision-oriented wording over literal inbox phrasing. "
                        "Keep each summary short and usually under 160 characters when possible. "
                        "For candidate or profile-style messages, keep only the most decision-useful profile signal plus the follow-up. "
                        "Drop greetings, thank-you lead-ins, and sign-offs unless they change the decision. "
                        "Preserve supplier names, internal topic names, and important English business terms when translating them would reduce clarity. "
                        "If the output language is French and the source content is in English, prefer intentional FR-English wording over awkward full translation. "
                        "Preserve facts, urgency, and requested actions. "
                        "Do not invent details. "
                        "Return JSON with an `items` array containing objects with: "
                        "`ref`, `summary`, optional `recommended_action`, optional `confidence_score`, optional `confidence_label`, and optional `confidence_reason`."
                    ).format(
                        "French" if self.language == "fr" else "English",
                        self.style_prompt,
                    ),
                },
                {
                    "role": "user",
                    "content": json.dumps(
                        {
                            "items": [
                                {
                                    "ref": _item_ref(item),
                                    "section_name": item.section_name,
                                    "title": item.title,
                                    "summary": item.summary,
                                    "recommended_action": item.recommended_action,
                                    "handling_bucket": item.handling_bucket or item.section_name,
                                    "confidence_score": item.confidence_score,
                                    "confidence_label": item.confidence_label,
                                    "confidence_reason": item.confidence_reason,
                                    "context_metadata": dict(item.context_metadata),
                                    "reason_codes": list(item.reason_codes),
                                    "guardrail_applied": item.guardrail_applied,
                                }
                                for item in items
                            ]
                        },
                        sort_keys=True,
                    ),
                },
            ),
        }
        reasoning_effort = self._reasoning_effort()
        if reasoning_effort:
            payload["reasoning_effort"] = reasoning_effort
        if self._supports_custom_temperature():
            payload["temperature"] = self.temperature
        raw = self._post_json("{0}/chat/completions".format(self.base_url), payload)
        response_payload = json.loads(raw or "{}")
        if not isinstance(response_payload, dict):
            raise LlmProviderError("Expected JSON object from LLM provider.")
        choices = response_payload.get("choices")
        if not isinstance(choices, list) or not choices:
            raise LlmProviderError("LLM response did not include any choices.")
        first_choice = choices[0]
        if not isinstance(first_choice, dict):
            raise LlmProviderError("LLM choice payload was invalid.")
        message = first_choice.get("message")
        if not isinstance(message, dict):
            raise LlmProviderError("LLM response did not include a message payload.")
        content = _response_text(message.get("content"))
        if not content:
            raise LlmProviderError("LLM response message was empty.")
        try:
            rewritten = json.loads(content)
        except json.JSONDecodeError as exc:
            raise LlmProviderError("LLM content was not valid JSON.") from exc
        if not isinstance(rewritten, dict):
            raise LlmProviderError("LLM content was not a JSON object.")
        result = {}
        for item in rewritten.get("items") or ():
            if not isinstance(item, dict):
                continue
            ref = str(item.get("ref") or "").strip()
            summary = str(item.get("summary") or "").strip()
            if not ref or not summary:
                continue
            result[ref] = {
                "summary": summary,
                "recommended_action": str(item.get("recommended_action") or "").strip(),
                "confidence_score": item.get("confidence_score"),
                "confidence_label": str(item.get("confidence_label") or "").strip(),
                "confidence_reason": str(item.get("confidence_reason") or "").strip(),
            }
        if not result:
            raise LlmProviderError("LLM response did not include any rewritten items.")
        return result

    def summarize_digest(
        self,
        sections: Mapping[str, Sequence[DigestEntry]],
        labels: Mapping[str, str],
        meeting_note: str = "",
    ) -> str:
        payload = {
            "model": self.model,
            "max_completion_tokens": min(self.max_output_tokens, 120),
            "response_format": {"type": "json_object"},
            "messages": (
                {
                    "role": "system",
                    "content": (
                        "Write a short opening digest summary in {0}. "
                        "{1} "
                        "Use 1 to 2 short factual sentences. "
                        "Lead with the single most important action or priority. "
                        "If meetings matter, summarize them briefly without listing every meeting or every attendee. "
                        "If you mention meetings, prefer the nearest one with a concrete day or time and avoid vague phrasing. "
                        "Prefer decision-oriented wording over inbox-style phrasing. "
                        "Avoid unfinished endings, trailing ellipses, or phrases like 'the next one is'. "
                        "Prefer readable names over raw email addresses. "
                        "For candidate or profile-style items, avoid copying long qualification details when a shorter label plus follow-up is enough. "
                        "Drop greetings, thank-you lead-ins, and sign-offs unless they materially change the action. "
                        "Avoid repeating long parenthetical profile details when one shorter label is enough. "
                        "Avoid repeating the exact wording already present in the detailed sections. "
                        "Preserve supplier names, internal topic names, and important English business terms when translating them would reduce clarity. "
                        "If the output language is French and the source content is in English, prefer intentional FR-English wording over awkward full translation. "
                        "Only use the provided digest sections. "
                        "Do not invent details. "
                        "Avoid greetings, sign-offs, bullet points, and markdown. "
                        "Return JSON with a single `summary` string."
                    ).format(
                        "French" if self.language == "fr" else "English",
                        self.style_prompt,
                    ),
                },
                {
                    "role": "user",
                    "content": json.dumps(
                        {
                            "meeting_note": meeting_note,
                            "sections": [
                                {
                                    "name": section_name,
                                    "label": labels.get(section_name, section_name),
                                    "items": [
                                        {
                                            "title": item.title,
                                            "summary": item.summary,
                                            "recommended_action": item.recommended_action,
                                            "confidence_score": item.confidence_score,
                                            "confidence_label": item.confidence_label,
                                            "confidence_reason": item.confidence_reason,
                                        }
                                        for item in items
                                    ],
                                }
                                for section_name, items in sections.items()
                                if items
                            ],
                        },
                        sort_keys=True,
                    ),
                },
            ),
        }
        reasoning_effort = self._reasoning_effort()
        if reasoning_effort:
            payload["reasoning_effort"] = reasoning_effort
        if self._supports_custom_temperature():
            payload["temperature"] = self.temperature
        raw = self._post_json("{0}/chat/completions".format(self.base_url), payload)
        response_payload = json.loads(raw or "{}")
        if not isinstance(response_payload, dict):
            raise LlmProviderError("Expected JSON object from LLM provider.")
        choices = response_payload.get("choices")
        if not isinstance(choices, list) or not choices:
            raise LlmProviderError("LLM response did not include any choices.")
        first_choice = choices[0]
        if not isinstance(first_choice, dict):
            raise LlmProviderError("LLM choice payload was invalid.")
        message = first_choice.get("message")
        if not isinstance(message, dict):
            raise LlmProviderError("LLM response did not include a message payload.")
        content = _response_text(message.get("content"))
        if not content:
            raise LlmProviderError("LLM response message was empty.")
        try:
            summary_payload = json.loads(content)
        except json.JSONDecodeError as exc:
            raise LlmProviderError("LLM content was not valid JSON.") from exc
        if not isinstance(summary_payload, dict):
            raise LlmProviderError("LLM content was not a JSON object.")
        summary = str(summary_payload.get("summary") or "").strip()
        if not summary:
            raise LlmProviderError("LLM response did not include a summary.")
        return summary

    def _post_json(self, url: str, payload: Mapping[str, Any]) -> str:
        body = json.dumps(payload).encode("utf-8")
        req = request.Request(
            url,
            data=body,
            headers={
                "Authorization": "Bearer {0}".format(self.api_key),
                "Content-Type": "application/json",
                "Accept": "application/json",
            },
            method="POST",
        )
        try:
            with self._opener(req, timeout=self.timeout_seconds) as response:
                return response.read().decode("utf-8")
        except error.HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="replace")
            raise LlmProviderError("LLM request failed with {0}: {1}".format(exc.code, detail)) from exc
        except error.URLError as exc:
            raise LlmProviderError("Unable to reach LLM provider: {0}".format(exc.reason)) from exc

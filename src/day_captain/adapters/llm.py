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
        opener: Optional[Callable[..., Any]] = None,
    ) -> None:
        self.api_key = api_key
        self.model = model
        self.base_url = base_url.rstrip("/")
        self.timeout_seconds = timeout_seconds
        self.max_output_tokens = max_output_tokens
        self.temperature = temperature
        self._opener = opener or request.urlopen

    def rewrite_summaries(
        self,
        items: Sequence[DigestEntry],
    ) -> Mapping[str, str]:
        payload = {
            "model": self.model,
            "temperature": self.temperature,
            "max_tokens": self.max_output_tokens,
            "response_format": {"type": "json_object"},
            "messages": (
                {
                    "role": "system",
                    "content": (
                        "Rewrite each digest item summary in one sentence. "
                        "Preserve facts, urgency, and requested actions. "
                        "Do not invent details. Return JSON with an `items` array "
                        "containing `{ref, summary}` objects only."
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
            if ref and summary:
                result[ref] = summary
        if not result:
            raise LlmProviderError("LLM response did not include any rewritten items.")
        return result

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

import json
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from day_captain.adapters.llm import LlmProviderError
from day_captain.adapters.llm import OpenAICompatibleDigestWordingProvider
from day_captain.models import DigestEntry
from day_captain.services import LlmDigestWordingEngine


class _FakeResponse:
    def __init__(self, payload):
        self.payload = payload

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def read(self):
        return json.dumps(self.payload).encode("utf-8")


class OpenAICompatibleDigestWordingProviderTest(unittest.TestCase):
    def test_rewrite_summaries_posts_chat_completion_request(self) -> None:
        captured = {}

        def opener(req, timeout=0):
            captured["url"] = req.full_url
            captured["timeout"] = timeout
            captured["headers"] = dict(req.header_items())
            captured["body"] = json.loads(req.data.decode("utf-8"))
            return _FakeResponse(
                {
                    "choices": [
                        {
                            "message": {
                                "content": json.dumps(
                                    {
                                        "items": [
                                            {
                                                "ref": "message:msg-1",
                                                "summary": "Review the budget before noon because the request is urgent.",
                                            }
                                        ]
                                    }
                                )
                            }
                        }
                    ]
                }
            )

        provider = OpenAICompatibleDigestWordingProvider(
            api_key="sk-test",
            model="gpt-5-mini",
            style_prompt="Write like my chief of staff.",
            opener=opener,
        )

        rewritten = provider.rewrite_summaries(
            (
                DigestEntry(
                    title="Urgent budget review",
                    summary="Critical: Please review before noon.",
                    section_name="critical_topics",
                    source_kind="message",
                    source_id="msg-1",
                    score=3.0,
                    reason_codes=("critical_keyword",),
                    guardrail_applied=True,
                ),
            )
        )

        self.assertEqual(captured["url"], "https://api.openai.com/v1/chat/completions")
        self.assertEqual(captured["timeout"], 30)
        self.assertEqual(captured["headers"]["Authorization"], "Bearer sk-test")
        self.assertEqual(captured["body"]["model"], "gpt-5-mini")
        self.assertEqual(captured["body"]["messages"][1]["role"], "user")
        self.assertIn("chief of staff", captured["body"]["messages"][0]["content"])
        self.assertEqual(
            rewritten["message:msg-1"],
            "Review the budget before noon because the request is urgent.",
        )

    def test_rewrite_summaries_rejects_malformed_provider_content(self) -> None:
        provider = OpenAICompatibleDigestWordingProvider(
            api_key="sk-test",
            model="gpt-5-mini",
            opener=lambda req, timeout=0: _FakeResponse({"choices": [{"message": {"content": "not-json"}}]}),
        )

        with self.assertRaises((LlmProviderError, json.JSONDecodeError)):
            provider.rewrite_summaries(
                (
                    DigestEntry(
                        title="Urgent budget review",
                        summary="Critical: Please review before noon.",
                        section_name="critical_topics",
                        source_kind="message",
                        source_id="msg-1",
                        score=3.0,
                    ),
                )
            )


class LlmDigestWordingEngineTest(unittest.TestCase):
    def test_rewrite_updates_only_shortlisted_items(self) -> None:
        provider = type(
            "Provider",
            (),
            {
                "rewrite_summaries": lambda self, items: {
                    "message:msg-1": "Polished summary one.",
                    "message:msg-2": "Polished summary two.",
                }
            },
        )()
        engine = LlmDigestWordingEngine(provider=provider, shortlist_limit=2)
        items = (
            DigestEntry(
                title="First",
                summary="Original one",
                section_name="critical_topics",
                source_kind="message",
                source_id="msg-1",
                score=3.0,
            ),
            DigestEntry(
                title="Second",
                summary="Original two",
                section_name="actions_to_take",
                source_kind="message",
                source_id="msg-2",
                score=2.0,
            ),
            DigestEntry(
                title="Third",
                summary="Original three",
                section_name="watch_items",
                source_kind="message",
                source_id="msg-3",
                score=1.0,
            ),
        )

        rewritten = engine.rewrite(items)

        self.assertEqual(rewritten[0].summary, "Polished summary one.")
        self.assertEqual(rewritten[1].summary, "Polished summary two.")
        self.assertEqual(rewritten[2].summary, "Original three")

    def test_rewrite_only_targets_enabled_sections(self) -> None:
        provider = type(
            "Provider",
            (),
            {
                "rewrite_summaries": lambda self, items: {
                    "message:msg-1": "Polished summary one.",
                }
            },
        )()
        engine = LlmDigestWordingEngine(
            provider=provider,
            shortlist_limit=2,
            enabled_sections=("critical_topics",),
        )
        items = (
            DigestEntry(
                title="First",
                summary="Original one",
                section_name="critical_topics",
                source_kind="message",
                source_id="msg-1",
                score=3.0,
            ),
            DigestEntry(
                title="Second",
                summary="Original two",
                section_name="watch_items",
                source_kind="message",
                source_id="msg-2",
                score=2.0,
            ),
        )

        rewritten = engine.rewrite(items)

        self.assertEqual(rewritten[0].summary, "Polished summary one.")
        self.assertEqual(rewritten[1].summary, "Original two")

    def test_rewrite_falls_back_when_provider_fails(self) -> None:
        provider = type(
            "Provider",
            (),
            {
                "rewrite_summaries": lambda self, items: (_ for _ in ()).throw(RuntimeError("boom")),
            },
        )()
        engine = LlmDigestWordingEngine(provider=provider, shortlist_limit=2)
        items = (
            DigestEntry(
                title="First",
                summary="Original one",
                section_name="critical_topics",
                source_kind="message",
                source_id="msg-1",
                score=3.0,
            ),
        )

        rewritten = engine.rewrite(items)

        self.assertEqual(rewritten, items)

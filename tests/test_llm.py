import json
from datetime import datetime
from datetime import timezone
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from day_captain.adapters.llm import LlmProviderError
from day_captain.adapters.llm import OpenAICompatibleDigestWordingProvider
from day_captain.models import DigestEntry
from day_captain.models import DigestPayload
from day_captain.services import DeterministicDigestOverviewEngine
from day_captain.services import LlmDigestWordingEngine
from day_captain.services import LlmDigestOverviewEngine


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
            language="fr",
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
        self.assertEqual(captured["body"]["reasoning_effort"], "minimal")
        self.assertEqual(captured["body"]["messages"][1]["role"], "user")
        self.assertNotIn("temperature", captured["body"])
        self.assertIn("chief of staff", captured["body"]["messages"][0]["content"])
        self.assertIn("French", captured["body"]["messages"][0]["content"])
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

    def test_summarize_digest_posts_bounded_summary_request(self) -> None:
        captured = {}

        def opener(req, timeout=0):
            captured["url"] = req.full_url
            captured["timeout"] = timeout
            captured["body"] = json.loads(req.data.decode("utf-8"))
            return _FakeResponse(
                {
                    "choices": [
                        {
                            "message": {
                                "content": json.dumps(
                                    {
                                        "summary": "Budget review is the main priority, with roadmap follow-up next."
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
            language="en",
            opener=opener,
        )

        summary = provider.summarize_digest(
            sections={
                "critical_topics": (
                    DigestEntry(
                        title="Urgent budget review",
                        summary="Critical: Please review before noon.",
                        section_name="critical_topics",
                        source_kind="message",
                        source_id="msg-1",
                        score=3.0,
                    ),
                ),
                "actions_to_take": (
                    DigestEntry(
                        title="Roadmap update",
                        summary="Need your input for planning.",
                        section_name="actions_to_take",
                        source_kind="message",
                        source_id="msg-2",
                        score=2.0,
                    ),
                ),
            },
            labels={"critical_topics": "Critical topics", "actions_to_take": "Actions to take"},
        )

        self.assertEqual(captured["url"], "https://api.openai.com/v1/chat/completions")
        self.assertEqual(captured["timeout"], 30)
        self.assertEqual(captured["body"]["max_completion_tokens"], 120)
        self.assertEqual(captured["body"]["reasoning_effort"], "minimal")
        self.assertNotIn("temperature", captured["body"])
        self.assertIn("2 to 4 short factual sentences", captured["body"]["messages"][0]["content"])
        self.assertEqual(
            summary,
            "Budget review is the main priority, with roadmap follow-up next.",
        )

    def test_non_gpt5_models_keep_custom_temperature(self) -> None:
        captured = {}

        def opener(req, timeout=0):
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
            model="gpt-4o-mini",
            temperature=0.2,
            opener=opener,
        )

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

        self.assertEqual(captured["body"]["temperature"], 0.2)
        self.assertNotIn("reasoning_effort", captured["body"])


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


class DigestOverviewEngineTest(unittest.TestCase):
    def test_llm_summary_uses_provider_output_when_available(self) -> None:
        payload = DigestPayload(
            run_id="run-1",
            generated_at=datetime(2026, 3, 7, 8, 0, tzinfo=timezone.utc),
            window_start=datetime(2026, 3, 6, 8, 0, tzinfo=timezone.utc),
            window_end=datetime(2026, 3, 7, 8, 0, tzinfo=timezone.utc),
            delivery_mode="json",
            delivery_payload={"digest_language": "en"},
            actions_to_take=(
                DigestEntry(
                    title="Roadmap update",
                    summary="Need your input for planning.",
                    section_name="actions_to_take",
                    source_kind="message",
                    source_id="msg-2",
                    score=2.0,
                ),
            ),
        )
        provider = type(
            "Provider",
            (),
            {"summarize_digest": lambda self, sections, labels: "Roadmap follow-up is the main action for today."},
        )()

        overview = LlmDigestOverviewEngine(provider=provider).summarize(payload)

        self.assertEqual(overview.source, "llm")
        self.assertEqual(overview.summary, "Roadmap follow-up is the main action for today.")

    def test_deterministic_summary_uses_final_sections(self) -> None:
        payload = DigestPayload(
            run_id="run-1",
            generated_at=datetime(2026, 3, 7, 8, 0, tzinfo=timezone.utc),
            window_start=datetime(2026, 3, 6, 8, 0, tzinfo=timezone.utc),
            window_end=datetime(2026, 3, 7, 8, 0, tzinfo=timezone.utc),
            delivery_mode="json",
            delivery_payload={"digest_language": "en"},
            critical_topics=(
                DigestEntry(
                    title="Urgent budget review",
                    summary="Critical: Please review before noon.",
                    section_name="critical_topics",
                    source_kind="message",
                    source_id="msg-1",
                    score=3.0,
                ),
            ),
            upcoming_meetings=(
                DigestEntry(
                    title="Leadership sync",
                    summary="Today at 10:00 with ceo@example.com",
                    section_name="upcoming_meetings",
                    source_kind="meeting",
                    source_id="mtg-1",
                    score=2.0,
                ),
            ),
        )

        overview = DeterministicDigestOverviewEngine().summarize(payload)

        self.assertEqual(overview.source, "deterministic")
        self.assertIn("Top priority: Urgent budget review.", overview.summary)
        self.assertIn("Upcoming meeting: Today at 10:00 with ceo@example.com.", overview.summary)

    def test_llm_summary_falls_back_to_deterministic_summary(self) -> None:
        payload = DigestPayload(
            run_id="run-1",
            generated_at=datetime(2026, 3, 7, 8, 0, tzinfo=timezone.utc),
            window_start=datetime(2026, 3, 6, 8, 0, tzinfo=timezone.utc),
            window_end=datetime(2026, 3, 7, 8, 0, tzinfo=timezone.utc),
            delivery_mode="json",
            delivery_payload={"digest_language": "fr"},
            actions_to_take=(
                DigestEntry(
                    title="A imprimer",
                    summary="Bonjour, Voici notre logo en pj.",
                    section_name="actions_to_take",
                    source_kind="message",
                    source_id="msg-2",
                    score=2.0,
                ),
            ),
        )
        provider = type(
            "Provider",
            (),
            {"summarize_digest": lambda self, sections, labels: (_ for _ in ()).throw(RuntimeError("boom"))},
        )()

        overview = LlmDigestOverviewEngine(provider=provider).summarize(payload)

        self.assertEqual(overview.source, "deterministic")
        self.assertIn("Suivi principal", overview.summary)

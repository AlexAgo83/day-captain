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
        self.assertIn("Do not repeat the title at the start of the summary", captured["body"]["messages"][0]["content"])
        self.assertIn("under 160 characters", captured["body"]["messages"][0]["content"])
        self.assertIn("candidate or profile-style messages", captured["body"]["messages"][0]["content"])
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
        self.assertIn("Use 1 to 2 short factual sentences", captured["body"]["messages"][0]["content"])
        self.assertIn("avoid vague phrasing", captured["body"]["messages"][0]["content"])
        self.assertIn("Avoid unfinished endings", captured["body"]["messages"][0]["content"])
        self.assertIn("candidate or profile-style items", captured["body"]["messages"][0]["content"])
        self.assertIn("Prefer readable names over raw email addresses", captured["body"]["messages"][0]["content"])
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

    def test_rewrite_cleans_redundant_title_prefix_and_long_summary(self) -> None:
        provider = type(
            "Provider",
            (),
            {
                "rewrite_summaries": lambda self, items: {
                    "message:msg-1": (
                        "Candidature spontanée : diplômé d'un bachelor en design transport et d'un master en design urbain, "
                        "actuellement designer chez Studio Meridian depuis plus de 4 ans, cherche une nouvelle opportunité. "
                        "Action attendue : examiner la candidature ou proposer un suivi."
                    ),
                }
            },
        )()
        engine = LlmDigestWordingEngine(provider=provider, shortlist_limit=1)
        items = (
            DigestEntry(
                title="Candidature spontanée - Designer",
                summary="Original",
                section_name="watch_items",
                source_kind="message",
                source_id="msg-1",
                score=1.0,
            ),
        )

        rewritten = engine.rewrite(items)

        self.assertNotIn("Candidature spontanée :", rewritten[0].summary)
        self.assertIn("Suivi :", rewritten[0].summary)
        self.assertLessEqual(len(rewritten[0].summary), 183)


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
            {
                "summarize_digest": (
                    lambda self, sections, labels, meeting_note="": "Roadmap follow-up is the main action for today."
                )
            },
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
            {
                "summarize_digest": (
                    lambda self, sections, labels, meeting_note="": (_ for _ in ()).throw(RuntimeError("boom"))
                )
            },
        )()

        overview = LlmDigestOverviewEngine(provider=provider).summarize(payload)

        self.assertEqual(overview.source, "deterministic")
        self.assertIn("Suivi principal", overview.summary)

    def test_llm_summary_limits_meeting_input_and_passes_meeting_note(self) -> None:
        payload = DigestPayload(
            run_id="run-1",
            generated_at=datetime(2026, 3, 7, 8, 0, tzinfo=timezone.utc),
            window_start=datetime(2026, 3, 6, 8, 0, tzinfo=timezone.utc),
            window_end=datetime(2026, 3, 7, 8, 0, tzinfo=timezone.utc),
            delivery_mode="json",
            delivery_payload={"digest_language": "fr"},
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
            upcoming_meetings=(
                DigestEntry(
                    title="Point équipe",
                    summary="lun. 09 mars à 10:00 avec Morgan Lee sur Teams",
                    section_name="upcoming_meetings",
                    source_kind="meeting",
                    source_id="mtg-1",
                    score=2.0,
                ),
                DigestEntry(
                    title="Daily Meeting",
                    summary="lun. 09 mars à 11:30 avec Project Author sur Teams",
                    section_name="upcoming_meetings",
                    source_kind="meeting",
                    source_id="mtg-2",
                    score=1.5,
                ),
            ),
        )
        captured = {}

        class Provider:
            def summarize_digest(self, sections, labels, meeting_note=""):
                captured["sections"] = sections
                captured["labels"] = labels
                captured["meeting_note"] = meeting_note
                return "Résumé court."

        overview = LlmDigestOverviewEngine(provider=Provider()).summarize(payload)

        self.assertEqual(overview.source, "llm")
        self.assertEqual(
            captured["meeting_note"],
            "2 réunions sont prévues. Résume-les brièvement sans toutes les lister. Si elles sont demain ou lundi, dis-le ainsi plutôt que 'la semaine prochaine'. Si tu mentionnes une réunion, cite la plus proche avec un horaire concret et évite les formulations vagues.",
        )
        self.assertEqual(len(captured["sections"]["upcoming_meetings"]), 1)

    def test_llm_summary_compacts_verbose_watch_item_before_prompt(self) -> None:
        payload = DigestPayload(
            run_id="run-1",
            generated_at=datetime(2026, 3, 9, 8, 0, tzinfo=timezone.utc),
            window_start=datetime(2026, 3, 8, 8, 0, tzinfo=timezone.utc),
            window_end=datetime(2026, 3, 9, 8, 0, tzinfo=timezone.utc),
            delivery_mode="json",
            delivery_payload={"digest_language": "fr"},
            watch_items=(
                DigestEntry(
                    title="Candidature spontanée - Designer",
                    summary=(
                        "Candidature spontanée : diplômé d'un bachelor en design transport et d'un master en design urbain, "
                        "actuellement designer chez Studio Meridian depuis plus de 4 ans, cherche une nouvelle opportunité. "
                        "Action attendue : examiner la candidature ou proposer un suivi."
                    ),
                    section_name="watch_items",
                    source_kind="message",
                    source_id="msg-1",
                    score=1.0,
                ),
            ),
        )
        captured = {}

        class Provider:
            def summarize_digest(self, sections, labels, meeting_note=""):
                captured["sections"] = sections
                return "Résumé court."

        overview = LlmDigestOverviewEngine(provider=Provider()).summarize(payload)

        self.assertEqual(overview.source, "llm")
        self.assertEqual(len(captured["sections"]["watch_items"]), 1)
        self.assertNotIn("Candidature spontanée :", captured["sections"]["watch_items"][0].summary)
        self.assertIn("Suivi :", captured["sections"]["watch_items"][0].summary)
        self.assertLessEqual(len(captured["sections"]["watch_items"][0].summary), 123)

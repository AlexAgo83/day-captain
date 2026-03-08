from pathlib import Path
import io
import json
import sys
import unittest
from urllib import error

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from day_captain.hosted_jobs import HostedJobError
from day_captain.hosted_jobs import build_job_payload
from day_captain.hosted_jobs import check_hosted_health
from day_captain.hosted_jobs import trigger_hosted_job
from day_captain.hosted_jobs import validate_hosted_service


class FakeResponse:
    def __init__(self, payload, status=200):
        self.payload = payload
        self.status = status

    def read(self):
        return json.dumps(self.payload).encode("utf-8")

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False


class HostedJobRecorder:
    def __init__(self, payload, status=200):
        self.payload = payload
        self.status = status
        self.requests = []

    def __call__(self, req, timeout=0):
        self.requests.append(
            {
                "url": req.full_url,
                "body": req.data.decode("utf-8") if req.data else "",
                "secret": req.headers.get("X-day-captain-secret"),
                "content_type": req.headers.get("Content-type"),
                "timeout": timeout,
            }
        )
        return FakeResponse(self.payload, status=self.status)


class HostedJobsTest(unittest.TestCase):
    def test_check_hosted_health_reads_healthz(self) -> None:
        recorder = HostedJobRecorder({"status": "ok"})

        result = check_hosted_health(
            "https://example.com",
            timeout_seconds=10,
            opener=recorder,
        )

        self.assertEqual(result["status"], "ok")
        self.assertEqual(recorder.requests[0]["url"], "https://example.com/healthz")

    def test_build_job_payload_for_morning_digest(self) -> None:
        payload = build_job_payload(
            "morning-digest",
            force=True,
            target_user_id="alice@example.com",
            delivery_mode="graph_send",
            now="2026-03-08T08:00:00+00:00",
        )

        self.assertEqual(
            payload,
            {
                "force": True,
                "delivery_mode": "graph_send",
                "now": "2026-03-08T08:00:00+00:00",
                "target_user_id": "alice@example.com",
            },
        )

    def test_build_job_payload_for_recall_digest(self) -> None:
        payload = build_job_payload(
            "recall-digest",
            run_id="run-123",
            day="2026-03-08",
            target_user_id="alice@example.com",
        )

        self.assertEqual(
            payload,
            {
                "run_id": "run-123",
                "day": "2026-03-08",
                "target_user_id": "alice@example.com",
            },
        )

    def test_trigger_hosted_job_posts_expected_payload(self) -> None:
        recorder = HostedJobRecorder(
            {
                "status": "completed",
                "job": "morning_digest",
                "run_id": "run-1",
                "generated_at": "2026-03-08T08:00:00+00:00",
                "delivery_mode": "json",
                "section_counts": {
                    "critical_topics": 0,
                    "actions_to_take": 0,
                    "watch_items": 0,
                    "upcoming_meetings": 0,
                },
            }
        )

        result = trigger_hosted_job(
            "https://example.com",
            "secret",
            job_name="morning-digest",
            payload={"force": False, "target_user_id": "alice@example.com"},
            timeout_seconds=15,
            opener=recorder,
        )

        self.assertEqual(result["status"], "ok")
        self.assertEqual(result["status_code"], 200)
        self.assertEqual(result["response"]["run_id"], "run-1")
        self.assertEqual(recorder.requests[0]["url"], "https://example.com/jobs/morning-digest")
        self.assertEqual(
            json.loads(recorder.requests[0]["body"]),
            {"force": False, "target_user_id": "alice@example.com"},
        )
        self.assertEqual(recorder.requests[0]["secret"], "secret")
        self.assertEqual(recorder.requests[0]["timeout"], 15)

    def test_trigger_hosted_job_raises_for_http_errors(self) -> None:
        def failing_opener(req, timeout=0):
            raise error.HTTPError(
                url=req.full_url,
                code=500,
                msg="error",
                hdrs=None,
                fp=io.BytesIO(b'{"error":"internal_error"}'),
            )

        with self.assertRaises(HostedJobError):
            trigger_hosted_job(
                "https://example.com",
                "secret",
                payload={"force": False},
                opener=failing_opener,
            )

    def test_trigger_hosted_job_raises_for_invalid_ack_shape(self) -> None:
        recorder = HostedJobRecorder({"status": "completed", "run_id": "run-1"})

        with self.assertRaises(HostedJobError):
            trigger_hosted_job(
                "https://example.com",
                "secret",
                payload={"force": False},
                opener=recorder,
            )

    def test_validate_hosted_service_runs_health_morning_and_recall(self) -> None:
        payloads = [
            {"status": "ok"},
            {
                "status": "completed",
                "job": "morning_digest",
                "run_id": "run-1",
                "generated_at": "2026-03-08T08:00:00+00:00",
                "delivery_mode": "json",
                "section_counts": {
                    "critical_topics": 1,
                    "actions_to_take": 0,
                    "watch_items": 0,
                    "upcoming_meetings": 0,
                },
            },
            {
                "status": "completed",
                "job": "recall_digest",
                "run_id": "run-1",
                "generated_at": "2026-03-08T08:01:00+00:00",
                "delivery_mode": "json",
                "section_counts": {
                    "critical_topics": 1,
                    "actions_to_take": 0,
                    "watch_items": 0,
                    "upcoming_meetings": 0,
                },
            },
        ]

        class SequenceRecorder:
            def __init__(self):
                self.requests = []

            def __call__(self, req, timeout=0):
                self.requests.append((req.full_url, req.data.decode("utf-8") if req.data else ""))
                return FakeResponse(payloads.pop(0), status=200)

        recorder = SequenceRecorder()
        result = validate_hosted_service(
            "https://example.com",
            "secret",
            target_user_id="alice@example.com",
            opener=recorder,
        )

        self.assertEqual(result["status"], "ok")
        self.assertEqual(recorder.requests[0][0], "https://example.com/healthz")
        self.assertEqual(recorder.requests[1][0], "https://example.com/jobs/morning-digest")
        self.assertEqual(recorder.requests[2][0], "https://example.com/jobs/recall-digest")
        self.assertEqual(json.loads(recorder.requests[2][1])["run_id"], "run-1")

    def test_validate_hosted_service_raises_when_recall_run_id_differs(self) -> None:
        payloads = [
            {"status": "ok"},
            {
                "status": "completed",
                "job": "morning_digest",
                "run_id": "run-1",
                "generated_at": "2026-03-08T08:00:00+00:00",
                "delivery_mode": "json",
                "section_counts": {
                    "critical_topics": 0,
                    "actions_to_take": 0,
                    "watch_items": 0,
                    "upcoming_meetings": 0,
                },
            },
            {
                "status": "completed",
                "job": "recall_digest",
                "run_id": "run-2",
                "generated_at": "2026-03-08T08:01:00+00:00",
                "delivery_mode": "json",
                "section_counts": {
                    "critical_topics": 0,
                    "actions_to_take": 0,
                    "watch_items": 0,
                    "upcoming_meetings": 0,
                },
            },
        ]

        class SequenceRecorder:
            def __call__(self, req, timeout=0):
                return FakeResponse(payloads.pop(0), status=200)

        with self.assertRaises(HostedJobError):
            validate_hosted_service(
                "https://example.com",
                "secret",
                target_user_id="alice@example.com",
                opener=SequenceRecorder(),
            )


if __name__ == "__main__":
    unittest.main()

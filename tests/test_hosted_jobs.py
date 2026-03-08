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
from day_captain.hosted_jobs import wait_for_hosted_health


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

    def test_check_hosted_health_validates_runtime_summary(self) -> None:
        recorder = HostedJobRecorder(
            {
                "status": "ok",
                "runtime": {
                    "status": "ok",
                    "graph_auth_mode": "app_only",
                    "storage_backend": "postgres",
                    "configured_target_user_count": 1,
                    "database_configured": True,
                },
            }
        )

        result = check_hosted_health(
            "https://example.com",
            job_secret="secret",
            include_runtime_summary=True,
            expected_graph_auth_mode="app_only",
            expected_storage_backend="postgres",
            opener=recorder,
        )

        self.assertEqual(result["runtime"]["graph_auth_mode"], "app_only")
        self.assertEqual(recorder.requests[0]["secret"], "secret")

    def test_wait_for_hosted_health_retries_until_ready(self) -> None:
        calls = []
        sleeps = []

        def delayed_health(req, timeout=0):
            calls.append(req.full_url)
            if len(calls) < 3:
                raise error.URLError("warming up")
            return FakeResponse({"status": "ok"}, status=200)

        result = wait_for_hosted_health(
            "https://example.com",
            timeout_seconds=20,
            max_attempts=3,
            delay_seconds=5,
            opener=delayed_health,
            sleeper=sleeps.append,
        )

        self.assertEqual(result["status"], "ok")
        self.assertEqual(result["attempt_count"], 3)
        self.assertTrue(result["warmed_up"])
        self.assertEqual(sleeps, [5, 5])

    def test_wait_for_hosted_health_raises_when_service_never_wakes(self) -> None:
        sleeps = []

        def failing_health(req, timeout=0):
            raise error.URLError("still asleep")

        with self.assertRaises(HostedJobError):
            wait_for_hosted_health(
                "https://example.com",
                timeout_seconds=20,
                max_attempts=2,
                delay_seconds=7,
                opener=failing_health,
                sleeper=sleeps.append,
            )

        self.assertEqual(sleeps, [7])

    def test_wait_for_hosted_health_retries_after_timeout(self) -> None:
        calls = []
        sleeps = []

        def delayed_health(req, timeout=0):
            calls.append(timeout)
            if len(calls) < 3:
                raise TimeoutError("timed out")
            return FakeResponse({"status": "ok"}, status=200)

        result = wait_for_hosted_health(
            "https://example.com",
            timeout_seconds=15,
            max_attempts=3,
            delay_seconds=4,
            opener=delayed_health,
            sleeper=sleeps.append,
        )

        self.assertEqual(result["status"], "ok")
        self.assertEqual(result["attempt_count"], 3)
        self.assertEqual(calls, [15, 15, 15])
        self.assertEqual(sleeps, [4, 4])

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

    def test_build_job_payload_for_email_command_recall(self) -> None:
        payload = build_job_payload(
            "email-command-recall",
            command_message_id="cmd-1",
            sender_address="alice@example.com",
            command_text="recall",
            now="2026-03-11T10:00:00+00:00",
        )

        self.assertEqual(
            payload,
            {
                "command_message_id": "cmd-1",
                "sender_address": "alice@example.com",
                "command_text": "recall",
                "now": "2026-03-11T10:00:00+00:00",
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

    def test_trigger_hosted_job_can_wake_service_first(self) -> None:
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
        ]

        class SequenceRecorder:
            def __init__(self):
                self.requests = []

            def __call__(self, req, timeout=0):
                self.requests.append((req.full_url, timeout, req.data.decode("utf-8") if req.data else ""))
                return FakeResponse(payloads.pop(0), status=200)

        recorder = SequenceRecorder()
        result = trigger_hosted_job(
            "https://example.com",
            "secret",
            job_name="morning-digest",
            payload={"force": False},
            timeout_seconds=90,
            wake_service=True,
            wake_timeout_seconds=45,
            wake_max_attempts=2,
            wake_delay_seconds=5,
            opener=recorder,
            sleeper=lambda _: None,
        )

        self.assertEqual(result["status"], "ok")
        self.assertEqual(result["warmup"]["attempt_count"], 1)
        self.assertEqual(recorder.requests[0][0], "https://example.com/healthz")
        self.assertEqual(recorder.requests[0][1], 45)
        self.assertEqual(recorder.requests[1][0], "https://example.com/jobs/morning-digest")
        self.assertEqual(recorder.requests[1][1], 90)

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
            {
                "status": "ok",
            },
            {
                "status": "ok",
                "runtime": {
                    "status": "ok",
                    "graph_auth_mode": "app_only",
                    "storage_backend": "postgres",
                    "configured_target_user_count": 1,
                    "database_configured": True,
                },
            },
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
            expected_graph_auth_mode="app_only",
            expected_storage_backend="postgres",
            wake_service=True,
            wake_timeout_seconds=45,
            wake_max_attempts=3,
            wake_delay_seconds=10,
            opener=recorder,
            sleeper=lambda _: None,
        )

        self.assertEqual(result["status"], "ok")
        self.assertEqual(result["warmup"]["attempt_count"], 1)
        self.assertEqual(result["runtime"]["storage_backend"], "postgres")
        self.assertEqual(recorder.requests[0][0], "https://example.com/healthz")
        self.assertEqual(recorder.requests[1][0], "https://example.com/healthz")
        self.assertEqual(recorder.requests[2][0], "https://example.com/jobs/morning-digest")
        self.assertEqual(recorder.requests[3][0], "https://example.com/jobs/recall-digest")
        self.assertEqual(json.loads(recorder.requests[3][1])["run_id"], "run-1")

    def test_validate_hosted_service_raises_when_recall_run_id_differs(self) -> None:
        payloads = [
            {
                "status": "ok",
                "runtime": {
                    "status": "ok",
                    "graph_auth_mode": "app_only",
                    "storage_backend": "postgres",
                    "configured_target_user_count": 1,
                    "database_configured": True,
                },
            },
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
                expected_graph_auth_mode="app_only",
                expected_storage_backend="postgres",
                opener=SequenceRecorder(),
            )


if __name__ == "__main__":
    unittest.main()

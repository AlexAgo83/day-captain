"""Helpers for triggering hosted Day Captain jobs from external automation."""

import json
import socket
import time
from typing import Any
from typing import Callable
from typing import Mapping
from typing import Optional
from urllib import error
from urllib import request


class HostedJobError(RuntimeError):
    """Raised when a hosted Day Captain job cannot be triggered safely."""


def _normalized_service_url(service_url: str) -> str:
    normalized = str(service_url or "").rstrip("/")
    if not normalized:
        raise HostedJobError("service_url is required.")
    return normalized


def _normalized_job_secret(job_secret: str) -> str:
    normalized = str(job_secret or "").strip()
    if not normalized:
        raise HostedJobError("job_secret is required.")
    return normalized


def _validate_job_ack(payload: Mapping[str, Any], expected_job_name: str) -> Mapping[str, Any]:
    status = str(payload.get("status") or "").strip()
    job = str(payload.get("job") or "").strip()
    run_id = str(payload.get("run_id") or "").strip()
    generated_at = str(payload.get("generated_at") or "").strip()
    delivery_mode = str(payload.get("delivery_mode") or "").strip()
    section_counts = payload.get("section_counts")

    if status != "completed":
        raise HostedJobError("Hosted job acknowledgement did not report status=completed.")
    if job != expected_job_name.replace("-", "_"):
        raise HostedJobError("Hosted job acknowledgement reported unexpected job name.")
    if not run_id:
        raise HostedJobError("Hosted job acknowledgement did not include run_id.")
    if not generated_at:
        raise HostedJobError("Hosted job acknowledgement did not include generated_at.")
    if not delivery_mode:
        raise HostedJobError("Hosted job acknowledgement did not include delivery_mode.")
    if not isinstance(section_counts, dict):
        raise HostedJobError("Hosted job acknowledgement did not include section_counts.")
    required_sections = ("critical_topics", "actions_to_take", "watch_items", "upcoming_meetings")
    for section_name in required_sections:
        if section_name not in section_counts:
            raise HostedJobError("Hosted job acknowledgement is missing section count `{0}`.".format(section_name))
    return payload


def _validate_runtime_summary(
    payload: Mapping[str, Any],
    *,
    expected_graph_auth_mode: str = "",
    expected_storage_backend: str = "",
) -> Mapping[str, Any]:
    status = str(payload.get("status") or "").strip()
    if status != "ok":
        raise HostedJobError("Hosted runtime summary did not report status=ok.")
    storage_backend = str(payload.get("storage_backend") or "").strip()
    if storage_backend not in {"postgres", "sqlite"}:
        raise HostedJobError("Hosted runtime summary did not include a valid storage_backend.")
    graph_auth_mode = str(payload.get("graph_auth_mode") or "").strip()
    if graph_auth_mode not in {"delegated", "app_only"}:
        raise HostedJobError("Hosted runtime summary did not include a valid graph_auth_mode.")
    configured_target_user_count = payload.get("configured_target_user_count")
    if not isinstance(configured_target_user_count, int):
        raise HostedJobError("Hosted runtime summary did not include configured_target_user_count.")
    if "database_configured" not in payload:
        raise HostedJobError("Hosted runtime summary did not include database_configured.")
    if expected_graph_auth_mode and graph_auth_mode != expected_graph_auth_mode:
        raise HostedJobError(
            "Hosted runtime summary reported graph_auth_mode={0}, expected {1}.".format(
                graph_auth_mode,
                expected_graph_auth_mode,
            )
        )
    if expected_storage_backend and storage_backend != expected_storage_backend:
        raise HostedJobError(
            "Hosted runtime summary reported storage_backend={0}, expected {1}.".format(
                storage_backend,
                expected_storage_backend,
            )
        )
    return payload


def check_hosted_health(
    service_url: str,
    *,
    job_secret: str = "",
    include_runtime_summary: bool = False,
    expected_graph_auth_mode: str = "",
    expected_storage_backend: str = "",
    timeout_seconds: int = 30,
    opener: Optional[Callable[..., Any]] = None,
) -> Mapping[str, Any]:
    normalized_service_url = _normalized_service_url(service_url)
    opener = opener or request.urlopen
    url = "{0}/healthz".format(normalized_service_url)
    headers = {"Accept": "application/json"}
    if include_runtime_summary:
        headers["X-Day-Captain-Secret"] = _normalized_job_secret(job_secret)
    req = request.Request(
        url,
        headers=headers,
        method="GET",
    )
    try:
        with opener(req, timeout=timeout_seconds) as response:
            raw = response.read().decode("utf-8")
            status_code = int(getattr(response, "status", 200))
    except error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise HostedJobError("Hosted healthcheck failed with {0}: {1}".format(exc.code, detail)) from exc
    except error.URLError as exc:
        raise HostedJobError("Unable to reach hosted Day Captain service: {0}".format(exc.reason)) from exc
    except (TimeoutError, socket.timeout) as exc:
        raise HostedJobError("Hosted healthcheck timed out after {0} second(s).".format(timeout_seconds)) from exc
    try:
        payload = json.loads(raw or "{}")
    except json.JSONDecodeError:
        payload = {"raw_response": raw}
    if status_code != 200:
        raise HostedJobError("Hosted healthcheck returned unexpected status {0}.".format(status_code))
    if payload.get("status") != "ok":
        raise HostedJobError("Hosted healthcheck did not return status=ok.")
    runtime_summary = None
    if include_runtime_summary:
        runtime_payload = payload.get("runtime")
        if not isinstance(runtime_payload, dict):
            raise HostedJobError("Hosted healthcheck did not include runtime summary.")
        runtime_summary = _validate_runtime_summary(
            runtime_payload,
            expected_graph_auth_mode=expected_graph_auth_mode,
            expected_storage_backend=expected_storage_backend,
        )
    return {
        "status": "ok",
        "url": url,
        "status_code": status_code,
        "response": payload,
        "runtime": runtime_summary,
    }


def wait_for_hosted_health(
    service_url: str,
    *,
    job_secret: str = "",
    include_runtime_summary: bool = False,
    expected_graph_auth_mode: str = "",
    expected_storage_backend: str = "",
    timeout_seconds: int = 30,
    max_attempts: int = 1,
    delay_seconds: int = 0,
    opener: Optional[Callable[..., Any]] = None,
    sleeper: Optional[Callable[[float], None]] = None,
) -> Mapping[str, Any]:
    attempts = max(1, int(max_attempts))
    delay = max(0, int(delay_seconds))
    sleeper = sleeper or time.sleep
    last_error = ""

    for attempt_index in range(1, attempts + 1):
        try:
            result = check_hosted_health(
                service_url,
                job_secret=job_secret,
                include_runtime_summary=include_runtime_summary,
                expected_graph_auth_mode=expected_graph_auth_mode,
                expected_storage_backend=expected_storage_backend,
                timeout_seconds=timeout_seconds,
                opener=opener,
            )
            return {
                "status": "ok",
                "attempt_count": attempt_index,
                "warmed_up": attempt_index > 1,
                "health": result,
            }
        except HostedJobError as exc:
            last_error = str(exc)
            if attempt_index >= attempts:
                break
            if delay > 0:
                sleeper(delay)
    raise HostedJobError(
        "Hosted service did not become ready after {0} attempt(s): {1}".format(
            attempts,
            last_error or "unknown error",
        )
    )


def build_job_payload(
    job_name: str,
    *,
    target_user_id: str = "",
    force: bool = False,
    delivery_mode: str = "",
    now: str = "",
    run_id: str = "",
    day: str = "",
) -> Mapping[str, Any]:
    normalized_job = str(job_name or "").strip()
    if normalized_job not in {"morning-digest", "recall-digest"}:
        raise HostedJobError("Unsupported hosted job: {0}".format(normalized_job or "<empty>"))

    payload: dict[str, Any] = {}
    if normalized_job == "morning-digest":
        payload["force"] = bool(force)
        if delivery_mode:
            payload["delivery_mode"] = delivery_mode
        if now:
            payload["now"] = now
    else:
        if run_id:
            payload["run_id"] = run_id
        if day:
            payload["day"] = day
    if target_user_id:
        payload["target_user_id"] = target_user_id
    return payload


def trigger_hosted_job(
    service_url: str,
    job_secret: str,
    *,
    job_name: str = "morning-digest",
    payload: Optional[Mapping[str, Any]] = None,
    timeout_seconds: int = 30,
    wake_service: bool = False,
    wake_timeout_seconds: int = 30,
    wake_max_attempts: int = 1,
    wake_delay_seconds: int = 0,
    opener: Optional[Callable[..., Any]] = None,
    sleeper: Optional[Callable[[float], None]] = None,
) -> Mapping[str, Any]:
    normalized_service_url = _normalized_service_url(service_url)
    normalized_secret = _normalized_job_secret(job_secret)
    normalized_job = str(job_name or "").strip()
    if normalized_job not in {"morning-digest", "recall-digest"}:
        raise HostedJobError("Unsupported hosted job: {0}".format(normalized_job or "<empty>"))

    opener = opener or request.urlopen
    warmup = None
    if wake_service:
        warmup = wait_for_hosted_health(
            normalized_service_url,
            job_secret=normalized_secret,
            timeout_seconds=wake_timeout_seconds,
            max_attempts=wake_max_attempts,
            delay_seconds=wake_delay_seconds,
            opener=opener,
            sleeper=sleeper,
        )
    url = "{0}/jobs/{1}".format(normalized_service_url, normalized_job)
    body = json.dumps(dict(payload or {}), sort_keys=True).encode("utf-8")
    req = request.Request(
        url,
        data=body,
        headers={
            "Content-Type": "application/json",
            "X-Day-Captain-Secret": normalized_secret,
        },
        method="POST",
    )
    try:
        with opener(req, timeout=timeout_seconds) as response:
            raw = response.read().decode("utf-8")
            status_code = int(getattr(response, "status", 200))
    except error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise HostedJobError("Hosted job failed with {0}: {1}".format(exc.code, detail)) from exc
    except error.URLError as exc:
        raise HostedJobError("Unable to reach hosted Day Captain service: {0}".format(exc.reason)) from exc
    except (TimeoutError, socket.timeout) as exc:
        raise HostedJobError("Hosted job request timed out after {0} second(s).".format(timeout_seconds)) from exc

    response_payload: Any
    try:
        response_payload = json.loads(raw or "{}")
    except json.JSONDecodeError:
        response_payload = {"raw_response": raw}
    if status_code != 200:
        raise HostedJobError("Hosted job returned unexpected status {0}.".format(status_code))
    if not isinstance(response_payload, dict):
        raise HostedJobError("Hosted job did not return a JSON object acknowledgement.")
    validated_payload = _validate_job_ack(response_payload, normalized_job)
    return {
        "status": "ok",
        "job": normalized_job,
        "url": url,
        "status_code": status_code,
        "request_payload": dict(payload or {}),
        "response": validated_payload,
        "warmup": warmup,
    }


def validate_hosted_service(
    service_url: str,
    job_secret: str,
    *,
    target_user_id: str = "",
    expected_graph_auth_mode: str = "",
    expected_storage_backend: str = "",
    timeout_seconds: int = 30,
    check_recall: bool = True,
    opener: Optional[Callable[..., Any]] = None,
    wake_service: bool = False,
    wake_timeout_seconds: int = 30,
    wake_max_attempts: int = 1,
    wake_delay_seconds: int = 0,
    sleeper: Optional[Callable[[float], None]] = None,
) -> Mapping[str, Any]:
    warmup = None
    if wake_service:
        warmup = wait_for_hosted_health(
            service_url,
            job_secret=job_secret,
            timeout_seconds=wake_timeout_seconds,
            max_attempts=wake_max_attempts,
            delay_seconds=wake_delay_seconds,
            opener=opener,
            sleeper=sleeper,
        )
    health = check_hosted_health(
        service_url,
        job_secret=job_secret,
        include_runtime_summary=True,
        expected_graph_auth_mode=expected_graph_auth_mode,
        expected_storage_backend=expected_storage_backend,
        timeout_seconds=timeout_seconds,
        opener=opener,
    )
    morning_payload = build_job_payload(
        "morning-digest",
        target_user_id=target_user_id,
        force=False,
    )
    morning = trigger_hosted_job(
        service_url,
        job_secret,
        job_name="morning-digest",
        payload=morning_payload,
        timeout_seconds=timeout_seconds,
        wake_service=False,
        opener=opener,
        sleeper=sleeper,
    )
    recall = None
    run_id = str(((morning.get("response") or {}).get("run_id")) or "").strip()
    if check_recall and run_id:
        recall = trigger_hosted_job(
            service_url,
            job_secret,
            job_name="recall-digest",
            payload=build_job_payload(
                "recall-digest",
                target_user_id=target_user_id,
                run_id=run_id,
            ),
            timeout_seconds=timeout_seconds,
            wake_service=False,
            opener=opener,
            sleeper=sleeper,
        )
        recalled_run_id = str(((recall.get("response") or {}).get("run_id")) or "").strip()
        if recalled_run_id != run_id:
            raise HostedJobError("Hosted recall validation returned a different run_id than morning-digest.")
    return {
        "status": "ok",
        "service_url": _normalized_service_url(service_url),
        "target_user_id": str(target_user_id or "").strip(),
        "warmup": warmup,
        "health": health,
        "runtime": health.get("runtime"),
        "morning_digest": morning,
        "recall_digest": recall,
    }

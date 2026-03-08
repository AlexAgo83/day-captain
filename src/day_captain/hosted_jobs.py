"""Helpers for triggering hosted Day Captain jobs from external automation."""

import json
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


def check_hosted_health(
    service_url: str,
    *,
    timeout_seconds: int = 30,
    opener: Optional[Callable[..., Any]] = None,
) -> Mapping[str, Any]:
    normalized_service_url = _normalized_service_url(service_url)
    opener = opener or request.urlopen
    url = "{0}/healthz".format(normalized_service_url)
    req = request.Request(
        url,
        headers={"Accept": "application/json"},
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
    try:
        payload = json.loads(raw or "{}")
    except json.JSONDecodeError:
        payload = {"raw_response": raw}
    if status_code != 200:
        raise HostedJobError("Hosted healthcheck returned unexpected status {0}.".format(status_code))
    if payload.get("status") != "ok":
        raise HostedJobError("Hosted healthcheck did not return status=ok.")
    return {
        "status": "ok",
        "url": url,
        "status_code": status_code,
        "response": payload,
    }


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
    opener: Optional[Callable[..., Any]] = None,
) -> Mapping[str, Any]:
    normalized_service_url = _normalized_service_url(service_url)
    normalized_secret = _normalized_job_secret(job_secret)
    normalized_job = str(job_name or "").strip()
    if normalized_job not in {"morning-digest", "recall-digest"}:
        raise HostedJobError("Unsupported hosted job: {0}".format(normalized_job or "<empty>"))

    opener = opener or request.urlopen
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

    response_payload: Any
    try:
        response_payload = json.loads(raw or "{}")
    except json.JSONDecodeError:
        response_payload = {"raw_response": raw}
    if status_code != 200:
        raise HostedJobError("Hosted job returned unexpected status {0}.".format(status_code))
    return {
        "status": "ok",
        "job": normalized_job,
        "url": url,
        "status_code": status_code,
        "request_payload": dict(payload or {}),
        "response": response_payload,
    }


def validate_hosted_service(
    service_url: str,
    job_secret: str,
    *,
    target_user_id: str = "",
    timeout_seconds: int = 30,
    check_recall: bool = True,
    opener: Optional[Callable[..., Any]] = None,
) -> Mapping[str, Any]:
    health = check_hosted_health(
        service_url,
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
        opener=opener,
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
            opener=opener,
        )
    return {
        "status": "ok",
        "service_url": _normalized_service_url(service_url),
        "target_user_id": str(target_user_id or "").strip(),
        "health": health,
        "morning_digest": morning,
        "recall_digest": recall,
    }

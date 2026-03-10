"""CLI entrypoints for Day Captain."""

import argparse
from datetime import date
from datetime import datetime
import json
import os
from pathlib import Path
import sys
from typing import Optional

from day_captain.adapters.auth import DeviceCodeAuthenticator
from day_captain.adapters.auth import EntraAuthError
from day_captain.adapters.auth import FileTokenCache
from day_captain.adapters.graph import GraphApiClient
from day_captain.adapters.graph import GraphDelegatedAuthProvider
from day_captain.app import build_application
from day_captain.config import DayCaptainSettings
from day_captain.hosted_jobs import HostedJobError
from day_captain.hosted_jobs import build_job_payload
from day_captain.hosted_jobs import check_hosted_health
from day_captain.hosted_jobs import trigger_hosted_job
from day_captain.hosted_jobs import validate_hosted_service
from day_captain.hosted_jobs import wait_for_hosted_health
from day_captain.models import parse_datetime
from day_captain.models import to_jsonable
from day_captain.web import serve


def _parse_datetime(value: Optional[str]) -> Optional[datetime]:
    if not value:
        return None
    return parse_datetime(str(value))


def _parse_date(value: Optional[str]) -> Optional[date]:
    if not value:
        return None
    return date.fromisoformat(value)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="day-captain")
    subparsers = parser.add_subparsers(dest="command", required=True)

    auth = subparsers.add_parser("auth", help="Manage Microsoft delegated auth.")
    auth_subparsers = auth.add_subparsers(dest="auth_command", required=True)
    auth_subparsers.add_parser("login", help="Run the Microsoft device code login flow.")
    auth_subparsers.add_parser("status", help="Show current cached auth status.")
    auth_subparsers.add_parser("logout", help="Clear cached auth tokens.")

    morning = subparsers.add_parser("morning-digest", help="Run the morning digest flow.")
    morning.add_argument("--now", help="ISO datetime override for the run clock.")
    morning.add_argument("--delivery-mode", help="Override the configured delivery mode.")
    morning.add_argument("--force", action="store_true", help="Ignore the last successful run window.")
    morning.add_argument("--preview", action="store_true", help="Render/export locally without sending mail.")
    morning.add_argument("--target-user", help="Configured mailbox/user to run.")
    morning.add_argument("--output-html", help="Optional file path where the rendered HTML digest will be written.")
    morning.add_argument("--output-text", help="Optional file path where the rendered text digest will be written.")

    weekly = subparsers.add_parser("weekly-digest", help="Run the weekly digest flow.")
    weekly.add_argument("--now", help="ISO datetime override for the run clock.")
    weekly.add_argument("--delivery-mode", help="Override the configured delivery mode.")
    weekly.add_argument("--preview", action="store_true", help="Render/export locally without sending mail.")
    weekly.add_argument("--target-user", help="Configured mailbox/user to run.")
    weekly.add_argument("--output-html", help="Optional file path where the rendered HTML digest will be written.")
    weekly.add_argument("--output-text", help="Optional file path where the rendered text digest will be written.")

    serve_parser = subparsers.add_parser("serve", help="Run the Day Captain HTTP service.")
    serve_parser.add_argument("--host", help="Override the configured bind host.")
    serve_parser.add_argument("--port", type=int, help="Override the configured bind port.")

    recall = subparsers.add_parser("recall-digest", help="Recall the latest completed digest.")
    recall.add_argument("--run-id", help="Specific digest run identifier.")
    recall.add_argument("--day", help="ISO date used to find the latest run for a day.")
    recall.add_argument("--preview", action="store_true", help="Render/export locally without sending mail.")
    recall.add_argument("--target-user", help="Configured mailbox/user to recall.")
    recall.add_argument("--output-html", help="Optional file path where the rendered HTML digest will be written.")
    recall.add_argument("--output-text", help="Optional file path where the rendered text digest will be written.")

    email_command = subparsers.add_parser(
        "email-command-recall",
        help="Process a bounded inbound email command and generate the requested recall digest.",
    )
    email_command.add_argument("--message-id", required=True, help="Inbound command email/message identifier.")
    email_command.add_argument("--sender-address", required=True, help="Sender email address.")
    email_command.add_argument("--command-text", help="Explicit normalized command text.")
    email_command.add_argument("--subject", help="Inbound email subject used for command parsing.")
    email_command.add_argument("--body", help="Inbound email body used for command parsing.")
    email_command.add_argument("--now", help="Optional ISO datetime override.")
    email_command.add_argument("--preview", action="store_true", help="Render/export locally without sending mail.")
    email_command.add_argument("--output-html", help="Optional file path where the rendered HTML digest will be written.")
    email_command.add_argument("--output-text", help="Optional file path where the rendered text digest will be written.")

    feedback = subparsers.add_parser("record-feedback", help="Record user feedback on a digest item.")
    feedback.add_argument("--run-id", required=True)
    feedback.add_argument("--source-kind", required=True)
    feedback.add_argument("--source-id", required=True)
    feedback.add_argument("--signal-type", required=True)
    feedback.add_argument("--signal-value", required=True)
    feedback.add_argument("--recorded-at", help="ISO datetime for the feedback event.")
    feedback.add_argument("--target-user", help="Configured mailbox/user tied to the feedback.")

    validate = subparsers.add_parser("validate-config", help="Validate current environment configuration.")
    validate.add_argument("--target-user", help="Optional target user to validate against configured recipients.")

    health = subparsers.add_parser(
        "check-hosted-health",
        help="Check or warm a hosted Day Captain service before running jobs, intended for ops automation.",
    )
    health.add_argument(
        "--service-url",
        default="",
        help="Hosted Day Captain base URL. Falls back to DAY_CAPTAIN_SERVICE_URL.",
    )
    health.add_argument(
        "--job-secret",
        default="",
        help="Hosted job secret. Falls back to DAY_CAPTAIN_JOB_SECRET.",
    )
    health.add_argument("--timeout-seconds", type=int, default=30)
    health.add_argument(
        "--wake-service",
        action="store_true",
        help="Retry /healthz to wake a sleeping hosted service before reporting readiness.",
    )
    health.add_argument("--wake-timeout-seconds", type=int, default=30)
    health.add_argument("--wake-max-attempts", type=int, default=1)
    health.add_argument("--wake-delay-seconds", type=int, default=0)
    health.add_argument(
        "--expect-graph-auth-mode",
        choices=("delegated", "app_only"),
        help="Fail if the hosted runtime summary reports a different Graph auth mode.",
    )
    health.add_argument(
        "--expect-storage-backend",
        choices=("sqlite", "postgres"),
        help="Fail if the hosted runtime summary reports a different storage backend.",
    )

    trigger = subparsers.add_parser(
        "trigger-hosted-job",
        help="Trigger a hosted Day Captain job, intended for external ops automation.",
    )
    trigger.add_argument(
        "--service-url",
        default="",
        help="Hosted Day Captain base URL. Falls back to DAY_CAPTAIN_SERVICE_URL.",
    )
    trigger.add_argument(
        "--job-secret",
        default="",
        help="Hosted job secret. Falls back to DAY_CAPTAIN_JOB_SECRET.",
    )
    trigger.add_argument(
        "--job",
        choices=("morning-digest", "weekly-digest", "recall-digest", "email-command-recall"),
        default="morning-digest",
    )
    trigger.add_argument("--target-user", help="Explicit target user for the hosted run.")
    trigger.add_argument("--force", action="store_true", help="Force a fresh morning digest window.")
    trigger.add_argument("--delivery-mode", help="Optional delivery-mode override for morning digest.")
    trigger.add_argument("--now", help="Optional ISO datetime override for morning digest.")
    trigger.add_argument("--run-id", help="Run identifier for recall.")
    trigger.add_argument("--day", help="ISO date for recall when run-id is omitted.")
    trigger.add_argument("--message-id", help="Inbound command message identifier.")
    trigger.add_argument("--sender-address", help="Inbound command sender email address.")
    trigger.add_argument("--command-text", help="Explicit normalized command text.")
    trigger.add_argument("--subject", help="Inbound command email subject.")
    trigger.add_argument("--body", help="Inbound command email body.")
    trigger.add_argument("--timeout-seconds", type=int, default=30)
    trigger.add_argument(
        "--wake-service",
        action="store_true",
        help="Probe /healthz first to wake a sleeping hosted service before the real job trigger.",
    )
    trigger.add_argument("--wake-timeout-seconds", type=int, default=30)
    trigger.add_argument("--wake-max-attempts", type=int, default=1)
    trigger.add_argument("--wake-delay-seconds", type=int, default=0)

    validate_hosted = subparsers.add_parser(
        "validate-hosted-service",
        help="Run a hosted healthcheck plus morning-digest/recall validation, intended for ops automation.",
    )
    validate_hosted.add_argument(
        "--service-url",
        default="",
        help="Hosted Day Captain base URL. Falls back to DAY_CAPTAIN_SERVICE_URL.",
    )
    validate_hosted.add_argument(
        "--job-secret",
        default="",
        help="Hosted job secret. Falls back to DAY_CAPTAIN_JOB_SECRET.",
    )
    validate_hosted.add_argument("--target-user", help="Explicit target user for hosted validation.")
    validate_hosted.add_argument("--timeout-seconds", type=int, default=30)
    validate_hosted.add_argument(
        "--wake-service",
        action="store_true",
        help="Probe /healthz first to wake a sleeping hosted service before validation.",
    )
    validate_hosted.add_argument("--wake-timeout-seconds", type=int, default=30)
    validate_hosted.add_argument("--wake-max-attempts", type=int, default=1)
    validate_hosted.add_argument("--wake-delay-seconds", type=int, default=0)
    validate_hosted.add_argument(
        "--expect-graph-auth-mode",
        choices=("delegated", "app_only"),
        help="Fail if the hosted runtime summary reports a different Graph auth mode.",
    )
    validate_hosted.add_argument(
        "--expect-storage-backend",
        choices=("sqlite", "postgres"),
        help="Fail if the hosted runtime summary reports a different storage backend.",
    )
    validate_hosted.add_argument(
        "--skip-recall",
        action="store_true",
        help="Skip recall-digest validation after the morning-digest trigger.",
    )
    validate_hosted.add_argument(
        "--check-email-command",
        action="store_true",
        help="Also validate the hosted inbound email-command recall path.",
    )
    validate_hosted.add_argument(
        "--email-command-sender",
        help="Sender address used when validating hosted email-command recall.",
    )
    validate_hosted.add_argument(
        "--email-command-text",
        default="recall",
        help="Command text used when validating hosted email-command recall.",
    )

    return parser


def _auth_cache(settings: DayCaptainSettings) -> FileTokenCache:
    return FileTokenCache(settings.graph_auth_cache_path)


def _authenticator(settings: DayCaptainSettings) -> DeviceCodeAuthenticator:
    return DeviceCodeAuthenticator(
        tenant_id=settings.graph_tenant_id,
        client_id=settings.graph_client_id,
        timeout_seconds=settings.graph_timeout_seconds,
    )


def _graph_provider(settings: DayCaptainSettings) -> GraphDelegatedAuthProvider:
    # Local CLI auth remains delegated even when hosted deployment uses app-only auth.
    return GraphDelegatedAuthProvider(
        api_client=GraphApiClient(
            base_url=settings.graph_base_url,
            timeout_seconds=settings.graph_timeout_seconds,
        ),
        access_token=settings.graph_access_token,
        token_cache=_auth_cache(settings),
        authenticator=_authenticator(settings),
        user_id=settings.graph_user_id,
    )


def _run_auth_command(args: argparse.Namespace, settings: DayCaptainSettings) -> object:
    cache = _auth_cache(settings)
    if args.auth_command == "logout":
        cache.clear()
        return {"status": "logged_out", "cache_path": settings.graph_auth_cache_path}

    cached = cache.load()
    if args.auth_command == "status":
        return {
            "status": "authenticated" if cached is not None else "not_authenticated",
            "cache_path": settings.graph_auth_cache_path,
            "user_id": "" if cached is None else cached.user_id,
            "expires_at": None if cached is None else cached.expires_at,
            "scopes": () if cached is None else cached.scopes,
        }

    try:
        session = _authenticator(settings).start_device_code(settings.graph_login_scopes())
        print(session.message or "Open the Microsoft device login URL and enter the code.", file=sys.stderr)
        bundle = _authenticator(settings).poll_for_tokens(session, settings.graph_login_scopes())
        provider = _graph_provider(settings)
        cache.save(bundle)
        context = provider.authenticate(settings.graph_scopes)
        refreshed = cache.load()
        return {
            "status": "authenticated",
            "user_code": session.user_code,
            "verification_uri": session.verification_uri,
            "user_id": context.user_id,
            "expires_at": None if refreshed is None else refreshed.expires_at,
            "scopes": None if refreshed is None else refreshed.scopes,
            "cache_path": settings.graph_auth_cache_path,
        }
    except EntraAuthError as exc:
        raise SystemExit(str(exc))


def _run_validate_command(args: argparse.Namespace, settings: DayCaptainSettings) -> object:
    try:
        return settings.validation_summary(target_user_id=getattr(args, "target_user", "") or "")
    except ValueError as exc:
        raise SystemExit(str(exc))


def _run_check_hosted_health_command(args: argparse.Namespace) -> object:
    service_url = str(args.service_url or "").strip() or str(os.getenv("DAY_CAPTAIN_SERVICE_URL") or "").strip()
    job_secret = str(args.job_secret or "").strip() or str(os.getenv("DAY_CAPTAIN_JOB_SECRET") or "").strip()
    try:
        if bool(getattr(args, "wake_service", False)):
            return wait_for_hosted_health(
                service_url,
                job_secret=job_secret,
                include_runtime_summary=True,
                expected_graph_auth_mode=str(getattr(args, "expect_graph_auth_mode", "") or "").strip(),
                expected_storage_backend=str(getattr(args, "expect_storage_backend", "") or "").strip(),
                timeout_seconds=int(getattr(args, "wake_timeout_seconds", 30)),
                max_attempts=int(getattr(args, "wake_max_attempts", 1)),
                delay_seconds=int(getattr(args, "wake_delay_seconds", 0)),
            )
        return check_hosted_health(
            service_url,
            job_secret=job_secret,
            include_runtime_summary=True,
            expected_graph_auth_mode=str(getattr(args, "expect_graph_auth_mode", "") or "").strip(),
            expected_storage_backend=str(getattr(args, "expect_storage_backend", "") or "").strip(),
            timeout_seconds=int(args.timeout_seconds),
        )
    except HostedJobError as exc:
        raise SystemExit(str(exc))


def _run_trigger_hosted_job_command(args: argparse.Namespace) -> object:
    service_url = str(args.service_url or "").strip() or str(os.getenv("DAY_CAPTAIN_SERVICE_URL") or "").strip()
    job_secret = str(args.job_secret or "").strip()
    if not job_secret:
        job_secret = str(os.getenv("DAY_CAPTAIN_JOB_SECRET") or "").strip()
    payload = build_job_payload(
        args.job,
        target_user_id=str(args.target_user or "").strip(),
        force=bool(getattr(args, "force", False)),
        delivery_mode=str(getattr(args, "delivery_mode", "") or "").strip(),
        now=str(getattr(args, "now", "") or "").strip(),
        run_id=str(getattr(args, "run_id", "") or "").strip(),
        day=str(getattr(args, "day", "") or "").strip(),
        command_message_id=str(getattr(args, "message_id", "") or "").strip(),
        sender_address=str(getattr(args, "sender_address", "") or "").strip(),
        command_text=str(getattr(args, "command_text", "") or "").strip(),
        subject=str(getattr(args, "subject", "") or "").strip(),
        body=str(getattr(args, "body", "") or "").strip(),
    )
    try:
        return trigger_hosted_job(
            service_url,
            job_secret,
            job_name=args.job,
            payload=payload,
            timeout_seconds=int(args.timeout_seconds),
            wake_service=bool(getattr(args, "wake_service", False)),
            wake_timeout_seconds=int(getattr(args, "wake_timeout_seconds", 30)),
            wake_max_attempts=int(getattr(args, "wake_max_attempts", 1)),
            wake_delay_seconds=int(getattr(args, "wake_delay_seconds", 0)),
        )
    except HostedJobError as exc:
        raise SystemExit(str(exc))


def _run_validate_hosted_service_command(args: argparse.Namespace) -> object:
    service_url = str(args.service_url or "").strip() or str(os.getenv("DAY_CAPTAIN_SERVICE_URL") or "").strip()
    job_secret = str(args.job_secret or "").strip() or str(os.getenv("DAY_CAPTAIN_JOB_SECRET") or "").strip()
    try:
        return validate_hosted_service(
            service_url,
            job_secret,
            target_user_id=str(args.target_user or "").strip(),
            expected_graph_auth_mode=str(getattr(args, "expect_graph_auth_mode", "") or "").strip(),
            expected_storage_backend=str(getattr(args, "expect_storage_backend", "") or "").strip(),
            timeout_seconds=int(args.timeout_seconds),
            check_recall=not bool(args.skip_recall),
            check_email_command=bool(getattr(args, "check_email_command", False)),
            email_command_sender=str(getattr(args, "email_command_sender", "") or "").strip(),
            email_command_text=str(getattr(args, "email_command_text", "recall") or "recall").strip(),
            wake_service=bool(getattr(args, "wake_service", False)),
            wake_timeout_seconds=int(getattr(args, "wake_timeout_seconds", 30)),
            wake_max_attempts=int(getattr(args, "wake_max_attempts", 1)),
            wake_delay_seconds=int(getattr(args, "wake_delay_seconds", 0)),
        )
    except HostedJobError as exc:
        raise SystemExit(str(exc))


def _export_digest_preview(args: argparse.Namespace, result: object) -> None:
    output_html = str(getattr(args, "output_html", "") or "").strip()
    output_text = str(getattr(args, "output_text", "") or "").strip()
    if not output_html and not output_text:
        return

    payload = getattr(result, "payload", result)
    delivery_body = str(getattr(payload, "delivery_body", "") or "")
    delivery_payload = getattr(payload, "delivery_payload", {}) or {}
    html_body = str(delivery_payload.get("html_body") or "")

    if output_html:
        target = Path(output_html)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(html_body, encoding="utf-8")
    if output_text:
        target = Path(output_text)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(delivery_body, encoding="utf-8")


def _resolved_delivery_mode(
    args: argparse.Namespace,
    *,
    explicit_delivery_mode: Optional[str] = None,
) -> Optional[str]:
    if bool(getattr(args, "preview", False)):
        return "json"
    if explicit_delivery_mode is None:
        return None
    candidate = str(explicit_delivery_mode or "").strip()
    return candidate or None


def main(argv: Optional[list] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    settings = DayCaptainSettings.from_env()

    if args.command == "auth":
        result = _run_auth_command(args, settings)
        print(json.dumps(to_jsonable(result), indent=2, sort_keys=True))
        return 0
    if args.command == "validate-config":
        result = _run_validate_command(args, settings)
        print(json.dumps(to_jsonable(result), indent=2, sort_keys=True))
        return 0
    if args.command == "check-hosted-health":
        result = _run_check_hosted_health_command(args)
        print(json.dumps(to_jsonable(result), indent=2, sort_keys=True))
        return 0
    if args.command == "trigger-hosted-job":
        result = _run_trigger_hosted_job_command(args)
        print(json.dumps(to_jsonable(result), indent=2, sort_keys=True))
        return 0
    if args.command == "validate-hosted-service":
        result = _run_validate_hosted_service_command(args)
        print(json.dumps(to_jsonable(result), indent=2, sort_keys=True))
        return 0
    if args.command == "serve":
        serve(settings=settings, host=args.host, port=args.port)
        return 0

    app = build_application(settings=settings)

    if args.command == "morning-digest":
        result = app.run_morning_digest(
            now=_parse_datetime(args.now),
            delivery_mode=_resolved_delivery_mode(args, explicit_delivery_mode=args.delivery_mode),
            force=args.force,
            target_user_id=args.target_user,
        )
    elif args.command == "weekly-digest":
        result = app.run_weekly_digest(
            now=_parse_datetime(args.now),
            delivery_mode=_resolved_delivery_mode(args, explicit_delivery_mode=args.delivery_mode),
            target_user_id=args.target_user,
        )
    elif args.command == "recall-digest":
        result = app.recall_digest(
            run_id=args.run_id,
            day=_parse_date(args.day),
            target_user_id=args.target_user,
        )
    elif args.command == "email-command-recall":
        result = app.process_email_command_recall(
            command_message_id=args.message_id,
            sender_address=args.sender_address,
            command_text=args.command_text or "",
            subject=args.subject or "",
            body=args.body or "",
            now=_parse_datetime(args.now),
            delivery_mode=_resolved_delivery_mode(args, explicit_delivery_mode="graph_send"),
        )
    else:
        result = app.record_feedback(
            run_id=args.run_id,
            source_kind=args.source_kind,
            source_id=args.source_id,
            signal_type=args.signal_type,
            signal_value=args.signal_value,
            recorded_at=_parse_datetime(args.recorded_at),
            target_user_id=args.target_user,
        )

    _export_digest_preview(args, result)
    print(json.dumps(to_jsonable(result), indent=2, sort_keys=True))
    return 0

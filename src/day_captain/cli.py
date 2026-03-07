"""CLI entrypoints for Day Captain."""

import argparse
from datetime import date
from datetime import datetime
import json
import sys
from typing import Optional

from day_captain.adapters.auth import DeviceCodeAuthenticator
from day_captain.adapters.auth import EntraAuthError
from day_captain.adapters.auth import FileTokenCache
from day_captain.adapters.graph import GraphApiClient
from day_captain.adapters.graph import GraphDelegatedAuthProvider
from day_captain.app import build_application
from day_captain.config import DayCaptainSettings
from day_captain.models import to_jsonable
from day_captain.web import serve


def _parse_datetime(value: Optional[str]) -> Optional[datetime]:
    if not value:
        return None
    return datetime.fromisoformat(value)


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

    serve_parser = subparsers.add_parser("serve", help="Run the Day Captain HTTP service.")
    serve_parser.add_argument("--host", help="Override the configured bind host.")
    serve_parser.add_argument("--port", type=int, help="Override the configured bind port.")

    recall = subparsers.add_parser("recall-digest", help="Recall the latest completed digest.")
    recall.add_argument("--run-id", help="Specific digest run identifier.")
    recall.add_argument("--day", help="ISO date used to find the latest run for a day.")

    feedback = subparsers.add_parser("record-feedback", help="Record user feedback on a digest item.")
    feedback.add_argument("--run-id", required=True)
    feedback.add_argument("--source-kind", required=True)
    feedback.add_argument("--source-id", required=True)
    feedback.add_argument("--signal-type", required=True)
    feedback.add_argument("--signal-value", required=True)
    feedback.add_argument("--recorded-at", help="ISO datetime for the feedback event.")

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


def main(argv: Optional[list] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    settings = DayCaptainSettings.from_env()

    if args.command == "auth":
        result = _run_auth_command(args, settings)
        print(json.dumps(to_jsonable(result), indent=2, sort_keys=True))
        return 0
    if args.command == "serve":
        serve(settings=settings, host=args.host, port=args.port)
        return 0

    app = build_application(settings=settings)

    if args.command == "morning-digest":
        result = app.run_morning_digest(
            now=_parse_datetime(args.now),
            delivery_mode=args.delivery_mode,
            force=args.force,
        )
    elif args.command == "recall-digest":
        result = app.recall_digest(
            run_id=args.run_id,
            day=_parse_date(args.day),
        )
    else:
        result = app.record_feedback(
            run_id=args.run_id,
            source_kind=args.source_kind,
            source_id=args.source_id,
            signal_type=args.signal_type,
            signal_value=args.signal_value,
            recorded_at=_parse_datetime(args.recorded_at),
        )

    print(json.dumps(to_jsonable(result), indent=2, sort_keys=True))
    return 0

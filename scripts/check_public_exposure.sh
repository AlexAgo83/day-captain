#!/usr/bin/env bash
set -euo pipefail

extra_pattern="${DAY_CAPTAIN_PUBLIC_SCAN_EXTRA_PATTERN:-}"
pattern='day-captain\.onrender\.com|DAY_CAPTAIN_GRAPH_AUTH_CACHE_PATH=\.day_captain_auth_[[:alnum:]_-]+\.json|\.day_captain_auth_[[:alnum:]_-]+\.json|production sender-side audit|sender-side audit|[0-9]+ historical briefs|[0-9]+ stable production briefs|[0-9]+-brief|2026-06-07|configured_sender_user=daycaptain@company\.com|target\.user@company\.com|roles=null|admin consent|Application permissions|default tenant Power Platform|cp-wc-26'

if [ -n "$extra_pattern" ]; then
  pattern="$pattern|$extra_pattern"
fi

if git grep -n -E "$pattern" -- ':!scripts/check_public_exposure.sh'; then
  echo
  echo "Public exposure scan found tracked matches. Anonymize them or move them to private ops docs." >&2
  exit 1
fi

echo "Public exposure scan passed."

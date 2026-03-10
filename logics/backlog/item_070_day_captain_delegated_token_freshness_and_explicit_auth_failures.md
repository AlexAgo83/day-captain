## item_070_day_captain_delegated_token_freshness_and_explicit_auth_failures - Prevent expired delegated token reuse and keep auth failures explicit
> From version: 1.5.0
> Status: Ready
> Understanding: 97%
> Confidence: 95%
> Progress: 0%
> Complexity: Medium
> Theme: Reliability
> Reminder: Update status/understanding/confidence/progress and linked task references when you edit this doc.

# Problem
- The delegated Graph auth path currently has a branch where an expired cached access token can still be reused if refresh is unavailable or cannot proceed.
- That behavior defers the failure into later Graph calls and obscures the real problem, which is stale auth state rather than a generic downstream API failure.

# Scope
- In:
  - rejecting expired delegated tokens when refresh is unavailable or unsuccessful
  - making the resulting auth failure explicit and actionable
  - adding regression coverage around expired-cache behavior
- Out:
  - app-only auth redesign
  - secret rotation or external vault integration
  - changing Graph data collection behavior beyond auth correctness

# Acceptance criteria
- AC1: Delegated auth never returns an expired cached access token as if it were valid.
- AC2: When delegated refresh is unavailable or fails, the user gets an explicit auth/configuration error instead of a delayed opaque Graph failure.
- AC3: Tests cover valid cache, expired cache with refresh, and expired cache without usable refresh.

# AC Traceability
- Req034 AC2 -> This item is the dedicated delegated-token freshness slice. Proof: it removes expired-token reuse and keeps auth failure explicit at the boundary.
- Req034 AC6 -> This item requires regression coverage for the auth edge cases. Proof: auth freshness scenarios need dedicated tests in this implementation slice.

# Links
- Request: `req_034_day_captain_hosted_runtime_fail_fast_and_identity_normalization`

# Priority
- Impact: High - auth issues should fail clearly at the boundary.
- Urgency: High - stale-token reuse creates misleading runtime behavior.

# Notes
- Derived from the project review of delegated auth error handling and cache freshness.

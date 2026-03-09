## item_051_day_captain_graph_nextlink_trust_boundary_enforcement - Prevent Graph pagination from forwarding bearer tokens to unexpected absolute hosts
> From version: 1.4.1
> Status: Ready
> Understanding: 100%
> Confidence: 95%
> Progress: 0%
> Complexity: Medium
> Theme: Security
> Reminder: Update status/understanding/confidence/progress and linked task references when you edit this doc.

# Problem
- The Graph adapter currently accepts absolute URLs when building collection requests and replays bearer-authenticated requests against `@odata.nextLink` values without constraining the host.
- If a malformed or malicious paginated response points to an unexpected absolute origin, the service could forward the Microsoft Graph bearer token outside the intended trust boundary.
- That risk exists in production because the same collection code is used by hosted runs.

# Scope
- In:
  - define a trusted-origin policy for Graph pagination
  - allow valid same-origin Graph absolute `nextLink` values
  - reject or fail boundedly on cross-origin absolute `nextLink` values
  - cover trusted and rejected pagination paths in tests
- Out:
  - redesign of the full Graph client stack
  - broader SSRF hardening for unrelated outbound integrations
  - local delegated token-cache storage concerns

```mermaid
flowchart LR
    GraphPage[Graph page response] --> NextLink{@odata.nextLink}
    NextLink -->|Trusted same origin| Follow[Continue collection]
    NextLink -->|Unexpected origin| Reject[Fail boundedly]
```

# Acceptance criteria
- AC1: The Graph adapter continues to support legitimate same-origin absolute pagination links.
- AC2: A cross-origin absolute `@odata.nextLink` is rejected before any bearer-authenticated request is sent.
- AC3: Tests cover same-origin allow and cross-origin reject behavior.

# AC Traceability
- Req029 AC1 -> Item scope explicitly constrains bearer token forwarding to the trusted origin only. Proof: the item exists to enforce a trusted-origin pagination policy.
- Req029 AC2 -> Acceptance criteria define the bounded handling of absolute `nextLink` values. Proof: the item covers both same-origin allow and cross-origin reject behavior.
- Req029 AC4 -> Acceptance criteria require automated coverage of trusted and rejected pagination paths. Proof: tests are part of the item closure contract.

# Links
- Request: `req_029_day_captain_hosted_graph_boundary_and_job_secret_hardening`
- Primary task(s): `task_034_day_captain_hosted_graph_boundary_and_job_secret_hardening_orchestration` (`Ready`)

# Priority
- Impact: High - this is a bearer-token boundary issue in production collection paths.
- Urgency: Medium - the exploitability depends on hostile or corrupted pagination input, but the boundary is worth tightening now.

# Notes
- Derived from `req_029_day_captain_hosted_graph_boundary_and_job_secret_hardening`.
- The implementation should normalize against `DAY_CAPTAIN_GRAPH_BASE_URL`, including sovereign or custom Graph hosts when configured.

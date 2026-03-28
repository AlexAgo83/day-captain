# Changelog (`1.8.0 -> 1.9.0`)

## Major Highlights

- Added a bounded external news capsule to the digest, with RSS ingestion, source attribution, and safe runtime fallback behavior.
- Hardened hosted Microsoft Graph delegated-auth handling by preventing stale cached identity metadata from shadowing explicit tokens and by tightening unattended hosted validation expectations.
- Introduced a broader mail-intelligence and runtime-clarity layer: typed digest cards, recent digest memory, action-ownership interpretation, suspicion signals, weather degradation logging, and explicit local Graph fail-fast behavior.
- Added footer processing-time metadata to delivered digests and locked down meeting-card open-link behavior with explicit regression coverage.

## Version 1.9.0

### Delivered

- Added a bounded external-news provider and renderer support so daily digests can include a small attributed news capsule when configured.
- Preserved safe omission of the external-news section when the provider is disabled, misconfigured, or fails at runtime.
- Hardened hosted delegated-auth validation so unattended hosted execution no longer accepts incomplete delegated setup as a valid production contract.
- Prevented stale delegated token-cache identity and scope metadata from overriding an explicit access token during Graph authentication.
- Added typed digest-card semantics to reduce renderer dependence on ad hoc metadata for ownership, trust, continuity, and recurrence behavior.
- Added recent digest memory across the last completed runs so surfaced items can carry bounded continuity signals such as changed, still-open, and cleared.
- Improved mail interpretation by distinguishing relevance from action ownership and by applying conservative suspicious-mail handling when trust is weak.
- Added weather degraded-path logging and explicit local fail-fast behavior when a real Graph-backed run was clearly expected but the runtime would otherwise fall back to stubs.
- Added footer processing-time metadata to delivered digests in both text and HTML output.
- Preserved the existing meeting-card open action and added explicit fallback coverage for meetings without a reliable source URL.
- Bumped the imported `logics/skills` kit to `v1.1.0`, disabled example scheduled workflows in the app repository, and synchronized the new Logics requests, backlog items, and orchestration tasks for the delivered slices.

### Validation

- `python3 -m pytest -q`
- `python3 logics/skills/logics-doc-linter/scripts/logics_lint.py --require-status`
- `python3 logics/skills/logics-flow-manager/scripts/workflow_audit.py --group-by-doc`
- `python3 /Users/alexandreagostini/Documents/cdx-logics-vscode/logics/skills/logics-version-release-manager/scripts/publish_version_release.py --version 1.9.0 --notes-file changelogs/CHANGELOGS_1_9_0.md --dry-run`

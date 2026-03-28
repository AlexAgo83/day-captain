## item_088_day_captain_typed_digest_card_contract_and_renderer_migration - Replace ad hoc digest metadata with a typed digest card contract
> From version: 1.8.0
> Status: Ready
> Understanding: 97%
> Confidence: 94%
> Progress: 0%
> Complexity: High
> Theme: Architecture
> Reminder: Update status/understanding/confidence/progress and linked task references when you edit this doc.

# Problem
- Core digest semantics are still passed through free-form `context_metadata` even when they drive first-class rendering and wording behavior.
- That makes renderer behavior fragile because upstream stages and downstream presentation are coupled through implicit string keys rather than explicit types.
- Future digest-card evolution needs a typed contract for meaning, next step, confidence, owner, trust, and related semantic fields.

# Scope
- In:
  - define a typed digest-card contract for first-class presentation semantics
  - migrate renderer-critical metadata off ad hoc key lookups where feasible
  - preserve text and HTML digest behavior while shifting to the new contract
  - add coverage for the new typed contract and migration behavior
- Out:
  - full redesign of the digest look and feel
  - unrelated auth or storage work
  - product features that do not depend on digest-card semantics

```mermaid
flowchart LR
    Meta[Ad hoc context metadata] --> Contract[Typed digest card contract]
    Contract --> Render[Renderer and wording use explicit fields]
    Render --> Stability[Safer feature evolution]
```

# Acceptance criteria
- AC1: Renderer-critical digest semantics are represented through a clearer typed contract instead of relying mainly on ad hoc metadata keys.
- AC2: Text and HTML rendering use the new contract for first-class fields such as sender, read state, recurrence, confidence, or similar card semantics.
- AC3: Existing digest behavior remains stable while the typed contract is introduced incrementally.
- AC4: Tests cover typed-card contract behavior and migration-safe rendering.

# AC Traceability
- Req040 AC4 -> This item creates a clearer typed contract between parsing and presentation. Proof: renderer-critical semantics are moved out of ad hoc metadata.
- Req040 AC5 -> This item supports explicit assistant-card rendering semantics. Proof: typed card fields are a prerequisite for clearer presentation.
- Req046 AC1 -> This item promotes core digest semantics into first-class contracts. Proof: the new typed digest card model is the main scope.
- Req046 AC3 -> This item removes renderer dependence on implicit string keys. Proof: migration off `context_metadata` is explicit in scope.

# Links
- Request: `req_040_day_captain_structured_mail_and_calendar_parsing_and_digest_presentation`
- Related request(s): `req_046_day_captain_typed_digest_contract_and_services_decomposition`
- Primary task(s): `task_045_day_captain_mail_intelligence_and_runtime_clarity_orchestration` (`Ready`)

# Priority
- Impact: High - this is the contract needed to keep renderer evolution safe as mail intelligence grows.
- Urgency: Medium - it should move in lockstep with the structured parsing work, not after too many more metadata-driven features land.

# Notes
- Derived jointly from `req_040` and `req_046`.
- The intent is to migrate the contract, not to perform a big-bang renderer rewrite.

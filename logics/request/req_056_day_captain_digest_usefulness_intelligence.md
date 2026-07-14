## req_056_day_captain_digest_usefulness_intelligence - Day Captain digest usefulness intelligence
> From version: 1.0.0
> Schema version: 1.0
> Status: Draft
> Understanding: 90%
> Confidence: 85%
> Complexity: High
> Theme: Intelligence
> Reminder: Update status/understanding/confidence and linked backlog/task references when you edit this doc.

# Needs
- Make delivered digests useful enough to justify opening them; a digest may be short and clean but should not feel shallow or unnecessary.
- Explain why each surfaced card exists so poor digest quality can be debugged from content-free evidence before changing ranking rules.
- Use richer but bounded context only for high-potential candidates, preserving privacy, cost, and existing Graph/storage boundaries.
- Select LLM and overview inputs by operational value instead of raw score order alone.
- Make the top summary answer what changed, what the user should do, and what can be ignored; if there is no meaningful work, say so plainly.

# Context
- The current production actionability work reduced visible length, generic actions, repeated cards, and sensitive-content exposure, but it mainly proved noise reduction rather than usefulness.
- Message scoring still starts from subject and body_preview; full body or thread context is not collected for normal candidates before scoring and wording.
- When the LLM provider is disabled or unavailable, IdentityDigestWordingEngine and DeterministicDigestOverviewEngine provide shallow deterministic wording.
- When the LLM provider is enabled, LlmDigestWordingEngine rewrites only a bounded shortlist selected from already-prioritized items, and LlmDigestOverviewEngine compacts each rendered section to at most one item.
- The existing replay command is identity-free and can export HTML/text artifacts, but it does not yet expose a per-card inclusion explanation or a usefulness gate.
- All fixtures and docs in this corpus must stay anonymized. Do not persist real subjects, bodies, addresses, client names, supplier names, tokens, or secrets.

# Acceptance criteria
- AC1: A debug-safe digest explanation artifact exists for preview/replay runs and shows each rendered card's section, score, reason codes, confidence, owner, continuity state, source kind, and suppression counters without raw mailbox content.
- AC2: The replay corpus includes shallow-but-noisy, truly useful, no-meaningful-work, wrong-shortlist, and rich-thread-context scenarios using only .test identities and synthetic content.
- AC3: A usefulness gate reports aggregate actionable-card quality: concrete next step, owner clarity, due signal, change signal, critical failure, meeting conflict, and unsupported-watch counts.
- AC4: The initial scoring pass remains cheap and preview-based, but a bounded enrichment pass can fetch or assemble richer context only for high-potential candidates before LLM wording or final selection.
- AC5: Rich context never crosses storage, telemetry, docs, replay fixtures, or debug artifacts as raw mailbox content; any persisted or printed evidence is content-free or synthetic.
- AC6: LLM wording shortlist selection uses a balanced operational mix rather than raw score order alone: critical failures, user-owned actions, overdue/changed continuity, meeting conflicts, and highest-confidence watch items each get a bounded slot when present.
- AC7: Deterministic fallback suppresses or labels unsupported generic actions instead of emitting keep-in-view or vague reply/confirm wording when evidence is insufficient.
- AC8: The top summary follows a stable contract: changed since last digest, required user action, blocked/waiting items, and safe-to-ignore/no-meaningful-work statement when applicable.
- AC9: A daily digest with no actionable or changed work can render a concise no-meaningful-work email rather than padded low-signal cards.
- AC10: Focused tests, full unit discovery, replay metrics, Logics validation, lint, and audit pass before implementation closeout.

# Definition of Ready (DoR)
- [x] Problem statement is explicit and user impact is clear.
- [x] Scope boundaries (in/out) are explicit.
- [x] Acceptance criteria are testable.
- [x] Dependencies and known risks are listed.

# Companion docs
- Product brief(s): `prod_003_day_captain_useful_decision_brief`
- Architecture decision(s): (none yet)

# References
- src/day_captain/app.py
- src/day_captain/services.py
- src/day_captain/adapters/graph.py
- src/day_captain/adapters/llm.py
- src/day_captain/config.py
- src/day_captain/replay.py
- src/day_captain/digest_metrics.py
- src/day_captain/digest_parsing.py
- src/day_captain/digest_memory.py
- tests/test_scoring.py
- tests/test_llm.py
- tests/test_replay.py
- tests/test_digest_metrics.py
- tests/test_digest_renderer.py
- docs/digest_rendering_validation.md
- logics/request/req_055_day_captain_production_digest_actionability_improvement.md
- logics/product/prod_002_day_captain_actionable_differential_brief.md

# AI Context
- Summary: Day Captain digest usefulness intelligence
- Keywords: request-chain-scaffold, day captain digest usefulness intelligence, development-ready
- Use when: You need to implement or review the scaffolded workflow for Day Captain digest usefulness intelligence.
- Skip when: The change is unrelated to this scaffolded request chain.

# Backlog
- `item_116_add_privacy_safe_digest_usefulness_debug_evidence`
- `item_117_add_bounded_rich_context_for_high_potential_candidates`
- `item_118_select_llm_and_final_digest_inputs_by_operational_value`
- `item_119_make_the_top_summary_decision_oriented`

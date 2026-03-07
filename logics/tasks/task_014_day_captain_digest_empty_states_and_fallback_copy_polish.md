## task_014_day_captain_digest_empty_states_and_fallback_copy_polish - Replace technical empty states and improve deterministic assistant copy
> From version: 0.5.0
> Status: Ready
> Understanding: 99%
> Confidence: 98%
> Progress: 0%
> Complexity: Medium
> Theme: Quality
> Reminder: Update status/understanding/confidence/progress and dependencies/references when you edit this doc.

# Context
- Derived from backlog item `item_007_day_captain_mailbox_tone_and_copy_polish`.
- Source file: `logics/backlog/item_007_day_captain_mailbox_tone_and_copy_polish.md`.
- Related request(s): `req_007_day_captain_mailbox_tone_and_copy_polish`.
- Depends on: `task_009_day_captain_digest_signal_quality_tuning`, `task_010_day_captain_llm_digest_wording_activation_and_tuning`.
- Delivery target: make the digest read more like a concise assistant update even when the LLM path is not active, especially in empty sections and fallback summaries.

```mermaid
flowchart LR
    Backlog[Backlog: `item_007_day_captain_mailbox_tone_and_copy_polish`] --> Step1[Replace technical empty states]
    Step1 --> Step2[Improve deterministic fallback summary copy]
    Step2 --> Step3[Validate safe behavior without LLM]
    Step3 --> Validation[Validation]
    Validation --> Report[Report and Done]
```

# Plan
- [ ] 1. Replace `None`-style empty states with assistant-like section copy.
- [ ] 2. Improve deterministic fallback summaries so they are concise, factual, and more user-facing.
- [ ] 3. Preserve safe behavior when the LLM wording path is disabled or unavailable.
- [ ] 4. Validate the updated wording on local payloads and a real delivered digest.
- [ ] FINAL: Update related Logics docs

# AC Traceability
- AC3 -> Plan step 1 replaces technical empty states. Proof: task explicitly removes `None`-style output.
- AC4 -> Plan step 2 improves deterministic assistant copy. Proof: task explicitly rewrites fallback summaries.
- AC5 -> Plan step 4 validates real digest quality. Proof: task explicitly includes real delivered validation.
- AC6 -> Plan step 4 preserves delivery compatibility. Proof: task explicitly validates both local payloads and delivered output.
- AC7 -> Plan step 3 preserves deterministic safety. Proof: task explicitly keeps behavior coherent without LLM availability.
- AC8 -> This task is one part of the mailbox tone decomposition. Proof: the request explicitly splits the polish slice into header/subject and copy/empty-state tasks, including this one.

# Links
- Backlog item: `item_007_day_captain_mailbox_tone_and_copy_polish`
- Request(s): `req_007_day_captain_mailbox_tone_and_copy_polish`

# Validation
- python3 -m unittest tests.test_digest_renderer tests.test_llm tests.test_delivery_contract
- python3 -m unittest discover -s tests
- PYTHONPATH=src python3 -m day_captain morning-digest --delivery-mode graph_send --force
- python3 logics/skills/logics-doc-linter/scripts/logics_lint.py --require-status
- python3 logics/skills/logics-flow-manager/scripts/workflow_audit.py --group-by-doc

# Definition of Done (DoD)
- [ ] Scope implemented and acceptance criteria covered.
- [ ] Validation commands executed and results captured.
- [ ] Linked request/backlog/task docs updated.
- [ ] Status is `Done` and progress is `100%`.

# Report
- Pending implementation.

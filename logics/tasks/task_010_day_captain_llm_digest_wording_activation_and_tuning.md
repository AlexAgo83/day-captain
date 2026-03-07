## task_010_day_captain_llm_digest_wording_activation_and_tuning - Activate and tune bounded LLM wording for delivered digests
> From version: 0.4.0
> Status: Ready
> Understanding: 97%
> Confidence: 95%
> Progress: 0%
> Complexity: High
> Theme: Quality
> Reminder: Update status/understanding/confidence/progress and dependencies/references when you edit this doc.

# Context
- Derived from backlog item `item_004_day_captain_digest_quality_and_email_polish`.
- Source file: `logics/backlog/item_004_day_captain_digest_quality_and_email_polish.md`.
- Related request(s): `req_004_day_captain_digest_quality_and_email_polish`.
- Depends on: `task_005_day_captain_llm_digest_wording_for_shortlisted_items`, `task_007_day_captain_mailbox_delivery_end_to_end_validation`.
- Delivery target: move the LLM wording layer from “implemented in code” to “configured and tuned in real delivered digests” while preserving deterministic fallback and bounded cost.

```mermaid
flowchart LR
    Backlog[Backlog: `item_004_day_captain_digest_quality_and_email_polish`] --> Step1[Enable and configure bounded LLM wording locally]
    Step1 --> Step2[Tune prompts/settings for delivered digests]
    Step2 --> Step3[Validate wording quality and fallback behavior]
    Step3 --> Validation[Validation]
    Validation --> Report[Report and Done]
```

# Plan
- [ ] 1. Configure the bounded LLM wording path for real delivered digest runs.
- [ ] 2. Tune the wording behavior so summaries sound more assistant-like while staying factual and concise.
- [ ] 3. Validate that fallback behavior remains safe when the LLM path is disabled or fails.
- [ ] 4. Validate the wording quality on a real delivered digest.
- [ ] FINAL: Update related Logics docs

# AC Traceability
- AC3 -> Plan step 1 activates the existing LLM path. Proof: task explicitly configures bounded LLM wording for delivered digests.
- AC4 -> Plan step 2 improves assistant-like wording. Proof: task explicitly tunes summary tone and quality.
- AC5 -> Plan step 4 validates mailbox output. Proof: task explicitly requires a real delivered digest review.
- AC7 -> Plan steps 1 through 3 preserve bounded operation. Proof: task explicitly keeps fallback and bounded-cost behavior in scope.

# Links
- Backlog item: `item_004_day_captain_digest_quality_and_email_polish`
- Request(s): `req_004_day_captain_digest_quality_and_email_polish`

# Validation
- python3 -m unittest tests.test_llm tests.test_app tests.test_settings
- python3 -m unittest discover -s tests
- PYTHONPATH=src python3 -m day_captain morning-digest --delivery-mode graph_send --force
- delivered email review in Outlook
- python3 logics/skills/logics-doc-linter/scripts/logics_lint.py --require-status
- python3 logics/skills/logics-flow-manager/scripts/workflow_audit.py --group-by-doc

# Definition of Done (DoD)
- [ ] Scope implemented and acceptance criteria covered.
- [ ] Validation commands executed and results captured.
- [ ] Linked request/backlog/task docs updated.
- [ ] Status is `Done` and progress is `100%`.

# Report
- Pending implementation.

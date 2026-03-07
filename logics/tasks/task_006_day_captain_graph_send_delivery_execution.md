## task_006_day_captain_graph_send_delivery_execution - Implement real Graph sendMail execution for digest delivery
> From version: 0.3.0
> Status: Ready
> Understanding: 98%
> Confidence: 96%
> Progress: 0%
> Complexity: High
> Theme: Delivery
> Reminder: Update status/understanding/confidence/progress and dependencies/references when you edit this doc.

# Context
- Derived from backlog item `item_003_day_captain_graph_send_and_mailbox_delivery_validation`.
- Source file: `logics/backlog/item_003_day_captain_graph_send_and_mailbox_delivery_validation.md`.
- Related request(s): `req_003_day_captain_graph_send_and_mailbox_delivery_validation`.
- Depends on: `task_001_day_captain_graph_ingestion_and_storage`, `task_002_day_captain_digest_scoring_recall_and_delivery`, `task_005_day_captain_llm_digest_wording_for_shortlisted_items`.
- Delivery target: change `graph_send` from a rendered payload-only mode into a real delegated Graph delivery path with explicit send prerequisites and automated coverage.

```mermaid
flowchart LR
    Backlog[Backlog: `item_003_day_captain_graph_send_and_mailbox_delivery_validation`] --> Step1[Add Graph send adapter support and config/auth guardrails]
    Step1 --> Step2[Execute sendMail for graph_send delivery]
    Step2 --> Step3[Add tests and docs for the send path]
    Step3 --> Validation[Validation]
    Validation --> Report[Report and Done]
```

# Plan
- [ ] 1. Extend the Graph adapter layer with a POST/send capability suitable for delegated `sendMail`.
- [ ] 2. Wire `graph_send` delivery mode to execute the real send operation when explicitly enabled and correctly authorized.
- [ ] 3. Add clear failure behavior for missing `Mail.Send`, disabled send mode, or provider errors without breaking `json` mode.
- [ ] 4. Add focused tests plus README/config updates for the send flow.
- [ ] FINAL: Update related Logics docs

# AC Traceability
- AC1 -> Plan step 2 implements real delivery. Proof: task explicitly executes delegated `sendMail`.
- AC2 -> Plan steps 1 and 3 enforce prerequisites. Proof: task explicitly covers send-mode and auth guardrails.
- AC3 -> Plan step 3 preserves existing behavior. Proof: task explicitly protects `json` mode and non-send flows.
- AC4 -> Plan step 4 adds automated coverage. Proof: task explicitly requires tests for the send path.
- AC6 -> Plan steps 1 and 2 preserve deployment fit. Proof: task keeps current local and hosted flows in scope.
- AC7 -> Plan step 4 updates docs. Proof: task explicitly requires README/config updates.

# Links
- Backlog item: `item_003_day_captain_graph_send_and_mailbox_delivery_validation`
- Request(s): `req_003_day_captain_graph_send_and_mailbox_delivery_validation`

# Validation
- python3 -m unittest tests.test_graph_client tests.test_app tests.test_delivery_contract
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

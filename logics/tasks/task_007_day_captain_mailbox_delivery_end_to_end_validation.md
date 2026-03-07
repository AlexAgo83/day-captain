## task_007_day_captain_mailbox_delivery_end_to_end_validation - Validate delegated Outlook delivery end to end in the real mailbox
> From version: 0.3.0
> Status: Ready
> Understanding: 98%
> Confidence: 95%
> Progress: 0%
> Complexity: Medium
> Theme: Delivery
> Reminder: Update status/understanding/confidence/progress and dependencies/references when you edit this doc.

# Context
- Derived from backlog item `item_003_day_captain_graph_send_and_mailbox_delivery_validation`.
- Source file: `logics/backlog/item_003_day_captain_graph_send_and_mailbox_delivery_validation.md`.
- Related request(s): `req_003_day_captain_graph_send_and_mailbox_delivery_validation`.
- Depends on: `task_006_day_captain_graph_send_delivery_execution`.
- Delivery target: confirm that the local delegated Graph send flow can produce a real message in the intended Outlook mailbox with the required scope and runtime configuration.

```mermaid
flowchart LR
    Backlog[Backlog: `item_003_day_captain_graph_send_and_mailbox_delivery_validation`] --> Step1[Enable Mail.Send and graph_send config locally]
    Step1 --> Step2[Refresh delegated auth with the required scope]
    Step2 --> Step3[Run a real digest send and verify mailbox receipt]
    Step3 --> Validation[Validation]
    Validation --> Report[Report and Done]
```

# Plan
- [ ] 1. Update local config to enable `graph_send`, explicit send mode, and `Mail.Send` in delegated scopes.
- [ ] 2. Re-run delegated auth login so the local token cache contains the required send scope.
- [ ] 3. Execute a real local digest send and confirm the message is received in the target mailbox.
- [ ] 4. Capture the exact validation outcome, observed constraints, and any follow-up gaps.
- [ ] FINAL: Update related Logics docs

# AC Traceability
- AC2 -> Plan steps 1 and 2 validate prerequisites. Proof: task explicitly requires send-mode config and refreshed delegated auth.
- AC5 -> Plan step 3 validates real-world delivery. Proof: task explicitly requires mailbox receipt confirmation.
- AC7 -> Plan steps 1 and 4 update the operational path. Proof: task explicitly captures config/auth/validation reality.
- AC8 -> Plan steps 1 through 4 keep external proof separate from code implementation. Proof: this task is exclusively about end-to-end validation.

# Links
- Backlog item: `item_003_day_captain_graph_send_and_mailbox_delivery_validation`
- Request(s): `req_003_day_captain_graph_send_and_mailbox_delivery_validation`

# Validation
- set -a && source .env && set +a
- PYTHONPATH=src python3 -m day_captain auth login
- PYTHONPATH=src python3 -m day_captain morning-digest --delivery-mode graph_send --force
- mailbox receipt check in Outlook
- python3 logics/skills/logics-doc-linter/scripts/logics_lint.py --require-status
- python3 logics/skills/logics-flow-manager/scripts/workflow_audit.py --group-by-doc

# Definition of Done (DoD)
- [ ] Scope implemented and acceptance criteria covered.
- [ ] Validation commands executed and results captured.
- [ ] Linked request/backlog/task docs updated.
- [ ] Status is `Done` and progress is `100%`.

# Report
- Pending implementation and real mailbox validation.

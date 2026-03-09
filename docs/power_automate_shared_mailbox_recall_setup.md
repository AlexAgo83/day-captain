# Power Automate Shared Mailbox Recall Setup

Use this runbook to bridge inbound emails sent to `daycaptain@...` into the hosted Day Captain endpoint `POST /jobs/email-command-recall`.

Hosted prerequisites for this flow:
- `DAY_CAPTAIN_GRAPH_AUTH_MODE=app_only`
- `DAY_CAPTAIN_GRAPH_SEND_ENABLED=true`
- `DAY_CAPTAIN_EMAIL_COMMAND_ALLOWED_SENDERS` configured with the bounded sender allowlist
- if several hosted target users are configured, helper senders must use explicit `sender=target` mappings such as `assistant@example.com=alice@example.com`

## Goal

- Let a user send `recall`, `recall-today`, or `recall-week` to the shared mailbox.
- Use Power Automate as the first inbound trigger instead of building a Graph webhook immediately.
- Keep Day Captain responsible for authorization, duplicate suppression, and digest delivery.

## Prerequisites

- The hosted Day Captain service is deployed and reachable.
- Render env includes:
  - `DAY_CAPTAIN_JOB_SECRET`
  - `DAY_CAPTAIN_GRAPH_SENDER_USER_ID`
  - `DAY_CAPTAIN_EMAIL_COMMAND_ALLOWED_SENDERS`
- The shared mailbox exists in Exchange Online, for example `daycaptain@company.com`.
- The operator account used in Power Automate has `Full Access` to the shared mailbox.
- The operator account can open the shared mailbox in Outlook on the web before attempting the Power Automate flow.

## Trigger

Create an automated cloud flow with:

- Connector: `Office 365 Outlook`
- Trigger: `When a new email arrives in a shared mailbox (V2)`

Recommended trigger values:

- `Original mailbox address`: `daycaptain@company.com`
- `Folder`: select the mailbox inbox from the picker when possible
- `Include attachments`: `No`
- `Only with attachments`: `No`
- `Importance`: `Any`
- `Subject filter`: `recall`

Notes:

- If the trigger fails with `Inbox not found`, prefer selecting the folder from the picker instead of typing it manually.
- If the trigger fails with `Root not found` or `403 Forbidden`, the mailbox permissions are not yet propagated or the Power Automate Outlook connection needs to be recreated.

## HTTP action

Add a premium `HTTP` action after the trigger.

- `Method`: `POST`
- `URI`: `https://your-service.onrender.com/jobs/email-command-recall`

Headers:

```json
{
  "Content-Type": "application/json",
  "X-Day-Captain-Secret": "REPLACE_WITH_DAY_CAPTAIN_JOB_SECRET"
}
```

Body:

```json
{
  "command_message_id": "@{triggerOutputs()?['body/id']}",
  "sender_address": "@{triggerOutputs()?['body/from']?['emailAddress']?['address']}",
  "command_text": "@{toLower(trim(triggerOutputs()?['body/subject']))}",
  "subject": "@{triggerOutputs()?['body/subject']}",
  "body": "@{triggerOutputs()?['body/bodyPreview']}"
}
```

Notes:

- In the expression editor, enter expressions without `@{...}`.
- In the JSON body itself, keep the full `@{...}` form.

## Test procedure

1. Save the flow.
2. Start a manual test from Power Automate.
3. Send a new email to `daycaptain@company.com` with subject `recall-week`.
4. Confirm the trigger succeeds.
5. Confirm the HTTP action returns `200`.
6. Confirm Day Captain replies with the generated digest.

## Troubleshooting

- `Root not found`:
  - The shared mailbox is not accessible yet through the connector.
  - Recheck Exchange permissions and wait for propagation.
- `403 Forbidden`:
  - The mailbox is found but the Power Automate account still lacks effective access.
  - Recreate the `Office 365 Outlook` connection after permissions propagate.
- No run appears:
  - The email may not have reached the shared mailbox inbox.
  - The flow may still be waiting for a new event after entering test mode.
- Trigger works but HTTP fails:
  - Recheck `X-Day-Captain-Secret`
  - Recheck the Render service URL
  - Recheck whether the sender is allowed by `DAY_CAPTAIN_EMAIL_COMMAND_ALLOWED_SENDERS`

## Security follow-up

- Rotate `DAY_CAPTAIN_JOB_SECRET` after any debugging session where it was exposed in screenshots or shared in plain text.
- Update both Render and Power Automate with the rotated secret before resuming tests.

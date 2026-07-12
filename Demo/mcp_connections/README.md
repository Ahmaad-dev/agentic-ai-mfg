# AP5 — MCP review integration

## Implemented prototype

`tools.py` is the small internal adapter: every tool delegates database access to existing
functions in `db/repository.py`. `notifier.py` adds the enterprise workflow. A newly inserted
`pending_review` proposal invokes the configured provider and includes this deep link:

`{APP_BASE_URL}/review.html?id={proposal_id}`

The generator treats notification as best-effort: a provider/configuration failure is reported but
never rolls back or interrupts proposal persistence. Re-generating the same deterministic proposal
ID does not send another notification.

Azure Communication Services configuration in `demo/.env`:

```dotenv
NOTIFICATION_CHANNEL=acs
ACS_CONNECTION_STRING=<secret>
ACS_SENDER_EMAIL=<verified MailFrom address>
NOTIFICATION_RECIPIENT_EMAIL=<reviewer address>
APP_BASE_URL=http://localhost:8000
```

Provider imports are lazy. An unset `NOTIFICATION_CHANNEL` skips silently. Secrets are read only
from environment variables / `.env`; none are stored in source code.

## Full MCP-server variant

`server.py` registers the same adapter functions as standard FastMCP tools. This implements the
server side, but PT4 does not configure or authenticate a production MCP client. Run locally from
`demo/` after installing `requirements.txt`:

```powershell
python -m mcp_connections.server
```

The default transport is stdio. A production deployment can switch to Streamable HTTP and add OAuth
token validation; token validation is deliberately out of scope for PT4.

## Conversational email workflow

The chat UI exposes an **E-Mail** entry through its plus menu. Selecting it routes the request to a
dedicated email agent. Natural-language email requests can also be selected by the orchestrator.
The agent may use ordinary chat context or, when the user explicitly refers to a snapshot/review,
the existing review tools to add verified case facts and a review deep link.

The workflow is deliberately two-phase:

1. `create_email_draft` stores and displays the exact recipient, subject and body.
2. Further chat messages call `revise_email_draft`; every revision creates a new draft version.
3. Approval-only replies such as `Ja, passt` keep the draft unchanged and do not send it.
4. Only an explicit command such as `Bitte absenden` calls `send_email_draft(..., confirmed=True)`.

Drafts are stored in `email_drafts` and remain attached to the chat session, so the flow survives a
page reload. `send_email_draft` is idempotent, and cancelled or already-sent drafts cannot be sent a
second time. Provider selection and secrets use the same environment-only ACS/SendGrid configuration
shown above; no recipient is fixed in configuration for this general email tool.

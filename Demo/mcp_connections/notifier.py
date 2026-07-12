"""Email provider adapter; delivery occurs only after explicit chat confirmation."""
from __future__ import annotations

import logging
import os
from pathlib import Path

from dotenv import load_dotenv

logger = logging.getLogger(__name__)

load_dotenv(Path(__file__).resolve().parent.parent / ".env")


def _required_env(name: str) -> str:
    value = (os.getenv(name) or "").strip()
    if not value:
        raise RuntimeError(f"{name} is required for the selected notification channel")
    return value


def _send_acs(
    recipient: str,
    subject: str,
    plain: str,
    html_body: str,
) -> dict:
    from azure.communication.email import EmailClient  # lazy: optional provider dependency

    client = EmailClient.from_connection_string(_required_env("ACS_CONNECTION_STRING"))
    message = {
        "senderAddress": _required_env("ACS_SENDER_EMAIL"),
        "recipients": {"to": [{"address": recipient}]},
        "content": {"subject": subject, "plainText": plain, "html": html_body},
    }
    result = client.begin_send(message).result()
    message_id = result.get("id") if isinstance(result, dict) else getattr(result, "id", None)
    return {"sent": True, "channel": "acs", "message_id": message_id}


def _send_sendgrid(
    recipient: str,
    subject: str,
    plain: str,
    html_body: str,
) -> dict:
    from sendgrid import SendGridAPIClient  # lazy: optional provider dependency
    from sendgrid.helpers.mail import Mail

    message = Mail(
        from_email=_required_env("NOTIFICATION_SENDER_EMAIL"),
        to_emails=recipient,
        subject=subject,
        plain_text_content=plain,
        html_content=html_body,
    )
    response = SendGridAPIClient(_required_env("SENDGRID_API_KEY")).send(message)
    return {"sent": True, "channel": "sendgrid", "status_code": response.status_code}


def send_email_message(
    recipient: str,
    subject: str,
    plain: str,
    html_body: str,
) -> dict:
    """Send an explicitly prepared email through the configured provider."""
    channel = (os.getenv("NOTIFICATION_CHANNEL") or "").strip().lower()
    if not channel:
        logger.info("Notification skipped: NOTIFICATION_CHANNEL not set")
        return {"sent": False, "skipped": True, "reason": "NOTIFICATION_CHANNEL not set"}
    if channel == "acs":
        result = _send_acs(recipient, subject, plain, html_body)
    elif channel == "sendgrid":
        result = _send_sendgrid(recipient, subject, plain, html_body)
    else:
        raise ValueError(f"Unsupported NOTIFICATION_CHANNEL {channel!r}; expected 'acs' or 'sendgrid'")
    logger.info("Email sent via %s to %s", channel, recipient)
    return result


def send_proposal_notification(
    proposal_id: str,
    snapshot_id: str,
    error_type: str,
) -> dict:
    """Keep the former hook compatible, but never send mail from proposal generation.

    Email delivery is user-triggered exclusively through the conversational draft flow and
    ``send_email_draft(..., confirmed=True)``.  The runtime hook intentionally remains callable
    so the runtime tool does not need to be changed.
    """
    logger.info(
        "Automatic review notification skipped for proposal %s: email requires explicit chat confirmation",
        proposal_id,
    )
    return {
        "sent": False,
        "skipped": True,
        "reason": "automatic review notifications disabled; explicit chat confirmation required",
        "proposal_id": proposal_id,
    }

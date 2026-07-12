"""Repository-backed tools exposed through MCP in :mod:`mcp_connections.server`."""
from __future__ import annotations

import datetime as _dt
import re
import sys
from collections import Counter
from pathlib import Path
from typing import Any

# Keep the adapter callable both from ``demo/`` and from the repository root.
_demo_dir = str(Path(__file__).resolve().parent.parent)
if _demo_dir not in sys.path:
    sys.path.insert(0, _demo_dir)

from db import repository as repo  # noqa: E402

# Token-Validierung der MCP-Tools ist out-of-scope für PT4.
MCP_REVIEWER_REF = "mcp_reviewer"
_EMAIL_RE = re.compile(r"^[^\s@]+@[^\s@]+\.[^\s@]+$")


def _json_value(value: Any) -> Any:
    """Convert repository timestamps recursively into MCP/JSON-safe values."""
    if isinstance(value, (_dt.datetime, _dt.date)):
        return value.isoformat()
    if isinstance(value, dict):
        return {key: _json_value(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json_value(item) for item in value]
    return value


def _decision_response(result: dict) -> dict:
    """Add HTTP-like status semantics without introducing an HTTP dependency."""
    outcome = result.get("outcome")
    if outcome == "not_found":
        return {"ok": False, "status_code": 404, "error": "Proposal not found"}
    if outcome == "already_decided":
        return {
            "ok": False,
            "status_code": 409,
            "error": "Proposal has already been decided",
            **result,
        }
    return {
        "ok": True,
        "status_code": 200,
        "application_triggered": False,
        "note": "Decision recorded; applying corrections remains in the existing review workflow.",
        **_json_value(result),
    }


def get_pending_reviews() -> list[dict[str, Any]]:
    """Return every proposal currently awaiting human review."""
    return repo.list_open_proposals_as_dicts()


def get_review_details(proposal_id: str) -> dict[str, Any]:
    """Return one proposal or an HTTP-like 404 result."""
    proposal = repo.get_proposal_as_dict(proposal_id)
    if proposal is None:
        return {
            "ok": False,
            "status_code": 404,
            "error": "Proposal not found",
            "proposal_id": proposal_id,
        }
    return {"ok": True, "status_code": 200, "proposal": proposal}


def approve_correction(proposal_id: str, comment: str = "") -> dict[str, Any]:
    """Record approval of a pending proposal; application remains in the review workflow."""
    return _decision_response(
        repo.decide_proposal(
            proposal_id=proposal_id,
            decision="approve",
            comment=comment or None,
            reviewer_ref=MCP_REVIEWER_REF,
        )
    )


def reject_correction(proposal_id: str, comment: str) -> dict[str, Any]:
    """Record rejection of a pending proposal; a non-empty comment is required."""
    if not isinstance(comment, str) or not comment.strip():
        return {
            "ok": False,
            "status_code": 400,
            "error": "A non-empty comment is required to reject a proposal",
            "proposal_id": proposal_id,
        }
    return _decision_response(
        repo.decide_proposal(
            proposal_id=proposal_id,
            decision="reject",
            comment=comment.strip(),
            reviewer_ref=MCP_REVIEWER_REF,
        )
    )


def modify_correction(
    proposal_id: str,
    final_value: str,
    comment: str,
) -> dict[str, Any]:
    """Record a human replacement value for a pending proposal."""
    if final_value is None:
        return {
            "ok": False,
            "status_code": 400,
            "error": "final_value is required to modify a proposal",
            "proposal_id": proposal_id,
        }
    return _decision_response(
        repo.decide_proposal(
            proposal_id=proposal_id,
            decision="modify",
            final_value=final_value,
            comment=comment or None,
            reviewer_ref=MCP_REVIEWER_REF,
        )
    )


def get_snapshot_status(snapshot_id: str) -> dict[str, Any]:
    """Summarise open reviews and recorded decisions for one snapshot."""
    pending = [
        proposal
        for proposal in repo.list_open_proposals_as_dicts()
        if proposal.get("snapshot_id") == snapshot_id
    ]
    decisions = repo.get_decisions_for_snapshot(snapshot_id)
    if not pending and not decisions:
        return {
            "ok": False,
            "status_code": 404,
            "error": "Snapshot not found in review data",
            "snapshot_id": snapshot_id,
        }
    return {
        "ok": True,
        "status_code": 200,
        "snapshot_id": snapshot_id,
        "open_review_count": len(pending),
        "decision_count": len(decisions),
        "pending_reviews": pending,
        "decisions": decisions,
    }


def get_dashboard_metrics() -> dict[str, Any]:
    """Return compact AP6 metrics derived from the existing repository data pull."""
    data = repo.fetch_metrics_data()
    decisions = Counter(review.get("decision") for review in data["reviews"])
    statuses = Counter(proposal.get("status") for proposal in data["proposals"])
    return {
        "snapshot_count": data["snapshot_count"],
        "proposal_count": len(data["proposals"]),
        "open_review_count": statuses.get("pending_review", 0),
        "decision_count": len(data["reviews"]),
        "approve_count": decisions.get("approve", 0),
        "reject_count": decisions.get("reject", 0),
        "modify_count": decisions.get("modify", 0),
        "agent_run_count": len(data["agent_runs"]),
    }


def _email_error(message: str, status_code: int = 400, **extra: Any) -> dict[str, Any]:
    return {"ok": False, "status_code": status_code, "error": message, **extra}


def create_email_draft(
    session_id: int,
    recipient: str,
    subject: str,
    body_plain: str,
    body_html: str = "",
    context_summary: str = "",
) -> dict[str, Any]:
    """Persist an email preview. This tool never sends an email."""
    recipient = (recipient or "").strip()
    subject = (subject or "").strip()
    body_plain = (body_plain or "").strip()
    if not _EMAIL_RE.match(recipient):
        return _email_error("A valid recipient email address is required")
    if not subject:
        return _email_error("Email subject is required")
    if not body_plain:
        return _email_error("Email body is required")
    try:
        draft = repo.create_email_draft(
            session_id=session_id,
            recipient=recipient,
            subject=subject,
            body_plain=body_plain,
            body_html=body_html or None,
            context_summary=context_summary or None,
        )
    except ValueError as exc:
        return _email_error(str(exc), 404)
    return {"ok": True, "status_code": 201, "draft": draft}


def get_email_draft(draft_id: str) -> dict[str, Any]:
    """Return one persisted email draft."""
    draft = repo.get_email_draft(draft_id)
    if draft is None:
        return _email_error("Email draft not found", 404, draft_id=draft_id)
    return {"ok": True, "status_code": 200, "draft": draft}


def revise_email_draft(
    draft_id: str,
    recipient: str,
    subject: str,
    body_plain: str,
    body_html: str = "",
    context_summary: str = "",
) -> dict[str, Any]:
    """Replace the visible content of an unsent draft; this tool never sends."""
    recipient = (recipient or "").strip()
    subject = (subject or "").strip()
    body_plain = (body_plain or "").strip()
    if not _EMAIL_RE.match(recipient):
        return _email_error("A valid recipient email address is required")
    if not subject or not body_plain:
        return _email_error("Email subject and body are required")
    try:
        draft = repo.update_email_draft(
            draft_id,
            recipient=recipient,
            subject=subject,
            body_plain=body_plain,
            body_html=body_html or None,
            context_summary=context_summary or None,
        )
    except ValueError as exc:
        return _email_error(str(exc), 409, draft_id=draft_id)
    if draft is None:
        return _email_error("Email draft not found", 404, draft_id=draft_id)
    return {"ok": True, "status_code": 200, "draft": draft}


def send_email_draft(draft_id: str, confirmed: bool = False) -> dict[str, Any]:
    """Send the exact persisted draft, but only after explicit user confirmation."""
    draft = repo.get_email_draft(draft_id)
    if draft is None:
        return _email_error("Email draft not found", 404, draft_id=draft_id)
    if draft["status"] == "sent":
        return {
            "ok": True,
            "status_code": 200,
            "already_sent": True,
            "draft": draft,
        }
    if not confirmed:
        return _email_error(
            "Explicit confirmation is required before sending",
            409,
            draft_id=draft_id,
        )
    if draft["status"] != "draft":
        return _email_error(
            f"Email draft is {draft['status']!r}, not sendable",
            409,
            draft_id=draft_id,
        )

    from mcp_connections.notifier import send_email_message

    result = send_email_message(
        draft["recipient"],
        draft["subject"],
        draft["body_plain"],
        draft["body_html"] or "",
    )
    if not result.get("sent"):
        return _email_error(
            result.get("reason") or "Email provider did not accept the message",
            503,
            draft_id=draft_id,
            provider_result=result,
        )
    sent = repo.mark_email_draft_sent(draft_id, result.get("message_id"))
    return {
        "ok": True,
        "status_code": 200,
        "sent": True,
        "channel": result.get("channel"),
        "draft": sent,
    }


def cancel_email_draft(draft_id: str) -> dict[str, Any]:
    """Cancel an unsent email draft while preserving its audit record."""
    try:
        draft = repo.cancel_email_draft(draft_id)
    except ValueError as exc:
        return _email_error(str(exc), 409, draft_id=draft_id)
    if draft is None:
        return _email_error("Email draft not found", 404, draft_id=draft_id)
    return {"ok": True, "status_code": 200, "draft": draft}

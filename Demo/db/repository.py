"""
PT4 Persistence Layer — repository / CRUD helpers (AP2.3).

Keeps `web_server.py` slim: all DB access goes through these functions.
Every write is transactional via `session_scope()`.

Design notes:
- `sessions.id` is an integer PK; the web layer uses a string chat-session id,
  which is stored in `sessions.user_ref` and mapped lazily by the caller.
- `save_proposal()` maps the central proposal record (from
  `generate_correction_llm.save_central_proposal_record`) into the `proposals`
  table and upserts idempotently by `proposal_id`.
- Review/memory helpers exist for AP3/AP7; the tables are created now.
"""
from __future__ import annotations

import datetime as _dt
import logging
import uuid
from contextlib import contextmanager
from typing import Any, Optional

from . import models
from .session import get_sessionmaker

logger = logging.getLogger(__name__)

#: The only proposal status that may still receive a human decision (AP3.2).
PENDING_STATUS = "pending_review"

#: decision -> resulting proposal status. "applied" is set later by AP3.3.
DECISION_STATUS = {
    "approve": "approved",
    "reject": "rejected",
    "modify": "modified",
}


@contextmanager
def session_scope():
    """Provide a transactional scope around a series of operations."""
    factory = get_sessionmaker()
    db = factory()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def _parse_dt(value: Any) -> Optional[_dt.datetime]:
    """Best-effort ISO8601 -> datetime; returns None on failure."""
    if isinstance(value, _dt.datetime):
        return value
    if isinstance(value, str):
        try:
            return _dt.datetime.fromisoformat(value)
        except ValueError:
            return None
    return None


# --------------------------------------------------------------------------- #
# sessions / messages / agent_runs
# --------------------------------------------------------------------------- #
def create_session(snapshot_id: Optional[str] = None, user_ref: Optional[str] = None) -> int:
    """Create a new session row and return its id."""
    with session_scope() as db:
        row = models.Session(snapshot_id=snapshot_id, user_ref=user_ref)
        db.add(row)
        db.flush()
        return row.id


def add_message(
    session_id: int,
    role: str,
    content: str,
    agent_name: Optional[str] = None,
) -> int:
    """Persist a user/assistant message and return its id."""
    with session_scope() as db:
        row = models.Message(
            session_id=session_id,
            role=role,
            content=content,
            agent_name=agent_name,
        )
        db.add(row)
        db.flush()
        return row.id


#: How much of the first user message is used as a session title.
_TITLE_MAX = 60


def _derive_title(first_user_message: Optional[str]) -> str:
    """Session title = the first user message, shortened. No LLM call, no extra column."""
    text = (first_user_message or "").strip().replace("\n", " ")
    if not text:
        return "Neuer Chat"
    return text if len(text) <= _TITLE_MAX else text[: _TITLE_MAX - 1].rstrip() + "…"


def list_sessions_as_dicts(limit: int = 50) -> list[dict]:
    """
    AP4.6: All chat sessions that actually contain messages, newest activity first.

    Sessions without any message are skipped — every page load used to create one, so the
    table is full of empty rows; showing them would drown the real conversations.
    """
    with session_scope() as db:
        rows = db.query(models.Session).order_by(models.Session.id.desc()).all()
        out = []
        for s in rows:
            msgs = sorted(s.messages, key=lambda m: m.id)
            if not msgs:
                continue
            first_user = next((m.content for m in msgs if m.role == "user"), None)
            last = msgs[-1]
            out.append(
                {
                    "session_id": s.id,
                    "title": _derive_title(first_user),
                    "message_count": len(msgs),
                    "started_at": s.started_at.isoformat() if s.started_at else None,
                    "last_activity": last.created_at.isoformat() if last.created_at else None,
                    "snapshot_id": s.snapshot_id,
                }
            )
            if len(out) >= limit:
                break
        return out


def get_messages_as_dicts(session_id: int) -> list[dict]:
    """AP4.6: The full message history of one session, oldest first (for replaying a chat)."""
    with session_scope() as db:
        msgs = (
            db.query(models.Message)
            .filter(models.Message.session_id == session_id)
            .order_by(models.Message.id.asc())
            .all()
        )
        return [
            {
                "role": m.role,
                "content": m.content,
                "agent_name": m.agent_name,
                "created_at": m.created_at.isoformat() if m.created_at else None,
            }
            for m in msgs
        ]


def session_exists(session_id: int) -> bool:
    with session_scope() as db:
        return db.get(models.Session, session_id) is not None


def add_agent_run(
    session_id: int,
    agent_name: Optional[str] = None,
    tool_name: Optional[str] = None,
    input_summary: Optional[str] = None,
    output_summary: Optional[str] = None,
    status: Optional[str] = None,
    tokens_prompt: Optional[int] = None,
    tokens_completion: Optional[int] = None,
    cost_estimate: Optional[float] = None,
    duration_ms: Optional[int] = None,
) -> int:
    """Persist one agent/tool execution (incl. token/cost telemetry) and return its id."""
    with session_scope() as db:
        row = models.AgentRun(
            session_id=session_id,
            agent_name=agent_name,
            tool_name=tool_name,
            input_summary=input_summary,
            output_summary=output_summary,
            status=status,
            tokens_prompt=tokens_prompt,
            tokens_completion=tokens_completion,
            cost_estimate=cost_estimate,
            duration_ms=duration_ms,
        )
        db.add(row)
        db.flush()
        return row.id


# --------------------------------------------------------------------------- #
# snapshots_meta
# --------------------------------------------------------------------------- #
def upsert_snapshot_meta(snapshot_id: str, **fields: Any) -> None:
    """Insert or update a snapshots_meta row (only provided fields are set)."""
    if not snapshot_id:
        return
    with session_scope() as db:
        row = db.get(models.SnapshotMeta, snapshot_id)
        if row is None:
            row = models.SnapshotMeta(snapshot_id=snapshot_id)
            db.add(row)
        for key, value in fields.items():
            if hasattr(row, key) and value is not None:
                setattr(row, key, value)


# --------------------------------------------------------------------------- #
# proposals
# --------------------------------------------------------------------------- #
def save_proposal(record: dict) -> Optional[str]:
    """
    Upsert a proposal from the central proposal record (idempotent by proposal_id).

    Expects the wrapper produced by save_central_proposal_record(), i.e.:
        {proposal_id, snapshot_id, status, confidence_score, created_at,
         proposal: {error_analyzed, correction_proposal, ...}}
    """
    proposal_id = record.get("proposal_id")
    if not proposal_id:
        return None

    inner = record.get("proposal", {}) or {}
    cp = inner.get("correction_proposal", {}) or {}
    error_analyzed = inner.get("error_analyzed", {}) or {}
    snapshot_id = record.get("snapshot_id")

    # Ensure the parent snapshots_meta row exists (FK safety on Azure SQL).
    if snapshot_id:
        upsert_snapshot_meta(snapshot_id)

    with session_scope() as db:
        row = db.get(models.Proposal, proposal_id)
        is_new = row is None
        if is_new:
            row = models.Proposal(proposal_id=proposal_id)
            db.add(row)
        row.snapshot_id = snapshot_id
        row.error_type = error_analyzed.get("error_type")
        row.target_path = cp.get("target_path")
        row.affected_entity = cp.get("target_path")
        row.old_value = cp.get("current_value")
        row.suggested_value = cp.get("new_value")
        row.reasoning = cp.get("reasoning")
        row.evidence = cp.get("additional_updates") or []
        row.confidence_score = cp.get("confidence_score", record.get("confidence_score"))
        row.schema_valid = cp.get("schema_valid")
        # AP3.5a guard metadata (target_entity_id may be int/str in the JSON → store as str).
        row.correction_kind = cp.get("correction_kind")
        row.target_entity_type = cp.get("target_entity_type")
        _tid = cp.get("target_entity_id")
        row.target_entity_id = str(_tid) if _tid is not None else None
        row.identity_check_supported = cp.get("identity_check_supported")
        # AP4.5 confidence transparency
        row.value_grounded = cp.get("value_grounded")
        row.value_grounded_reason = cp.get("value_grounded_reason")
        row.confidence_rationale = cp.get("confidence_rationale")

        # `proposal_id` is deterministic ({snapshot_id}__iteration-{N}), so re-running
        # the generator hits an existing row. A human decision must survive that:
        # never downgrade a decided proposal back to pending_review (AP3.2).
        if is_new or _is_still_undecided(db, row):
            row.status = cp.get("status") or record.get("status") or "pending_review"
        else:
            logger.warning(
                "save_proposal: keeping decided status %r for proposal_id=%s "
                "(regeneration must not reset a human decision)",
                row.status,
                proposal_id,
            )

        created = _parse_dt(record.get("created_at"))
        if created is not None:
            row.created_at = created
        db.flush()
        return proposal_id


def _is_still_undecided(db: Any, row: models.Proposal) -> bool:
    """True only if the proposal is pending_review AND carries no review row yet."""
    if row.status != PENDING_STATUS:
        return False
    existing_review = (
        db.query(models.Review)
        .filter(models.Review.proposal_id == row.proposal_id)
        .first()
    )
    return existing_review is None


def get_proposal(proposal_id: str) -> Optional[models.Proposal]:
    """Return a proposal by id (detached copy after the scope closes)."""
    with session_scope() as db:
        return db.get(models.Proposal, proposal_id)


def list_open_proposals() -> list[models.Proposal]:
    """Return all proposals still awaiting review (status == pending_review)."""
    with session_scope() as db:
        return (
            db.query(models.Proposal)
            .filter(models.Proposal.status == "pending_review")
            .order_by(models.Proposal.created_at.desc())
            .all()
        )


def list_open_proposals_as_dicts() -> list[dict]:
    """
    AP3.1: Return open proposals as plain dicts (safe outside session scope).
    Serialises datetime fields to ISO-8601 strings.
    Returns the short-form fields needed by the list endpoint.
    """
    with session_scope() as db:
        rows = (
            db.query(models.Proposal)
            .filter(models.Proposal.status == "pending_review")
            .order_by(models.Proposal.created_at.desc())
            .all()
        )
        return [
            {
                "proposal_id": r.proposal_id,
                "snapshot_id": r.snapshot_id,
                "error_type": r.error_type,
                "target_path": r.target_path,
                "confidence_score": r.confidence_score,
                "status": r.status,
                "correction_kind": r.correction_kind,
                "target_entity_type": r.target_entity_type,
                "target_entity_id": r.target_entity_id,
                "identity_check_supported": r.identity_check_supported,
                "value_grounded": r.value_grounded,
                "value_grounded_reason": r.value_grounded_reason,
                "confidence_rationale": r.confidence_rationale,
                "created_at": r.created_at.isoformat() if r.created_at else None,
            }
            for r in rows
        ]


def get_proposal_as_dict(proposal_id: str) -> Optional[dict]:
    """
    AP3.1: Return a single proposal as a plain dict (safe outside session scope).
    Returns None if not found.
    Includes the full detail fields needed by the detail endpoint.
    """
    with session_scope() as db:
        r = db.get(models.Proposal, proposal_id)
        if r is None:
            return None
        return {
            "proposal_id": r.proposal_id,
            "snapshot_id": r.snapshot_id,
            "error_type": r.error_type,
            "affected_entity": r.affected_entity,
            "target_path": r.target_path,
            "old_value": r.old_value,
            "suggested_value": r.suggested_value,
            "reasoning": r.reasoning,
            "evidence": r.evidence,
            "confidence_score": r.confidence_score,
            "schema_valid": r.schema_valid,
            "status": r.status,
            "correction_kind": r.correction_kind,
            "target_entity_type": r.target_entity_type,
            "target_entity_id": r.target_entity_id,
            "identity_check_supported": r.identity_check_supported,
            "value_grounded": r.value_grounded,
            "value_grounded_reason": r.value_grounded_reason,
            "confidence_rationale": r.confidence_rationale,
            "created_at": r.created_at.isoformat() if r.created_at else None,
        }


def get_decisions_for_snapshot(snapshot_id: str) -> list[dict]:
    """
    All human review decisions made on a snapshot, newest first.

    Exists so the CHAT AGENT can answer "what was the solution?" truthfully. Without it the
    chat only sees the conversation history — which contains the AI's PROPOSAL, not the
    human's decision (that happens in the review board, outside the chat). It therefore used
    to report the AI's rejected value as the applied one.

    `final_value` is the value that was really applied (the human's on `modify`, the AI's on
    `approve`); `ai_value` is what the AI had proposed, kept for contrast.
    """
    with session_scope() as db:
        rows = (
            db.query(models.Review, models.Proposal)
            .join(models.Proposal, models.Review.proposal_id == models.Proposal.proposal_id)
            .filter(models.Proposal.snapshot_id == snapshot_id)
            .order_by(models.Review.decided_at.desc(), models.Review.id.desc())
            .all()
        )
        return [
            {
                "proposal_id": p.proposal_id,
                "error_type": p.error_type,
                "target_path": p.target_path,
                "decision": rv.decision,
                "applied_value": rv.final_value,
                "ai_value": p.suggested_value,
                "reviewer_comment": rv.comment,
                "proposal_status": p.status,
                "decided_at": rv.decided_at.isoformat() if rv.decided_at else None,
            }
            for rv, p in rows
        ]


# --------------------------------------------------------------------------- #
# reviews (AP3) / memory_items (AP7) — helpers ready, tables created now
# --------------------------------------------------------------------------- #
def create_review(
    proposal_id: str,
    decision: str,
    final_value: Any = None,
    comment: Optional[str] = None,
    reviewer_ref: Optional[str] = None,
    revalidation_result: Any = None,
) -> int:
    """Persist a human review decision and return its id (used from AP3)."""
    with session_scope() as db:
        row = models.Review(
            proposal_id=proposal_id,
            decision=decision,
            final_value=final_value,
            comment=comment,
            reviewer_ref=reviewer_ref,
            revalidation_result=revalidation_result,
        )
        db.add(row)
        db.flush()
        return row.id


def add_memory_item(**fields: Any) -> int:
    """Persist a memory item (populated from AP7) and return its id."""
    with session_scope() as db:
        row = models.MemoryItem(**fields)
        db.add(row)
        db.flush()
        return row.id


def get_decision_state(proposal_id: str) -> Optional[dict]:
    """
    AP3.3b: Everything the apply path needs to decide whether it may write.

    Returns None if the proposal does not exist. Otherwise:
        {proposal_id, snapshot_id, status, review_count, suggested_value}

    `review_count` is the proof that a human actually decided: the apply path requires
    both a decided status AND at least one review row.
    """
    with session_scope() as db:
        row = db.get(models.Proposal, proposal_id)
        if row is None:
            return None
        review_count = (
            db.query(models.Review)
            .filter(models.Review.proposal_id == proposal_id)
            .count()
        )
        return {
            "proposal_id": row.proposal_id,
            "snapshot_id": row.snapshot_id,
            "status": row.status,
            "review_count": review_count,
            "suggested_value": row.suggested_value,
        }


def set_proposal_status(proposal_id: str, status: str) -> bool:
    """AP3.3b: Move a proposal to a new status (e.g. -> 'applied'). False if unknown."""
    with session_scope() as db:
        row = db.get(models.Proposal, proposal_id)
        if row is None:
            return False
        row.status = status
        return True


def set_latest_review_revalidation(proposal_id: str, revalidation_result: Any) -> Optional[int]:
    """
    AP3.3b: Attach the re-validation outcome to the most recent review of a proposal.

    Written on success AND on failure, so the audit trail records what the apply attempt
    actually did. Returns the review id, or None if there is no review row.
    """
    with session_scope() as db:
        row = (
            db.query(models.Review)
            .filter(models.Review.proposal_id == proposal_id)
            .order_by(models.Review.decided_at.desc(), models.Review.id.desc())
            .first()
        )
        if row is None:
            return None
        row.revalidation_result = revalidation_result
        db.flush()
        return row.id


def decide_proposal(
    proposal_id: str,
    decision: str,
    final_value: Any = None,
    comment: Optional[str] = None,
    reviewer_ref: Optional[str] = None,
) -> dict:
    """
    AP3.2: Record a human decision on a proposal.

    The `reviews` row and the new `proposals.status` are written in ONE transaction,
    so a recorded decision can never drift apart from the proposal status.

    The pending-check happens inside that transaction: a proposal that already carries
    a decision is left untouched and no second review row is written, so repeating a
    call is safe.

    Does NOT touch snapshot data — applying an approved correction and re-validating
    the snapshot is AP3.3.

    Returns exactly one of:
        {"outcome": "not_found"}
        {"outcome": "already_decided", "proposal_id", "status"}
        {"outcome": "decided", "proposal_id", "status", "decision", "final_value",
         "suggested_value", "comment", "reviewer_ref", "review_id"}
    """
    new_status = DECISION_STATUS[decision]

    with session_scope() as db:
        row = db.get(models.Proposal, proposal_id)
        if row is None:
            return {"outcome": "not_found"}

        if not _is_still_undecided(db, row):
            return {
                "outcome": "already_decided",
                "proposal_id": proposal_id,
                "status": row.status,
            }

        # approve: keep the AI's suggestion as the final value.
        # modify:  the human value overrides it (the AI value stays in
        #          proposals.suggested_value as history).
        # reject:  no final value at all — the proposal is discarded for good.
        if decision == "approve":
            stored_final_value = row.suggested_value
        elif decision == "modify":
            stored_final_value = final_value
        else:
            stored_final_value = None

        review = models.Review(
            proposal_id=proposal_id,
            decision=decision,
            final_value=stored_final_value,
            comment=comment,
            reviewer_ref=reviewer_ref,
        )
        db.add(review)
        row.status = new_status
        db.flush()

        return {
            "outcome": "decided",
            "proposal_id": proposal_id,
            "status": row.status,
            "decision": decision,
            "final_value": stored_final_value,
            "suggested_value": row.suggested_value,
            "comment": comment,
            "reviewer_ref": reviewer_ref,
            "review_id": review.id,
        }


# --------------------------------------------------------------------------- #
# dashboard (AP6.1)
# --------------------------------------------------------------------------- #
def fetch_metrics_data() -> dict:
    """
    AP6.1: Pull everything the dashboard aggregates, in ONE session scope.

    This is deliberately a data pull, not a metric computation: the repository stays a
    thin DB layer, and every KPI definition (and every honesty caveat attached to it)
    lives in `routes/dashboard.py` where it can be read in one place.

    Rows are materialised to plain dicts inside the scope, so callers never touch a
    detached ORM object (same pattern as `list_open_proposals_as_dicts`).

    Only the LATEST review per proposal is returned. `decide_proposal()` already refuses a
    second decision, so today this is a 1:1 join — but a metric that silently double-counts
    if that ever changes would be a bad metric.
    """
    with session_scope() as db:
        proposals = [
            {
                "proposal_id": p.proposal_id,
                "snapshot_id": p.snapshot_id,
                "error_type": p.error_type,
                "target_path": p.target_path,
                "status": p.status,
                "confidence_score": p.confidence_score,
                "value_grounded": p.value_grounded,
                "created_at": p.created_at,
            }
            for p in db.query(models.Proposal).all()
        ]

        # Latest review per proposal (see docstring).
        latest: dict[str, models.Review] = {}
        for rv in (
            db.query(models.Review)
            .order_by(models.Review.decided_at.asc(), models.Review.id.asc())
            .all()
        ):
            latest[rv.proposal_id] = rv
        reviews = [
            {
                "review_id": rv.id,
                "proposal_id": rv.proposal_id,
                "decision": rv.decision,
                "decided_at": rv.decided_at,
                "revalidation_result": rv.revalidation_result,
            }
            for rv in latest.values()
        ]

        runs = [
            {
                "agent_name": r.agent_name,
                "tool_name": r.tool_name,
                "status": r.status,
                "tokens_prompt": r.tokens_prompt,
                "tokens_completion": r.tokens_completion,
                "cost_estimate": r.cost_estimate,
                "duration_ms": r.duration_ms,
                "created_at": r.created_at,   # AP6.4: the dashboard's time filter needs it
            }
            for r in db.query(models.AgentRun).all()
        ]

        return {
            "proposals": proposals,
            "reviews": reviews,
            "agent_runs": runs,
            "snapshot_count": db.query(models.SnapshotMeta).count(),
        }


# --------------------------------------------------------------------------- #
# conversational email drafts (AP5.3)
# --------------------------------------------------------------------------- #
def _email_draft_dict(row: models.EmailDraft) -> dict:
    """Materialise an email draft while its ORM session is still open."""
    return {
        "draft_id": row.id,
        "session_id": row.session_id,
        "recipient": row.recipient,
        "subject": row.subject,
        "body_plain": row.body_plain,
        "body_html": row.body_html,
        "context_summary": row.context_summary,
        "status": row.status,
        "version": row.version,
        "provider_message_id": row.provider_message_id,
        "created_at": row.created_at.isoformat() if row.created_at else None,
        "updated_at": row.updated_at.isoformat() if row.updated_at else None,
        "sent_at": row.sent_at.isoformat() if row.sent_at else None,
    }


def create_email_draft(
    session_id: int,
    recipient: str,
    subject: str,
    body_plain: str,
    body_html: Optional[str] = None,
    context_summary: Optional[str] = None,
) -> dict:
    """Persist a new, unsent email draft for one chat session."""
    with session_scope() as db:
        if db.get(models.Session, session_id) is None:
            raise ValueError(f"Unknown session_id {session_id}")
        row = models.EmailDraft(
            id=str(uuid.uuid4()),
            session_id=session_id,
            recipient=recipient,
            subject=subject,
            body_plain=body_plain,
            body_html=body_html,
            context_summary=context_summary,
            status="draft",
            version=1,
        )
        db.add(row)
        db.flush()
        return _email_draft_dict(row)


def get_email_draft(draft_id: str) -> Optional[dict]:
    """Return one email draft, or None if it does not exist."""
    with session_scope() as db:
        row = db.get(models.EmailDraft, draft_id)
        return _email_draft_dict(row) if row is not None else None


def get_latest_email_draft_for_session(
    session_id: int,
    status: Optional[str] = "draft",
) -> Optional[dict]:
    """Return the newest draft in a session, optionally filtered by status."""
    with session_scope() as db:
        query = db.query(models.EmailDraft).filter(models.EmailDraft.session_id == session_id)
        if status is not None:
            query = query.filter(models.EmailDraft.status == status)
        row = query.order_by(
            models.EmailDraft.updated_at.desc(), models.EmailDraft.created_at.desc()
        ).first()
        return _email_draft_dict(row) if row is not None else None


def update_email_draft(
    draft_id: str,
    *,
    recipient: Optional[str] = None,
    subject: Optional[str] = None,
    body_plain: Optional[str] = None,
    body_html: Optional[str] = None,
    context_summary: Optional[str] = None,
) -> Optional[dict]:
    """Revise an unsent draft and increment its visible version."""
    with session_scope() as db:
        row = db.get(models.EmailDraft, draft_id)
        if row is None:
            return None
        if row.status != "draft":
            raise ValueError(f"Email draft {draft_id} is {row.status!r}, not editable")
        updates = {
            "recipient": recipient,
            "subject": subject,
            "body_plain": body_plain,
            "body_html": body_html,
            "context_summary": context_summary,
        }
        for field, value in updates.items():
            if value is not None:
                setattr(row, field, value)
        row.version += 1
        row.updated_at = _dt.datetime.now(_dt.timezone.utc)
        db.flush()
        return _email_draft_dict(row)


def mark_email_draft_sent(draft_id: str, provider_message_id: Optional[str]) -> Optional[dict]:
    """Mark a successfully delivered-to-provider draft as sent."""
    with session_scope() as db:
        row = db.get(models.EmailDraft, draft_id)
        if row is None:
            return None
        if row.status == "sent":
            return _email_draft_dict(row)
        if row.status != "draft":
            raise ValueError(f"Email draft {draft_id} cannot be sent from status {row.status!r}")
        now = _dt.datetime.now(_dt.timezone.utc)
        row.status = "sent"
        row.provider_message_id = provider_message_id
        row.sent_at = now
        row.updated_at = now
        db.flush()
        return _email_draft_dict(row)


def cancel_email_draft(draft_id: str) -> Optional[dict]:
    """Cancel an unsent draft without deleting its audit trail."""
    with session_scope() as db:
        row = db.get(models.EmailDraft, draft_id)
        if row is None:
            return None
        if row.status != "draft":
            raise ValueError(f"Email draft {draft_id} cannot be cancelled from {row.status!r}")
        row.status = "cancelled"
        row.updated_at = _dt.datetime.now(_dt.timezone.utc)
        db.flush()
        return _email_draft_dict(row)

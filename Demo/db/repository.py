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
            "created_at": r.created_at.isoformat() if r.created_at else None,
        }


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

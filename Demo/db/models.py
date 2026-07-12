"""
PT4 Persistence Layer — SQLAlchemy ORM models (AP2).

Backbone for Human-in-the-Loop, dashboard and memory. Stores user requests,
agent answers and the FULL HitL decision (incl. the "why"), not just a boolean.

Core tables:
    sessions, messages, agent_runs, snapshots_meta, proposals, reviews, memory_items,
    email_drafts

Local default DB is SQLite; the Azure SQL target uses the same models
(generic types like JSON map to NVARCHAR(max) on Azure SQL).
"""
from __future__ import annotations

import datetime as _dt
from typing import Any, List, Optional

from sqlalchemy import (
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    JSON,
    String,
    Text,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    """Declarative base for all PT4 ORM models."""


def _utcnow() -> _dt.datetime:
    """Timezone-aware UTC timestamp (used as column default)."""
    return _dt.datetime.now(_dt.timezone.utc)


class Session(Base):
    """A single chat/work session (maps to table `sessions`)."""
    __tablename__ = "sessions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    started_at: Mapped[_dt.datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
    snapshot_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    user_ref: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    messages: Mapped[List["Message"]] = relationship(
        back_populates="session", cascade="all, delete-orphan"
    )
    agent_runs: Mapped[List["AgentRun"]] = relationship(
        back_populates="session", cascade="all, delete-orphan"
    )
    email_drafts: Mapped[List["EmailDraft"]] = relationship(
        back_populates="session", cascade="all, delete-orphan"
    )


class Message(Base):
    """A user or assistant message within a session (table `messages`)."""
    __tablename__ = "messages"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    session_id: Mapped[int] = mapped_column(ForeignKey("sessions.id"), index=True)
    role: Mapped[str] = mapped_column(String(20))  # "user" | "assistant"
    agent_name: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    content: Mapped[str] = mapped_column(Text)
    created_at: Mapped[_dt.datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)

    session: Mapped["Session"] = relationship(back_populates="messages")


class AgentRun(Base):
    """One agent/tool execution incl. token/cost telemetry (table `agent_runs`)."""
    __tablename__ = "agent_runs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    session_id: Mapped[int] = mapped_column(ForeignKey("sessions.id"), index=True)
    agent_name: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    tool_name: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    input_summary: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    output_summary: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    status: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    tokens_prompt: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    tokens_completion: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    cost_estimate: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    duration_ms: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    created_at: Mapped[_dt.datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)

    session: Mapped["Session"] = relationship(back_populates="agent_runs")


class SnapshotMeta(Base):
    """Snapshot-level validation metadata (table `snapshots_meta`)."""
    __tablename__ = "snapshots_meta"

    snapshot_id: Mapped[str] = mapped_column(String(255), primary_key=True)
    name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    created_at: Mapped[_dt.datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
    errors_before: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    warnings_before: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    errors_after: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    warnings_after: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    last_validated_at: Mapped[Optional[_dt.datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    proposals: Mapped[List["Proposal"]] = relationship(back_populates="snapshot")


class Proposal(Base):
    """A correction proposal awaiting/holding a review decision (table `proposals`)."""
    __tablename__ = "proposals"

    proposal_id: Mapped[str] = mapped_column(String(255), primary_key=True)
    snapshot_id: Mapped[Optional[str]] = mapped_column(
        ForeignKey("snapshots_meta.snapshot_id"), index=True, nullable=True
    )
    error_type: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    affected_entity: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    target_path: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    old_value: Mapped[Optional[Any]] = mapped_column(JSON, nullable=True)
    suggested_value: Mapped[Optional[Any]] = mapped_column(JSON, nullable=True)
    reasoning: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    evidence: Mapped[Optional[Any]] = mapped_column(JSON, nullable=True)
    confidence_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    schema_valid: Mapped[Optional[bool]] = mapped_column(Boolean, nullable=True)
    status: Mapped[str] = mapped_column(String(30), default="pending_review")
    # AP3.5a guard metadata (populated from the correction_proposal).
    correction_kind: Mapped[Optional[str]] = mapped_column(String(40), nullable=True)
    target_entity_type: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    target_entity_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    identity_check_supported: Mapped[Optional[bool]] = mapped_column(Boolean, nullable=True)
    # AP4.5 confidence transparency: the deterministic groundedness signal (is the proposed
    # value provable from the data or constructed?) plus the LLM's own justification for its
    # self-estimate. Both are what makes a confidence number reviewable instead of opaque.
    value_grounded: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    value_grounded_reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    confidence_rationale: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[_dt.datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)

    snapshot: Mapped[Optional["SnapshotMeta"]] = relationship(back_populates="proposals")
    reviews: Mapped[List["Review"]] = relationship(
        back_populates="proposal", cascade="all, delete-orphan"
    )


class Review(Base):
    """A human decision on a proposal incl. the reasoning (table `reviews`)."""
    __tablename__ = "reviews"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    proposal_id: Mapped[str] = mapped_column(ForeignKey("proposals.proposal_id"), index=True)
    decision: Mapped[str] = mapped_column(String(20))  # "approve" | "reject" | "modify"
    final_value: Mapped[Optional[Any]] = mapped_column(JSON, nullable=True)
    comment: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    reviewer_ref: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    decided_at: Mapped[_dt.datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
    revalidation_result: Mapped[Optional[Any]] = mapped_column(JSON, nullable=True)

    proposal: Mapped["Proposal"] = relationship(back_populates="reviews")


class EmailDraft(Base):
    """A previewed email that may be revised and explicitly sent by the user."""
    __tablename__ = "email_drafts"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    session_id: Mapped[int] = mapped_column(ForeignKey("sessions.id"), index=True)
    recipient: Mapped[str] = mapped_column(String(320))
    subject: Mapped[str] = mapped_column(String(500))
    body_plain: Mapped[str] = mapped_column(Text)
    body_html: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    context_summary: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(30), default="draft", index=True)
    version: Mapped[int] = mapped_column(Integer, default=1)
    provider_message_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    created_at: Mapped[_dt.datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
    updated_at: Mapped[_dt.datetime] = mapped_column(
        DateTime(timezone=True), default=_utcnow, onupdate=_utcnow
    )
    sent_at: Mapped[Optional[_dt.datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    session: Mapped["Session"] = relationship(back_populates="email_drafts")


class MemoryItem(Base):
    """Case-based-reasoning memory (populated in AP7; table created here)."""
    __tablename__ = "memory_items"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    error_type: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    affected_entity_pattern: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    suggested_value: Mapped[Optional[Any]] = mapped_column(JSON, nullable=True)
    final_value: Mapped[Optional[Any]] = mapped_column(JSON, nullable=True)
    decision: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    comment: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    revalidation_ok: Mapped[Optional[bool]] = mapped_column(Boolean, nullable=True)
    source_proposal_id: Mapped[Optional[str]] = mapped_column(
        ForeignKey("proposals.proposal_id"), nullable=True
    )
    created_at: Mapped[_dt.datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)

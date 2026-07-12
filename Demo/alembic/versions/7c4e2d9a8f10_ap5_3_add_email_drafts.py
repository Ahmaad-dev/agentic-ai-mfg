"""AP5.3 add persistent conversational email drafts

Revision ID: 7c4e2d9a8f10
Revises: 1aeb3778e9cb
Create Date: 2026-07-12

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "7c4e2d9a8f10"
down_revision: Union[str, Sequence[str], None] = "1aeb3778e9cb"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "email_drafts",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("session_id", sa.Integer(), nullable=False),
        sa.Column("recipient", sa.String(length=320), nullable=False),
        sa.Column("subject", sa.String(length=500), nullable=False),
        sa.Column("body_plain", sa.Text(), nullable=False),
        sa.Column("body_html", sa.Text(), nullable=True),
        sa.Column("context_summary", sa.Text(), nullable=True),
        sa.Column("status", sa.String(length=30), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("provider_message_id", sa.String(length=255), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("sent_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["session_id"], ["sessions.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_email_drafts_session_id"), "email_drafts", ["session_id"])
    op.create_index(op.f("ix_email_drafts_status"), "email_drafts", ["status"])


def downgrade() -> None:
    op.drop_index(op.f("ix_email_drafts_status"), table_name="email_drafts")
    op.drop_index(op.f("ix_email_drafts_session_id"), table_name="email_drafts")
    op.drop_table("email_drafts")

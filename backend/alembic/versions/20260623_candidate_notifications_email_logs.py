"""add candidate notifications and email logs

Revision ID: 20260623_notifications
Revises: 20260623_app_decisions
Create Date: 2026-06-23 12:00:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql


revision: str = "20260623_notifications"
down_revision: str | None = "20260623_app_decisions"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "candidate_notifications",
        sa.Column("id", postgresql.UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("candidate_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("application_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("interview_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("type", sa.String(length=40), nullable=False),
        sa.Column("title", sa.String(length=180), nullable=False),
        sa.Column("message", sa.Text(), nullable=False),
        sa.Column("is_read", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("read_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.CheckConstraint("type IN ('interview_invitation', 'accepted', 'rejected')", name="ck_candidate_notifications_type"),
        sa.ForeignKeyConstraint(["application_id"], ["applications.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["candidate_id"], ["candidates.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["interview_id"], ["interviews.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_candidate_notifications_candidate_id", "candidate_notifications", ["candidate_id"])
    op.create_index("ix_candidate_notifications_application_id", "candidate_notifications", ["application_id"])
    op.create_index("ix_candidate_notifications_interview_id", "candidate_notifications", ["interview_id"])
    op.create_index("ix_candidate_notifications_type", "candidate_notifications", ["type"])
    op.create_index("ix_candidate_notifications_is_read", "candidate_notifications", ["is_read"])

    op.create_table(
        "email_logs",
        sa.Column("id", postgresql.UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("candidate_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("application_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("to_email", sa.String(length=255), nullable=False),
        sa.Column("subject", sa.String(length=255), nullable=False),
        sa.Column("body", sa.Text(), nullable=False),
        sa.Column("status", sa.String(length=30), nullable=False, server_default="pending"),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("sent_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.CheckConstraint("status IN ('pending', 'sent', 'failed', 'skipped')", name="ck_email_logs_status"),
        sa.ForeignKeyConstraint(["application_id"], ["applications.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["candidate_id"], ["candidates.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_email_logs_candidate_id", "email_logs", ["candidate_id"])
    op.create_index("ix_email_logs_application_id", "email_logs", ["application_id"])
    op.create_index("ix_email_logs_to_email", "email_logs", ["to_email"])
    op.create_index("ix_email_logs_status", "email_logs", ["status"])


def downgrade() -> None:
    op.drop_index("ix_email_logs_status", table_name="email_logs")
    op.drop_index("ix_email_logs_to_email", table_name="email_logs")
    op.drop_index("ix_email_logs_application_id", table_name="email_logs")
    op.drop_index("ix_email_logs_candidate_id", table_name="email_logs")
    op.drop_table("email_logs")

    op.drop_index("ix_candidate_notifications_is_read", table_name="candidate_notifications")
    op.drop_index("ix_candidate_notifications_type", table_name="candidate_notifications")
    op.drop_index("ix_candidate_notifications_interview_id", table_name="candidate_notifications")
    op.drop_index("ix_candidate_notifications_application_id", table_name="candidate_notifications")
    op.drop_index("ix_candidate_notifications_candidate_id", table_name="candidate_notifications")
    op.drop_table("candidate_notifications")

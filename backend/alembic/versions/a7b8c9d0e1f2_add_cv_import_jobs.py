"""add cv import jobs

Revision ID: a7b8c9d0e1f2
Revises: 9c1d2e3f4a56
Create Date: 2026-08-14 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = "a7b8c9d0e1f2"
down_revision: Union[str, None] = "9c1d2e3f4a56"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _tables() -> set[str]:
    return set(sa.inspect(op.get_bind()).get_table_names())


def upgrade() -> None:
    if "cv_import_jobs" in _tables():
        return

    op.create_table(
        "cv_import_jobs",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("filename", sa.String(length=255), nullable=False),
        sa.Column("storage_path", sa.Text(), nullable=False),
        sa.Column("status", sa.String(length=30), nullable=False),
        sa.Column("current_step", sa.String(length=120), nullable=True),
        sa.Column("current_filename", sa.String(length=255), nullable=True),
        sa.Column("total_count", sa.Integer(), nullable=True),
        sa.Column("processed_count", sa.Integer(), nullable=False),
        sa.Column("success_count", sa.Integer(), nullable=False),
        sa.Column("duplicate_count", sa.Integer(), nullable=False),
        sa.Column("error_count", sa.Integer(), nullable=False),
        sa.Column("message", sa.Text(), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("result", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.CheckConstraint("status IN ('pending', 'processing', 'completed', 'failed')", name="ck_cv_import_jobs_status"),
        sa.CheckConstraint("total_count IS NULL OR total_count >= 0", name="ck_cv_import_jobs_total_count"),
        sa.CheckConstraint("processed_count >= 0", name="ck_cv_import_jobs_processed_count"),
        sa.CheckConstraint("success_count >= 0", name="ck_cv_import_jobs_success_count"),
        sa.CheckConstraint("duplicate_count >= 0", name="ck_cv_import_jobs_duplicate_count"),
        sa.CheckConstraint("error_count >= 0", name="ck_cv_import_jobs_error_count"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_cv_import_jobs_status"), "cv_import_jobs", ["status"], unique=False)


def downgrade() -> None:
    if "cv_import_jobs" not in _tables():
        return
    op.drop_index(op.f("ix_cv_import_jobs_status"), table_name="cv_import_jobs")
    op.drop_table("cv_import_jobs")

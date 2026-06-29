"""add job offer sector soft_skills languages

Revision ID: 20260627_job_fields
Revises: 20260627_pipeline_statuses
Create Date: 2026-06-27 14:00:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql


revision: str = "20260627_job_fields"
down_revision: str | None = "20260627_pipeline_statuses"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("job_offers", sa.Column("sector", sa.String(length=150), nullable=True))
    op.add_column("job_offers", sa.Column("soft_skills", postgresql.JSONB(astext_type=sa.Text()), nullable=True))
    op.add_column("job_offers", sa.Column("languages", postgresql.JSONB(astext_type=sa.Text()), nullable=True))


def downgrade() -> None:
    op.drop_column("job_offers", "languages")
    op.drop_column("job_offers", "soft_skills")
    op.drop_column("job_offers", "sector")

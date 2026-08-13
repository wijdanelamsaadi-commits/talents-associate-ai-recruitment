"""add candidate identified job profile

Revision ID: 9c1d2e3f4a56
Revises: 85ec75b0960b
Create Date: 2026-08-13 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "9c1d2e3f4a56"
down_revision: Union[str, None] = "85ec75b0960b"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _columns(table_name: str) -> set[str]:
    return {column["name"] for column in sa.inspect(op.get_bind()).get_columns(table_name)}


def upgrade() -> None:
    columns = _columns("candidates")
    if "identified_job_profile" not in columns:
        op.add_column("candidates", sa.Column("identified_job_profile", sa.String(length=150), nullable=True))
    if "job_profile_confidence" not in columns:
        op.add_column("candidates", sa.Column("job_profile_confidence", sa.Float(), nullable=True))
    if "job_profile_matched_terms" not in columns:
        op.add_column("candidates", sa.Column("job_profile_matched_terms", sa.JSON(), nullable=True))


def downgrade() -> None:
    columns = _columns("candidates")
    if "job_profile_matched_terms" in columns:
        op.drop_column("candidates", "job_profile_matched_terms")
    if "job_profile_confidence" in columns:
        op.drop_column("candidates", "job_profile_confidence")
    if "identified_job_profile" in columns:
        op.drop_column("candidates", "identified_job_profile")

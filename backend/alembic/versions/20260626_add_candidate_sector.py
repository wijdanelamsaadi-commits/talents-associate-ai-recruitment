"""add candidate sector field

Revision ID: 20260626_add_candidate_sector
Revises: 20260623_admin_settings
Create Date: 2026-06-26 12:00:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op


revision: str = "20260626_add_candidate_sector"
down_revision: str | None = "20260623_admin_settings"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    columns = {column["name"] for column in sa.inspect(op.get_bind()).get_columns("candidates")}
    if "sector" not in columns:
        op.add_column("candidates", sa.Column("sector", sa.String(length=150), nullable=True))


def downgrade() -> None:
    columns = {column["name"] for column in sa.inspect(op.get_bind()).get_columns("candidates")}
    if "sector" in columns:
        op.drop_column("candidates", "sector")

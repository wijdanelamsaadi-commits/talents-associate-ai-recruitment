"""create initial tables

Revision ID: e33664dcb928
Revises:
Create Date: 2026-06-17 20:39:51.427459

"""
from typing import Sequence, Union

from alembic import op

from app.models import Base


# revision identifiers, used by Alembic.
revision: str = "e33664dcb928"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS pgcrypto")
    Base.metadata.create_all(bind=op.get_bind())


def downgrade() -> None:
    Base.metadata.drop_all(bind=op.get_bind())

"""allow parsed cv extraction status

Revision ID: 48534ef125e9
Revises: dcd132ea864b
Create Date: 2026-06-17 21:38:33.828735

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '48534ef125e9'
down_revision: Union[str, None] = 'dcd132ea864b'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("ALTER TABLE extracted_cv_data DROP CONSTRAINT IF EXISTS ck_extracted_cv_data_parsing_status")
    op.execute(
        """
        ALTER TABLE extracted_cv_data
        ADD CONSTRAINT ck_extracted_cv_data_parsing_status
        CHECK (parsing_status IN ('extracted', 'parsed', 'empty', 'failed'))
        """
    )


def downgrade() -> None:
    op.execute("ALTER TABLE extracted_cv_data DROP CONSTRAINT IF EXISTS ck_extracted_cv_data_parsing_status")
    op.execute(
        """
        ALTER TABLE extracted_cv_data
        ADD CONSTRAINT ck_extracted_cv_data_parsing_status
        CHECK (parsing_status IN ('extracted', 'empty', 'failed'))
        """
    )

"""add cv extraction fields

Revision ID: dcd132ea864b
Revises: e33664dcb928
Create Date: 2026-06-17 21:25:55.677068

"""
from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = 'dcd132ea864b'
down_revision: Union[str, None] = 'e33664dcb928'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("ALTER TABLE extracted_cv_data ADD COLUMN IF NOT EXISTS ai_output JSONB")
    op.execute(
        "ALTER TABLE extracted_cv_data "
        "ADD COLUMN IF NOT EXISTS parsing_status VARCHAR(30) NOT NULL DEFAULT 'extracted'"
    )
    op.execute(
        """
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1
                FROM pg_constraint
                WHERE conname = 'ck_extracted_cv_data_parsing_status'
            ) THEN
                ALTER TABLE extracted_cv_data
                ADD CONSTRAINT ck_extracted_cv_data_parsing_status
                CHECK (parsing_status IN ('extracted', 'empty', 'failed'));
            END IF;
        END
        $$;
        """
    )


def downgrade() -> None:
    op.execute("ALTER TABLE extracted_cv_data DROP CONSTRAINT IF EXISTS ck_extracted_cv_data_parsing_status")
    op.execute("ALTER TABLE extracted_cv_data DROP COLUMN IF EXISTS parsing_status")
    op.execute("ALTER TABLE extracted_cv_data DROP COLUMN IF EXISTS ai_output")

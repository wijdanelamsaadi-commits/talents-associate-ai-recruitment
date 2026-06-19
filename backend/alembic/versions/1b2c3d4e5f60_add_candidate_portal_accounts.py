"""add candidate portal accounts

Revision ID: 1b2c3d4e5f60
Revises: d4e5f6a7b8c9
Create Date: 2026-06-19 13:05:00.000000
"""

from collections.abc import Sequence

from alembic import op


revision: str = "1b2c3d4e5f60"
down_revision: str | None = "d4e5f6a7b8c9"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute("ALTER TABLE candidates ADD COLUMN IF NOT EXISTS password_hash TEXT")
    op.execute("ALTER TABLE candidates ADD COLUMN IF NOT EXISTS account_status VARCHAR(30) NOT NULL DEFAULT 'active'")
    op.execute("ALTER TABLE candidates ADD COLUMN IF NOT EXISTS last_login_at TIMESTAMPTZ")
    op.execute("CREATE INDEX IF NOT EXISTS ix_candidates_account_status ON candidates (account_status)")
    op.execute(
        """
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1 FROM pg_constraint WHERE conname = 'ck_candidates_account_status'
            ) THEN
                ALTER TABLE candidates
                ADD CONSTRAINT ck_candidates_account_status
                CHECK (account_status IN ('active', 'invited', 'suspended', 'deleted'));
            END IF;
        END$$;
        """
    )


def downgrade() -> None:
    op.drop_constraint("ck_candidates_account_status", "candidates", type_="check")
    op.drop_index("ix_candidates_account_status", table_name="candidates")
    op.drop_column("candidates", "last_login_at")
    op.drop_column("candidates", "account_status")
    op.drop_column("candidates", "password_hash")

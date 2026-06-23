"""add AI embeddings and candidate pagination fields

Revision ID: 20260622_ai_embed_page
Revises: f9a8b7c6d5e4, 1b2c3d4e5f60
Create Date: 2026-06-22 11:30:00.000000
"""

from collections.abc import Sequence

from alembic import op


revision: str = "20260622_ai_embed_page"
down_revision: tuple[str, str] | None = ("f9a8b7c6d5e4", "1b2c3d4e5f60")
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute("ALTER TABLE candidates ADD COLUMN IF NOT EXISTS current_company VARCHAR(150)")
    op.execute("ALTER TABLE candidates ADD COLUMN IF NOT EXISTS gender VARCHAR(1)")
    op.execute("ALTER TABLE extracted_cv_data ADD COLUMN IF NOT EXISTS embedding JSONB")
    op.execute("ALTER TABLE extracted_cv_data ADD COLUMN IF NOT EXISTS embedding_generated_at TIMESTAMPTZ")
    op.execute("ALTER TABLE job_offers ADD COLUMN IF NOT EXISTS embedding JSONB")
    op.execute("ALTER TABLE job_offers ADD COLUMN IF NOT EXISTS embedding_generated_at TIMESTAMPTZ")
    op.execute("ALTER TABLE ai_matching_results ALTER COLUMN recommendation TYPE VARCHAR(150)")
    op.execute("CREATE INDEX IF NOT EXISTS idx_candidates_created_at_desc ON candidates (created_at DESC, id DESC)")


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS idx_candidates_created_at_desc")
    op.execute("ALTER TABLE ai_matching_results ALTER COLUMN recommendation TYPE VARCHAR(40)")
    op.execute("ALTER TABLE job_offers DROP COLUMN IF EXISTS embedding_generated_at")
    op.execute("ALTER TABLE job_offers DROP COLUMN IF EXISTS embedding")
    op.execute("ALTER TABLE extracted_cv_data DROP COLUMN IF EXISTS embedding_generated_at")
    op.execute("ALTER TABLE extracted_cv_data DROP COLUMN IF EXISTS embedding")
    op.execute("ALTER TABLE candidates DROP COLUMN IF EXISTS gender")
    op.execute("ALTER TABLE candidates DROP COLUMN IF EXISTS current_company")

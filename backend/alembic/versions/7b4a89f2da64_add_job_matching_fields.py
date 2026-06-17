"""add job matching fields

Revision ID: 7b4a89f2da64
Revises: 48534ef125e9
Create Date: 2026-06-17 21:44:15.462275

"""
from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = '7b4a89f2da64'
down_revision: Union[str, None] = '48534ef125e9'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("ALTER TABLE job_offers ADD COLUMN IF NOT EXISTS company_name VARCHAR(180)")
    op.execute("ALTER TABLE job_offers ADD COLUMN IF NOT EXISTS contract_type VARCHAR(60)")
    op.execute("ALTER TABLE job_offers ADD COLUMN IF NOT EXISTS required_skills JSONB")
    op.execute("ALTER TABLE job_offers ADD COLUMN IF NOT EXISTS preferred_skills JSONB")
    op.execute("ALTER TABLE job_offers ADD COLUMN IF NOT EXISTS required_experience_years INTEGER")
    op.execute("ALTER TABLE job_offers ADD COLUMN IF NOT EXISTS education_level VARCHAR(120)")
    op.execute(
        """
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1 FROM pg_constraint WHERE conname = 'ck_job_offers_required_experience'
            ) THEN
                ALTER TABLE job_offers
                ADD CONSTRAINT ck_job_offers_required_experience
                CHECK (required_experience_years IS NULL OR required_experience_years >= 0);
            END IF;
        END
        $$;
        """
    )
    op.execute("CREATE INDEX IF NOT EXISTS ix_job_offers_company_name ON job_offers (company_name)")

    op.execute("ALTER TABLE ai_matching_results ADD COLUMN IF NOT EXISTS detailed_scores JSONB")
    op.execute("ALTER TABLE ai_matching_results ADD COLUMN IF NOT EXISTS recommendation VARCHAR(40)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_ai_matching_results_recommendation ON ai_matching_results (recommendation)")


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS ix_ai_matching_results_recommendation")
    op.execute("ALTER TABLE ai_matching_results DROP COLUMN IF EXISTS recommendation")
    op.execute("ALTER TABLE ai_matching_results DROP COLUMN IF EXISTS detailed_scores")

    op.execute("DROP INDEX IF EXISTS ix_job_offers_company_name")
    op.execute("ALTER TABLE job_offers DROP CONSTRAINT IF EXISTS ck_job_offers_required_experience")
    op.execute("ALTER TABLE job_offers DROP COLUMN IF EXISTS education_level")
    op.execute("ALTER TABLE job_offers DROP COLUMN IF EXISTS required_experience_years")
    op.execute("ALTER TABLE job_offers DROP COLUMN IF EXISTS preferred_skills")
    op.execute("ALTER TABLE job_offers DROP COLUMN IF EXISTS required_skills")
    op.execute("ALTER TABLE job_offers DROP COLUMN IF EXISTS contract_type")
    op.execute("ALTER TABLE job_offers DROP COLUMN IF EXISTS company_name")

"""add evaluation management fields

Revision ID: c3f2a1b8d9e4
Revises: 7b4a89f2da64
Create Date: 2026-06-17 23:10:00.000000

"""
from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = "c3f2a1b8d9e4"
down_revision: Union[str, None] = "7b4a89f2da64"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


SCORE_COLUMNS = (
    "technical_score",
    "soft_skills_score",
    "motivation_score",
    "communication_score",
    "culture_fit_score",
)


def _add_check_constraint_if_missing(name: str, expression: str) -> None:
    op.execute(
        f"""
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1 FROM pg_constraint WHERE conname = '{name}'
            ) THEN
                ALTER TABLE evaluations ADD CONSTRAINT {name} CHECK ({expression});
            END IF;
        END
        $$;
        """
    )


def upgrade() -> None:
    op.execute("ALTER TABLE evaluations ADD COLUMN IF NOT EXISTS candidate_id UUID")
    op.execute("ALTER TABLE evaluations ADD COLUMN IF NOT EXISTS evaluator_name VARCHAR(150)")
    for column in SCORE_COLUMNS:
        op.execute(f"ALTER TABLE evaluations ADD COLUMN IF NOT EXISTS {column} INTEGER")
    op.execute("ALTER TABLE evaluations ADD COLUMN IF NOT EXISTS global_score NUMERIC(5, 2)")
    op.execute("ALTER TABLE evaluations ADD COLUMN IF NOT EXISTS comments TEXT")

    op.execute(
        """
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1 FROM pg_constraint WHERE conname = 'fk_evaluations_candidate_id_candidates'
            ) THEN
                ALTER TABLE evaluations
                ADD CONSTRAINT fk_evaluations_candidate_id_candidates
                FOREIGN KEY (candidate_id) REFERENCES candidates(id) ON DELETE CASCADE;
            END IF;
        END
        $$;
        """
    )
    op.execute("CREATE INDEX IF NOT EXISTS ix_evaluations_candidate_id ON evaluations (candidate_id)")

    for column in SCORE_COLUMNS:
        _add_check_constraint_if_missing(
            f"ck_evaluations_{column}",
            f"{column} IS NULL OR {column} BETWEEN 0 AND 100",
        )
    _add_check_constraint_if_missing(
        "ck_evaluations_global_score",
        "global_score IS NULL OR global_score BETWEEN 0 AND 100",
    )


def downgrade() -> None:
    op.execute("ALTER TABLE evaluations DROP CONSTRAINT IF EXISTS ck_evaluations_global_score")
    for column in SCORE_COLUMNS:
        op.execute(f"ALTER TABLE evaluations DROP CONSTRAINT IF EXISTS ck_evaluations_{column}")
    op.execute("DROP INDEX IF EXISTS ix_evaluations_candidate_id")
    op.execute("ALTER TABLE evaluations DROP CONSTRAINT IF EXISTS fk_evaluations_candidate_id_candidates")
    op.execute("ALTER TABLE evaluations DROP COLUMN IF EXISTS comments")
    op.execute("ALTER TABLE evaluations DROP COLUMN IF EXISTS global_score")
    for column in reversed(SCORE_COLUMNS):
        op.execute(f"ALTER TABLE evaluations DROP COLUMN IF EXISTS {column}")
    op.execute("ALTER TABLE evaluations DROP COLUMN IF EXISTS evaluator_name")
    op.execute("ALTER TABLE evaluations DROP COLUMN IF EXISTS candidate_id")

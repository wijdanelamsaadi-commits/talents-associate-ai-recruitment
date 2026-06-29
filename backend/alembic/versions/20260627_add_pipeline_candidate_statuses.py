"""add pipeline candidate statuses

Revision ID: 20260627_pipeline_statuses
Revises: 20260626_add_candidate_sector
Create Date: 2026-06-27 12:00:00.000000
"""

from collections.abc import Sequence

from alembic import op


revision: str = "20260627_pipeline_statuses"
down_revision: str | None = "20260626_add_candidate_sector"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


PREVIOUS_CANDIDATE_STATUSES = (
    "new",
    "active",
    "shortlisted",
    "interviewing",
    "offered",
    "hired",
    "rejected",
    "archived",
    "talent_pool",
)

CANDIDATE_STATUSES = PREVIOUS_CANDIDATE_STATUSES + (
    "preselectionne",
    "non_selectionne",
    "entretien_cabinet",
    "entretien_client",
    "profil_valide",
    "refus_candidat",
)


def _check_values(values: tuple[str, ...]) -> str:
    return ", ".join(f"'{value}'" for value in values)


def upgrade() -> None:
    op.execute("ALTER TABLE candidates DROP CONSTRAINT IF EXISTS ck_candidates_status")
    op.execute(
        f"""
        ALTER TABLE candidates
        ADD CONSTRAINT ck_candidates_status CHECK (status IN ({_check_values(CANDIDATE_STATUSES)}))
        """
    )


def downgrade() -> None:
    op.execute("ALTER TABLE candidates DROP CONSTRAINT IF EXISTS ck_candidates_status")
    op.execute(
        f"""
        ALTER TABLE candidates
        ADD CONSTRAINT ck_candidates_status CHECK (status IN ({_check_values(PREVIOUS_CANDIDATE_STATUSES)}))
        """
    )

"""add candidate talent pool and soft archive fields

Revision ID: 20260623_talent_pool
Revises: 20260622_ai_embed_page
Create Date: 2026-06-23 10:00:00.000000
"""

from collections.abc import Sequence

from alembic import op


revision: str = "20260623_talent_pool"
down_revision: str | None = "20260622_ai_embed_page"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


CANDIDATE_STATUSES = (
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

PREVIOUS_CANDIDATE_STATUSES = (
    "new",
    "active",
    "shortlisted",
    "interviewing",
    "offered",
    "hired",
    "rejected",
    "archived",
)

TIMELINE_EVENT_TYPES = (
    "candidate_created",
    "candidate_updated",
    "note",
    "email",
    "call",
    "status_change",
    "cv_uploaded",
    "cv_parsed",
    "interview_scheduled",
    "evaluation_added",
    "ai_match_generated",
    "candidate_application_submitted",
    "linkedin_csv_imported",
    "outlook_imported",
    "manual_cv_uploaded",
    "portal_update",
    "candidate_archived",
    "candidate_reactivated",
    "candidate_rejected",
)

PREVIOUS_TIMELINE_EVENT_TYPES = (
    "candidate_created",
    "candidate_updated",
    "note",
    "email",
    "call",
    "status_change",
    "cv_uploaded",
    "cv_parsed",
    "interview_scheduled",
    "evaluation_added",
    "ai_match_generated",
    "candidate_application_submitted",
    "linkedin_csv_imported",
    "outlook_imported",
    "manual_cv_uploaded",
    "portal_update",
)


def _check_values(values: tuple[str, ...]) -> str:
    return ", ".join(f"'{value}'" for value in values)


def upgrade() -> None:
    op.execute("ALTER TABLE candidates ADD COLUMN IF NOT EXISTS is_talent_pool BOOLEAN NOT NULL DEFAULT false")
    op.execute("ALTER TABLE candidates ADD COLUMN IF NOT EXISTS archived_at TIMESTAMPTZ")
    op.execute("ALTER TABLE candidates ADD COLUMN IF NOT EXISTS rejected_at TIMESTAMPTZ")
    op.execute("ALTER TABLE candidates ADD COLUMN IF NOT EXISTS reactivated_at TIMESTAMPTZ")
    op.execute("ALTER TABLE candidates ADD COLUMN IF NOT EXISTS last_decision_at TIMESTAMPTZ")
    op.execute("CREATE INDEX IF NOT EXISTS ix_candidates_is_talent_pool ON candidates (is_talent_pool)")

    op.execute("UPDATE candidates SET is_talent_pool = true WHERE status = 'rejected'")
    op.execute("UPDATE candidates SET rejected_at = COALESCE(rejected_at, updated_at) WHERE status = 'rejected'")
    op.execute("UPDATE candidates SET archived_at = COALESCE(archived_at, updated_at) WHERE status = 'archived'")
    op.execute(
        """
        UPDATE candidates
        SET last_decision_at = COALESCE(last_decision_at, rejected_at, archived_at)
        WHERE status IN ('rejected', 'archived')
        """
    )

    op.execute("ALTER TABLE candidates DROP CONSTRAINT IF EXISTS ck_candidates_status")
    op.execute(
        f"""
        ALTER TABLE candidates
        ADD CONSTRAINT ck_candidates_status CHECK (status IN ({_check_values(CANDIDATE_STATUSES)}))
        """
    )

    op.execute("ALTER TABLE candidate_timeline_events DROP CONSTRAINT IF EXISTS ck_candidate_timeline_events_type")
    op.execute(
        f"""
        ALTER TABLE candidate_timeline_events
        ADD CONSTRAINT ck_candidate_timeline_events_type CHECK (event_type IN ({_check_values(TIMELINE_EVENT_TYPES)}))
        """
    )


def downgrade() -> None:
    op.execute("ALTER TABLE candidate_timeline_events DROP CONSTRAINT IF EXISTS ck_candidate_timeline_events_type")
    op.execute(
        f"""
        ALTER TABLE candidate_timeline_events
        ADD CONSTRAINT ck_candidate_timeline_events_type CHECK (event_type IN ({_check_values(PREVIOUS_TIMELINE_EVENT_TYPES)}))
        """
    )

    op.execute("ALTER TABLE candidates DROP CONSTRAINT IF EXISTS ck_candidates_status")
    op.execute(
        f"""
        ALTER TABLE candidates
        ADD CONSTRAINT ck_candidates_status CHECK (status IN ({_check_values(PREVIOUS_CANDIDATE_STATUSES)}))
        """
    )

    op.execute("DROP INDEX IF EXISTS ix_candidates_is_talent_pool")
    op.execute("ALTER TABLE candidates DROP COLUMN IF EXISTS last_decision_at")
    op.execute("ALTER TABLE candidates DROP COLUMN IF EXISTS reactivated_at")
    op.execute("ALTER TABLE candidates DROP COLUMN IF EXISTS rejected_at")
    op.execute("ALTER TABLE candidates DROP COLUMN IF EXISTS archived_at")
    op.execute("ALTER TABLE candidates DROP COLUMN IF EXISTS is_talent_pool")

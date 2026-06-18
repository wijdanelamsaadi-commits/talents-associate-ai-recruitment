"""improve candidate source tracking

Revision ID: c0a4d8e12f90
Revises: b7c2a91e4d10
Create Date: 2026-06-18 00:00:00.000000
"""

from collections.abc import Sequence

from alembic import op

revision: str = "c0a4d8e12f90"
down_revision: str | None = "b7c2a91e4d10"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


OLD_CANDIDATE_SOURCES = ("manual", "cv_upload", "linkedin_csv", "candidate_portal", "referral", "other")
NEW_CANDIDATE_SOURCES = ("manual", "cv_upload", "linkedin_csv", "candidate_portal", "outlook_import", "referral", "other")

OLD_TIMELINE_TYPES = (
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
    "portal_update",
)
NEW_TIMELINE_TYPES = (
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


def _constraint_sql(values: tuple[str, ...]) -> str:
    return ", ".join(f"'{value}'" for value in values)


def upgrade() -> None:
    op.execute("ALTER TABLE candidates DROP CONSTRAINT IF EXISTS ck_candidates_source")
    op.execute(
        f"""
        ALTER TABLE candidates
        ADD CONSTRAINT ck_candidates_source CHECK (source IN ({_constraint_sql(NEW_CANDIDATE_SOURCES)}))
        """
    )
    op.execute("ALTER TABLE candidate_timeline_events DROP CONSTRAINT IF EXISTS ck_candidate_timeline_events_type")
    op.execute(
        f"""
        ALTER TABLE candidate_timeline_events
        ADD CONSTRAINT ck_candidate_timeline_events_type CHECK (event_type IN ({_constraint_sql(NEW_TIMELINE_TYPES)}))
        """
    )


def downgrade() -> None:
    op.execute("UPDATE candidates SET source = 'other' WHERE source = 'outlook_import'")
    op.execute("ALTER TABLE candidates DROP CONSTRAINT IF EXISTS ck_candidates_source")
    op.execute(
        f"""
        ALTER TABLE candidates
        ADD CONSTRAINT ck_candidates_source CHECK (source IN ({_constraint_sql(OLD_CANDIDATE_SOURCES)}))
        """
    )
    op.execute("DELETE FROM candidate_timeline_events WHERE event_type IN ('linkedin_csv_imported', 'outlook_imported', 'manual_cv_uploaded')")
    op.execute("ALTER TABLE candidate_timeline_events DROP CONSTRAINT IF EXISTS ck_candidate_timeline_events_type")
    op.execute(
        f"""
        ALTER TABLE candidate_timeline_events
        ADD CONSTRAINT ck_candidate_timeline_events_type CHECK (event_type IN ({_constraint_sql(OLD_TIMELINE_TYPES)}))
        """
    )

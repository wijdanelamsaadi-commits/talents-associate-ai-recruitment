"""add application decision timeline events

Revision ID: 20260623_app_decisions
Revises: 20260623_talent_pool
Create Date: 2026-06-23 11:00:00.000000
"""

from collections.abc import Sequence

from alembic import op


revision: str = "20260623_app_decisions"
down_revision: str | None = "20260623_talent_pool"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


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
    "application_accepted",
    "application_rejected",
    "application_reactivated",
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
    "candidate_archived",
    "candidate_reactivated",
    "candidate_rejected",
)


def _check_values(values: tuple[str, ...]) -> str:
    return ", ".join(f"'{value}'" for value in values)


def upgrade() -> None:
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

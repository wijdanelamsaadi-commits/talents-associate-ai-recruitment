"""add candidate application timeline event

Revision ID: aa91f3d2b6c0
Revises: f9a8b7c6d5e4
Create Date: 2026-06-18 00:00:00.000000
"""

from collections.abc import Sequence

from alembic import op

revision: str = "aa91f3d2b6c0"
down_revision: str | None = "f9a8b7c6d5e4"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


OLD_EVENT_TYPES = (
    "'candidate_created', 'candidate_updated', 'note', 'email', 'call', 'status_change', "
    "'cv_uploaded', 'cv_parsed', 'interview_scheduled', 'evaluation_added', 'ai_match_generated', "
    "'portal_update'"
)
NEW_EVENT_TYPES = (
    "'candidate_created', 'candidate_updated', 'note', 'email', 'call', 'status_change', "
    "'cv_uploaded', 'cv_parsed', 'interview_scheduled', 'evaluation_added', 'ai_match_generated', "
    "'candidate_application_submitted', 'portal_update'"
)


def upgrade() -> None:
    op.drop_constraint("ck_candidate_timeline_events_type", "candidate_timeline_events", type_="check")
    op.create_check_constraint(
        "ck_candidate_timeline_events_type",
        "candidate_timeline_events",
        f"event_type IN ({NEW_EVENT_TYPES})",
    )


def downgrade() -> None:
    op.drop_constraint("ck_candidate_timeline_events_type", "candidate_timeline_events", type_="check")
    op.create_check_constraint(
        "ck_candidate_timeline_events_type",
        "candidate_timeline_events",
        f"event_type IN ({OLD_EVENT_TYPES})",
    )

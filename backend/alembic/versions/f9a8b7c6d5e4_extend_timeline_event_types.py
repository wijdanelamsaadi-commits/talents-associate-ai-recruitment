"""extend timeline event types

Revision ID: f9a8b7c6d5e4
Revises: c3f2a1b8d9e4
Create Date: 2026-06-17 23:30:00.000000

"""
from typing import Sequence, Union

from alembic import op


revision: str = "f9a8b7c6d5e4"
down_revision: Union[str, None] = "c3f2a1b8d9e4"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


NEW_EVENT_TYPES = (
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
    "portal_update",
)

OLD_EVENT_TYPES = (
    "note",
    "email",
    "call",
    "status_change",
    "cv_uploaded",
    "interview_scheduled",
    "evaluation_added",
    "ai_match_generated",
    "portal_update",
)


def _constraint_sql(event_types: tuple[str, ...]) -> str:
    values = ", ".join(f"'{event_type}'" for event_type in event_types)
    return f"event_type IN ({values})"


def upgrade() -> None:
    op.execute("ALTER TABLE candidate_timeline_events DROP CONSTRAINT IF EXISTS ck_candidate_timeline_events_type")
    op.execute(
        f"""
        ALTER TABLE candidate_timeline_events
        ADD CONSTRAINT ck_candidate_timeline_events_type CHECK ({_constraint_sql(NEW_EVENT_TYPES)})
        """
    )


def downgrade() -> None:
    op.execute("ALTER TABLE candidate_timeline_events DROP CONSTRAINT IF EXISTS ck_candidate_timeline_events_type")
    op.execute(
        f"""
        ALTER TABLE candidate_timeline_events
        ADD CONSTRAINT ck_candidate_timeline_events_type CHECK ({_constraint_sql(OLD_EVENT_TYPES)})
        """
    )

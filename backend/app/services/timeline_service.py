from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Candidate, CandidateTimelineEvent
from app.schemas import TimelineEventCreate


def create_timeline_event(
    db: Session,
    candidate_id: UUID,
    event_type: str,
    title: str,
    description: str | None = None,
    metadata: dict | None = None,
) -> CandidateTimelineEvent:
    event = CandidateTimelineEvent(
        candidate_id=candidate_id,
        event_type=event_type,
        title=title,
        description=description,
        event_metadata=metadata,
    )
    db.add(event)
    db.flush()
    return event


def create_manual_timeline_event(
    db: Session,
    candidate_id: UUID,
    event_in: TimelineEventCreate,
) -> CandidateTimelineEvent | None:
    if db.get(Candidate, candidate_id) is None:
        return None

    event = create_timeline_event(
        db,
        candidate_id=candidate_id,
        event_type=event_in.event_type,
        title=event_in.title,
        description=event_in.description,
        metadata=event_in.metadata,
    )
    db.commit()
    db.refresh(event)
    return event


def list_candidate_timeline(db: Session, candidate_id: UUID) -> list[CandidateTimelineEvent]:
    statement = (
        select(CandidateTimelineEvent)
        .where(CandidateTimelineEvent.candidate_id == candidate_id)
        .order_by(CandidateTimelineEvent.occurred_at.desc(), CandidateTimelineEvent.created_at.desc())
    )
    return list(db.scalars(statement).all())


def get_timeline_event(db: Session, event_id: UUID) -> CandidateTimelineEvent | None:
    return db.get(CandidateTimelineEvent, event_id)


def delete_timeline_event(db: Session, event: CandidateTimelineEvent) -> None:
    db.delete(event)
    db.commit()

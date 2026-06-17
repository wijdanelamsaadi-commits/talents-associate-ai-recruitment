from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models import CandidateTimelineEvent
from app.schemas import TimelineEventRead
from app.services import timeline_service


router = APIRouter(prefix="/timeline", tags=["timeline"])


def serialize_timeline_event(event: CandidateTimelineEvent) -> TimelineEventRead:
    return TimelineEventRead(
        id=event.id,
        candidate_id=event.candidate_id,
        event_type=event.event_type,
        title=event.title,
        description=event.description,
        metadata=event.event_metadata,
        created_at=event.occurred_at,
    )


@router.delete("/{event_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_timeline_event(event_id: UUID, db: Session = Depends(get_db)) -> None:
    event = timeline_service.get_timeline_event(db, event_id)
    if event is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Timeline event not found.")

    timeline_service.delete_timeline_event(db, event)

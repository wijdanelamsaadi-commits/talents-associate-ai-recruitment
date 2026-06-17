from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models import CandidateTimelineEvent
from app.schemas import CandidateCreate, CandidateRead, CandidateUpdate, TimelineEventCreate, TimelineEventRead
from app.services import candidate_service, timeline_service


router = APIRouter(prefix="/candidates", tags=["candidates"])


def _serialize_timeline_event(event: CandidateTimelineEvent) -> TimelineEventRead:
    return TimelineEventRead(
        id=event.id,
        candidate_id=event.candidate_id,
        event_type=event.event_type,
        title=event.title,
        description=event.description,
        metadata=event.event_metadata,
        created_at=event.occurred_at,
    )


@router.post("", response_model=CandidateRead, status_code=status.HTTP_201_CREATED)
def create_candidate(candidate_in: CandidateCreate, db: Session = Depends(get_db)) -> CandidateRead:
    try:
        return candidate_service.create_candidate(db, candidate_in)
    except IntegrityError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Candidate with this email already exists.",
        ) from exc


@router.get("", response_model=list[CandidateRead])
def list_candidates(
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=100, ge=1, le=200),
    db: Session = Depends(get_db),
) -> list[CandidateRead]:
    return candidate_service.list_candidates(db, skip=skip, limit=limit)


@router.get("/{candidate_id}", response_model=CandidateRead)
def get_candidate(candidate_id: UUID, db: Session = Depends(get_db)) -> CandidateRead:
    candidate = candidate_service.get_candidate(db, candidate_id)
    if candidate is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Candidate not found.")
    return candidate


@router.put("/{candidate_id}", response_model=CandidateRead)
def update_candidate(candidate_id: UUID, candidate_in: CandidateUpdate, db: Session = Depends(get_db)) -> CandidateRead:
    candidate = candidate_service.get_candidate(db, candidate_id)
    if candidate is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Candidate not found.")

    try:
        return candidate_service.update_candidate(db, candidate, candidate_in)
    except IntegrityError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Candidate with this email already exists.",
        ) from exc


@router.delete("/{candidate_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_candidate(candidate_id: UUID, db: Session = Depends(get_db)) -> None:
    candidate = candidate_service.get_candidate(db, candidate_id)
    if candidate is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Candidate not found.")

    candidate_service.delete_candidate(db, candidate)


@router.get("/{candidate_id}/timeline", response_model=list[TimelineEventRead])
def list_candidate_timeline(candidate_id: UUID, db: Session = Depends(get_db)) -> list[TimelineEventRead]:
    candidate = candidate_service.get_candidate(db, candidate_id)
    if candidate is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Candidate not found.")

    events = timeline_service.list_candidate_timeline(db, candidate_id)
    return [_serialize_timeline_event(event) for event in events]


@router.post("/{candidate_id}/timeline", response_model=TimelineEventRead, status_code=status.HTTP_201_CREATED)
def create_candidate_timeline_event(
    candidate_id: UUID,
    event_in: TimelineEventCreate,
    db: Session = Depends(get_db),
) -> TimelineEventRead:
    event = timeline_service.create_manual_timeline_event(db, candidate_id, event_in)
    if event is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Candidate not found.")

    return _serialize_timeline_event(event)

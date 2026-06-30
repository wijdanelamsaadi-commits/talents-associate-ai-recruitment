from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models import CandidateTimelineEvent
from app.schemas import CandidateCreate, CandidateRead, CandidateUpdate, TimelineEventCreate, TimelineEventRead
from app.schemas.candidate import CandidateHistoryRead
from app.services import application_service, candidate_service, timeline_service


router = APIRouter(prefix="/candidates", tags=["candidates"])


class PaginatedCandidatesResponse(BaseModel):
    items: list[CandidateRead]
    total: int
    next_cursor: str | None = None


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
            detail="Un candidat avec cet email existe déjà.",
        ) from exc


@router.get("", response_model=PaginatedCandidatesResponse)
def list_candidates(
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=100, ge=1, le=200),
    after_id: UUID | None = Query(default=None, description="Cursor: ID of the last candidate on the previous page"),
    last_id: UUID | None = Query(default=None, description="Cursor alias for after_id"),
    filter: str = Query(default="all", pattern="^(all|active|rejected|archived|talent_pool)$"),
    job_offer_id: UUID | None = Query(default=None),
    pipeline_stage: str | None = Query(
        default=None,
        pattern="^(recu|preselectionne|non_selectionne|entretien_cabinet|entretien_client|profil_valide|refus_candidat)$",
    ),
    db: Session = Depends(get_db),
) -> PaginatedCandidatesResponse:
    cursor_id = last_id or after_id
    candidates = candidate_service.list_candidates(
        db,
        skip=skip,
        limit=limit,
        after_id=cursor_id,
        candidate_filter=filter,
        job_offer_id=job_offer_id,
        pipeline_stage=pipeline_stage,
    )
    next_cursor = str(candidates[-1].id) if candidates and len(candidates) == limit else None
    return PaginatedCandidatesResponse(
        items=[CandidateRead.model_validate(candidate) for candidate in candidates],
        total=candidate_service.count_candidates(
            db,
            candidate_filter=filter,
            job_offer_id=job_offer_id,
            pipeline_stage=pipeline_stage,
        ),
        next_cursor=next_cursor,
    )


@router.get("/{candidate_id}", response_model=CandidateRead)
def get_candidate(candidate_id: UUID, db: Session = Depends(get_db)) -> CandidateRead:
    candidate = candidate_service.get_candidate(db, candidate_id)
    if candidate is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Candidat introuvable.")
    return candidate


@router.get("/{candidate_id}/history", response_model=CandidateHistoryRead)
def get_candidate_history(candidate_id: UUID, db: Session = Depends(get_db)) -> CandidateHistoryRead:
    history = application_service.get_candidate_history(db, candidate_id)
    if history is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Candidat introuvable.")
    return history


@router.put("/{candidate_id}", response_model=CandidateRead)
def update_candidate(candidate_id: UUID, candidate_in: CandidateUpdate, db: Session = Depends(get_db)) -> CandidateRead:
    candidate = candidate_service.get_candidate(db, candidate_id)
    if candidate is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Candidat introuvable.")

    try:
        return candidate_service.update_candidate(db, candidate, candidate_in)
    except IntegrityError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Un candidat avec cet email existe déjà.",
        ) from exc


@router.delete("/{candidate_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_candidate(candidate_id: UUID, db: Session = Depends(get_db)) -> None:
    candidate = candidate_service.get_candidate(db, candidate_id)
    if candidate is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Candidat introuvable.")

    candidate_service.delete_candidate(db, candidate)


@router.patch("/{candidate_id}/archive", response_model=CandidateRead)
def archive_candidate(candidate_id: UUID, db: Session = Depends(get_db)) -> CandidateRead:
    candidate = candidate_service.get_candidate(db, candidate_id)
    if candidate is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Candidat introuvable.")
    return candidate_service.archive_candidate(db, candidate)


@router.patch("/{candidate_id}/reactivate", response_model=CandidateRead)
def reactivate_candidate(
    candidate_id: UUID,
    keep_in_talent_pool: bool = Query(default=False),
    db: Session = Depends(get_db),
) -> CandidateRead:
    candidate = candidate_service.get_candidate(db, candidate_id)
    if candidate is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Candidat introuvable.")
    return candidate_service.reactivate_candidate(db, candidate, keep_in_talent_pool=keep_in_talent_pool)


@router.patch("/{candidate_id}/reject", response_model=CandidateRead)
def reject_candidate(
    candidate_id: UUID,
    application_id: UUID | None = Query(default=None),
    db: Session = Depends(get_db),
) -> CandidateRead:
    candidate = candidate_service.get_candidate(db, candidate_id)
    if candidate is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Candidat introuvable.")
    return candidate_service.reject_candidate(db, candidate, application_id=application_id)


@router.get("/{candidate_id}/timeline", response_model=list[TimelineEventRead])
def list_candidate_timeline(candidate_id: UUID, db: Session = Depends(get_db)) -> list[TimelineEventRead]:
    candidate = candidate_service.get_candidate(db, candidate_id)
    if candidate is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Candidat introuvable.")

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
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Candidat introuvable.")

    return _serialize_timeline_event(event)

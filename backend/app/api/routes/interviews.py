from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models import Interview
from app.schemas import InterviewCreate, InterviewRead, InterviewStatusUpdate, InterviewUpdate
from app.services import interview_service
from app.services.interview_service import InterviewError


router = APIRouter(prefix="/interviews", tags=["interviews"])


def _serialize_interview(db: Session, interview: Interview) -> InterviewRead:
    return InterviewRead(
        id=interview.id,
        application_id=interview.application_id,
        candidate_id=interview.candidate_id,
        job_offer_id=interview_service.get_interview_job_offer_id(db, interview),
        scheduled_by_user_id=interview.scheduled_by_user_id,
        interviewer_user_id=interview.interviewer_user_id,
        interview_type=interview.interview_type,
        status=interview.status,
        scheduled_start_at=interview.scheduled_start_at,
        scheduled_end_at=interview.scheduled_end_at,
        meeting_url=interview.meeting_url,
        location=interview.location,
        notes=interview.notes,
        created_at=interview.created_at,
        updated_at=interview.updated_at,
    )


@router.post("", response_model=InterviewRead, status_code=status.HTTP_201_CREATED)
def create_interview(interview_in: InterviewCreate, db: Session = Depends(get_db)) -> InterviewRead:
    try:
        interview = interview_service.create_interview(db, interview_in)
    except InterviewError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    return _serialize_interview(db, interview)


@router.get("", response_model=list[InterviewRead])
def list_interviews(
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=100, ge=1, le=200),
    db: Session = Depends(get_db),
) -> list[InterviewRead]:
    return [_serialize_interview(db, interview) for interview in interview_service.list_interviews(db, skip, limit)]


@router.get("/{interview_id}", response_model=InterviewRead)
def get_interview(interview_id: UUID, db: Session = Depends(get_db)) -> InterviewRead:
    interview = interview_service.get_interview(db, interview_id)
    if interview is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Interview not found.")

    return _serialize_interview(db, interview)


@router.put("/{interview_id}", response_model=InterviewRead)
def update_interview(interview_id: UUID, interview_in: InterviewUpdate, db: Session = Depends(get_db)) -> InterviewRead:
    interview = interview_service.get_interview(db, interview_id)
    if interview is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Interview not found.")

    try:
        updated = interview_service.update_interview(db, interview, interview_in)
    except InterviewError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    return _serialize_interview(db, updated)


@router.patch("/{interview_id}/status", response_model=InterviewRead)
def update_interview_status(
    interview_id: UUID,
    status_in: InterviewStatusUpdate,
    db: Session = Depends(get_db),
) -> InterviewRead:
    interview = interview_service.get_interview(db, interview_id)
    if interview is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Interview not found.")

    updated = interview_service.update_interview_status(db, interview, status_in.status)
    return _serialize_interview(db, updated)


@router.delete("/{interview_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_interview(interview_id: UUID, db: Session = Depends(get_db)) -> None:
    interview = interview_service.get_interview(db, interview_id)
    if interview is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Interview not found.")

    interview_service.delete_interview(db, interview)

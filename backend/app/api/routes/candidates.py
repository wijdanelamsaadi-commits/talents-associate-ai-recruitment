from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas import CandidateCreate, CandidateRead, CandidateUpdate
from app.services import candidate_service


router = APIRouter(prefix="/candidates", tags=["candidates"])


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

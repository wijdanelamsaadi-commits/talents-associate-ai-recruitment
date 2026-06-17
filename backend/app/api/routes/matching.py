from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas import MatchingResultRead
from app.services import matching_service
from app.services.matching_service import MatchingError

router = APIRouter(prefix="/matching", tags=["matching"])


@router.post("/candidate/{candidate_id}/job/{job_id}", response_model=MatchingResultRead)
def match_candidate_to_job(candidate_id: UUID, job_id: UUID, db: Session = Depends(get_db)) -> MatchingResultRead:
    try:
        return matching_service.match_candidate_to_job(db, candidate_id=candidate_id, job_id=job_id)
    except MatchingError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@router.get("/results", response_model=list[MatchingResultRead])
def list_matching_results(
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=100, ge=1, le=200),
    db: Session = Depends(get_db),
) -> list[MatchingResultRead]:
    return matching_service.list_matching_results(db, skip=skip, limit=limit)


@router.get("/candidate/{candidate_id}", response_model=list[MatchingResultRead])
def list_candidate_matching_results(candidate_id: UUID, db: Session = Depends(get_db)) -> list[MatchingResultRead]:
    return matching_service.list_candidate_matching_results(db, candidate_id)


@router.delete("/results/{matching_result_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_matching_result(matching_result_id: UUID, db: Session = Depends(get_db)) -> None:
    matching_result = matching_service.get_matching_result(db, matching_result_id)
    if matching_result is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Matching result not found.")

    matching_service.delete_matching_result(db, matching_result)

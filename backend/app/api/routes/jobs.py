from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas import JobOfferCreate, JobOfferRead, JobOfferUpdate
from app.services import job_service

router = APIRouter(prefix="/jobs", tags=["jobs"])


@router.post("", response_model=JobOfferRead, status_code=status.HTTP_201_CREATED)
def create_job_offer(job_in: JobOfferCreate, db: Session = Depends(get_db)) -> JobOfferRead:
    return job_service.create_job_offer(db, job_in)


@router.get("", response_model=list[JobOfferRead])
def list_job_offers(
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=100, ge=1, le=200),
    db: Session = Depends(get_db),
) -> list[JobOfferRead]:
    return job_service.list_job_offers(db, skip=skip, limit=limit)


@router.get("/{job_id}", response_model=JobOfferRead)
def get_job_offer(job_id: UUID, db: Session = Depends(get_db)) -> JobOfferRead:
    job = job_service.get_job_offer(db, job_id)
    if job is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Offre d'emploi introuvable.")
    return job


@router.put("/{job_id}", response_model=JobOfferRead)
def update_job_offer(job_id: UUID, job_in: JobOfferUpdate, db: Session = Depends(get_db)) -> JobOfferRead:
    job = job_service.get_job_offer(db, job_id)
    if job is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Offre d'emploi introuvable.")
    return job_service.update_job_offer(db, job, job_in)


@router.delete("/{job_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_job_offer(job_id: UUID, db: Session = Depends(get_db)) -> None:
    job = job_service.get_job_offer(db, job_id)
    if job is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Offre d'emploi introuvable.")
    job_service.delete_job_offer(db, job)

from uuid import UUID

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile, status
from pydantic import ValidationError
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas import PortalApplicationResponse, PortalApplicationStatusResponse, PortalCandidateData, PublicJobRead
from app.services.cv_service import CVUploadError
from app.services.portal_service import (
    PortalApplicationError,
    get_application_status_by_email,
    get_public_job,
    list_public_jobs,
    submit_application,
)
from app.services.text_extraction import TextExtractionError

router = APIRouter(prefix="/portal", tags=["candidate portal"])


@router.get("/jobs", response_model=list[PublicJobRead])
def list_jobs(db: Session = Depends(get_db)) -> list[PublicJobRead]:
    return list_public_jobs(db)


@router.get("/jobs/{job_id}", response_model=PublicJobRead)
def get_job(job_id: UUID, db: Session = Depends(get_db)) -> PublicJobRead:
    job = get_public_job(db, job_id)
    if job is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job offer not found.")
    return job


@router.get("/status", response_model=PortalApplicationStatusResponse)
def get_application_status(
    email: str = Query(..., min_length=3),
    db: Session = Depends(get_db),
) -> PortalApplicationStatusResponse:
    return get_application_status_by_email(db, email)


@router.post("/jobs/{job_id}/apply", response_model=PortalApplicationResponse, status_code=status.HTTP_201_CREATED)
def apply_to_job(
    job_id: UUID,
    first_name: str = Form(...),
    last_name: str = Form(...),
    email: str = Form(...),
    phone: str | None = Form(default=None),
    location: str | None = Form(default=None),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
) -> PortalApplicationResponse:
    try:
        candidate_data = PortalCandidateData(
            first_name=first_name,
            last_name=last_name,
            email=email,
            phone=phone,
            location=location,
        )
        return submit_application(db, job_id=job_id, candidate_data=candidate_data, upload_file=file)
    except ValidationError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=exc.errors()) from exc
    except PortalApplicationError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except CVUploadError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    except TextExtractionError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)) from exc
    except IntegrityError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Application could not be saved.") from exc

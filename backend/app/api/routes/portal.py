from uuid import UUID

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile, status
from pydantic import ValidationError
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.api.dependencies import require_candidate
from app.core.config import settings
from app.core.database import get_db
from app.models import Candidate
from app.schemas import (
    CandidateApplicationRead,
    CandidateLogin,
    CandidateNotificationRead,
    CandidateProfileRead,
    CandidateProfileUpdate,
    CandidateRegister,
    CandidateTokenResponse,
    PortalApplicationResponse,
    PortalApplicationStatusResponse,
    PortalCandidateData,
    PublicJobRead,
)
from app.services import notification_service
from app.services.cv_service import CVUploadError
from app.services.portal_service import (
    CandidateAuthError,
    PortalApplicationError,
    apply_authenticated_candidate,
    get_application_status_by_email,
    get_candidate_profile,
    get_public_job,
    list_public_jobs,
    list_authenticated_applications,
    login_candidate,
    register_candidate,
    replace_candidate_cv,
    submit_application,
    update_candidate_profile,
)
from app.services.text_extraction import TextExtractionError

router = APIRouter(prefix="/portal", tags=["candidate portal"])


@router.post("/auth/register", response_model=CandidateTokenResponse, status_code=status.HTTP_201_CREATED)
def register_candidate_account(payload: CandidateRegister, db: Session = Depends(get_db)) -> CandidateTokenResponse:
    try:
        return register_candidate(db, payload)
    except CandidateAuthError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    except Exception as exc:
        detail = str(exc) if settings.ENVIRONMENT == "development" else "Candidate registration failed."
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=detail) from exc


@router.post("/auth/login", response_model=CandidateTokenResponse)
def login_candidate_account(payload: CandidateLogin, db: Session = Depends(get_db)) -> CandidateTokenResponse:
    try:
        return login_candidate(db, payload)
    except CandidateAuthError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(exc)) from exc
    except Exception as exc:
        detail = str(exc) if settings.ENVIRONMENT == "development" else "Candidate login failed."
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=detail) from exc


@router.get("/me", response_model=CandidateProfileRead)
def read_candidate_me(
    candidate: Candidate = Depends(require_candidate),
    db: Session = Depends(get_db),
) -> CandidateProfileRead:
    return get_candidate_profile(db, candidate)


@router.get("/profile", response_model=CandidateProfileRead)
def read_candidate_profile(
    candidate: Candidate = Depends(require_candidate),
    db: Session = Depends(get_db),
) -> CandidateProfileRead:
    return get_candidate_profile(db, candidate)


@router.put("/profile", response_model=CandidateProfileRead)
def update_candidate_portal_profile(
    payload: CandidateProfileUpdate,
    candidate: Candidate = Depends(require_candidate),
    db: Session = Depends(get_db),
) -> CandidateProfileRead:
    return update_candidate_profile(db, candidate, payload)


@router.put("/profile/cv", response_model=CandidateProfileRead)
def replace_candidate_portal_cv(
    file: UploadFile = File(...),
    candidate: Candidate = Depends(require_candidate),
    db: Session = Depends(get_db),
) -> CandidateProfileRead:
    try:
        profile, _matching_results = replace_candidate_cv(db, candidate, file)
        return profile
    except CVUploadError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    except TextExtractionError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)) from exc


@router.get("/applications", response_model=list[CandidateApplicationRead])
def read_candidate_applications(
    candidate: Candidate = Depends(require_candidate),
    db: Session = Depends(get_db),
) -> list[CandidateApplicationRead]:
    return list_authenticated_applications(db, candidate)


@router.get("/notifications", response_model=list[CandidateNotificationRead])
def read_candidate_notifications(
    candidate: Candidate = Depends(require_candidate),
    db: Session = Depends(get_db),
) -> list[CandidateNotificationRead]:
    return notification_service.list_candidate_notifications(db, candidate.id)


@router.patch("/notifications/{notification_id}/read", response_model=CandidateNotificationRead)
def mark_candidate_notification_read(
    notification_id: UUID,
    candidate: Candidate = Depends(require_candidate),
    db: Session = Depends(get_db),
) -> CandidateNotificationRead:
    notification = notification_service.mark_candidate_notification_read(
        db,
        notification_id=notification_id,
        candidate_id=candidate.id,
    )
    if notification is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Notification not found.")
    return notification


@router.post("/jobs/{job_id}/apply-auth", response_model=PortalApplicationResponse, status_code=status.HTTP_201_CREATED)
def apply_logged_candidate_to_job(
    job_id: UUID,
    candidate: Candidate = Depends(require_candidate),
    db: Session = Depends(get_db),
) -> PortalApplicationResponse:
    try:
        return apply_authenticated_candidate(db, candidate, job_id)
    except PortalApplicationError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


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

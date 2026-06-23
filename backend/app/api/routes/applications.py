from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, ConfigDict
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.services import application_service


router = APIRouter(prefix="/applications", tags=["applications"])


class ApplicationRead(BaseModel):
    id: UUID
    candidate_id: UUID
    job_offer_id: UUID
    cv_file_id: UUID | None = None
    source: str
    status: str
    current_stage: str | None = None
    applied_at: datetime
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


def _get_application_or_404(application_id: UUID, db: Session):
    application = application_service.get_application(db, application_id)
    if application is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Application not found.")
    return application


@router.patch("/{application_id}/accept", response_model=ApplicationRead)
def accept_application(application_id: UUID, db: Session = Depends(get_db)) -> ApplicationRead:
    application = _get_application_or_404(application_id, db)
    return application_service.accept_application(db, application)


@router.post("/{application_id}/accept", response_model=ApplicationRead)
def accept_application_post(application_id: UUID, db: Session = Depends(get_db)) -> ApplicationRead:
    application = _get_application_or_404(application_id, db)
    return application_service.accept_application(db, application)


@router.patch("/{application_id}/reject", response_model=ApplicationRead)
def reject_application(application_id: UUID, db: Session = Depends(get_db)) -> ApplicationRead:
    application = _get_application_or_404(application_id, db)
    return application_service.reject_application(db, application)


@router.post("/{application_id}/reject", response_model=ApplicationRead)
def reject_application_post(application_id: UUID, db: Session = Depends(get_db)) -> ApplicationRead:
    application = _get_application_or_404(application_id, db)
    return application_service.reject_application(db, application)


@router.patch("/{application_id}/reactivate", response_model=ApplicationRead)
def reactivate_application(application_id: UUID, db: Session = Depends(get_db)) -> ApplicationRead:
    application = _get_application_or_404(application_id, db)
    return application_service.reactivate_application(db, application)


@router.post("/{application_id}/reactivate", response_model=ApplicationRead)
def reactivate_application_post(application_id: UUID, db: Session = Depends(get_db)) -> ApplicationRead:
    application = _get_application_or_404(application_id, db)
    return application_service.reactivate_application(db, application)

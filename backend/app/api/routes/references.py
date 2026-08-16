from fastapi import APIRouter
from fastapi import Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.services.job_profile_service import get_job_reference_titles

router = APIRouter(prefix="/references", tags=["references"])


@router.get("/job-titles", response_model=list[str])
def list_job_reference_titles(db: Session = Depends(get_db)) -> list[str]:
    return get_job_reference_titles(db)

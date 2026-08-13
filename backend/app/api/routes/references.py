from fastapi import APIRouter

from app.services.job_profile_service import get_job_reference_titles

router = APIRouter(prefix="/references", tags=["references"])


@router.get("/job-titles", response_model=list[str])
def list_job_reference_titles() -> list[str]:
    return get_job_reference_titles()

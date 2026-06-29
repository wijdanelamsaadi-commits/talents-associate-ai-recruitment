from datetime import date
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas import DashboardPipelineRead, DashboardStatsRead
from app.services import dashboard_service

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("/stats", response_model=DashboardStatsRead)
def get_dashboard_stats(db: Session = Depends(get_db)) -> DashboardStatsRead:
    return dashboard_service.get_dashboard_stats(db)


@router.get("/pipeline", response_model=DashboardPipelineRead)
def get_dashboard_pipeline(
    job_id: UUID | None = Query(default=None),
    job_status: str | None = Query(
        default=None,
        pattern="^(all|en_cours|cloture|annule)$",
        description="Statut du poste: en_cours, cloture, annule",
    ),
    client: str | None = Query(default=None),
    location: str | None = Query(default=None),
    opened_from: date | None = Query(default=None),
    opened_to: date | None = Query(default=None),
    db: Session = Depends(get_db),
) -> DashboardPipelineRead:
    return dashboard_service.get_dashboard_pipeline(
        db,
        job_id=job_id,
        job_status=job_status,
        client=client,
        location=location,
        opened_from=opened_from,
        opened_to=opened_to,
    )

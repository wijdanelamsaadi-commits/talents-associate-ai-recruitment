from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas import DashboardStatsRead
from app.services import dashboard_service

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("/stats", response_model=DashboardStatsRead)
def get_dashboard_stats(db: Session = Depends(get_db)) -> DashboardStatsRead:
    return dashboard_service.get_dashboard_stats(db)

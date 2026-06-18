from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class DashboardCount(BaseModel):
    name: str
    count: int


class DashboardActivity(BaseModel):
    id: UUID
    candidate_id: UUID
    event_type: str
    title: str
    description: str | None
    metadata: dict | None
    created_at: datetime


class DashboardStatsRead(BaseModel):
    total_candidates: int
    candidate_counts: list[DashboardCount]
    total_jobs: int
    open_jobs: int
    job_counts: list[DashboardCount]
    total_interviews: int
    upcoming_interviews: int
    interview_counts: list[DashboardCount]
    total_evaluations: int
    total_outlook_imports: int
    total_outlook_imported: int
    average_matching_score: float | None
    matching_score_buckets: list[DashboardCount]
    recent_activities: list[DashboardActivity]

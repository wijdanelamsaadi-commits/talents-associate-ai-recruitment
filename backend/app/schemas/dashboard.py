from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


PIPELINE_STAGES: tuple[tuple[str, str], ...] = (
    ("recu", "Candidatures reçues"),
    ("non_selectionne", "Non sélectionnées"),
    ("preselectionne", "Présélectionnées"),
    ("entretien_cabinet", "Entretien cabinet"),
    ("entretien_client", "Entretien client"),
    ("profil_valide", "Profil validé"),
    ("refus_candidat", "Refus candidat"),
)


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


class DashboardJobOption(BaseModel):
    id: UUID
    title: str
    company_name: str | None
    location: str | None
    status: str
    opened_at: datetime | None


class PipelineStageCount(BaseModel):
    stage: str
    label: str
    count: int


class JobPipelineRead(BaseModel):
    job_id: UUID
    title: str
    company_name: str | None
    location: str | None
    status: str
    opened_at: datetime | None
    stages: list[PipelineStageCount]


class DashboardPipelineRead(BaseModel):
    filter_options: dict[str, list[str] | list[DashboardJobOption]]
    pipelines: list[JobPipelineRead]

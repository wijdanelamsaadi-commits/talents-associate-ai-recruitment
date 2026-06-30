from datetime import datetime
from decimal import Decimal
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field, HttpUrl


CandidateStatusPattern = (
    "^(new|active|shortlisted|interviewing|offered|hired|rejected|archived|talent_pool|"
    "preselectionne|non_selectionne|entretien_cabinet|entretien_client|profil_valide|refus_candidat)$"
)


class CandidateBase(BaseModel):
    first_name: str = Field(min_length=1, max_length=100)
    last_name: str = Field(min_length=1, max_length=100)
    email: EmailStr | None = None
    phone: str | None = Field(default=None, max_length=50)
    location: str | None = Field(default=None, max_length=255)
    linkedin_url: str | None = None
    portfolio_url: str | None = None
    current_title: str | None = Field(default=None, max_length=150)
    current_company: str | None = Field(default=None, max_length=150)
    sector: str | None = Field(default=None, max_length=150)
    gender: str | None = Field(default=None, pattern="^(M|F)$")
    source: str = Field(default="cv_upload", pattern="^(cv_upload|linkedin_csv|candidate_portal)$")
    status: str = Field(
        default="new",
        pattern=CandidateStatusPattern,
    )
    is_talent_pool: bool = False
    archived_at: datetime | None = None
    rejected_at: datetime | None = None
    reactivated_at: datetime | None = None
    last_decision_at: datetime | None = None
    consent_given: bool = False
    owner_user_id: UUID | None = None


class CandidateCreate(CandidateBase):
    pass


class CandidateUpdate(BaseModel):
    first_name: str | None = Field(default=None, min_length=1, max_length=100)
    last_name: str | None = Field(default=None, min_length=1, max_length=100)
    email: EmailStr | None = None
    phone: str | None = Field(default=None, max_length=50)
    location: str | None = Field(default=None, max_length=255)
    linkedin_url: str | None = None
    portfolio_url: str | None = None
    current_title: str | None = Field(default=None, max_length=150)
    current_company: str | None = Field(default=None, max_length=150)
    sector: str | None = Field(default=None, max_length=150)
    gender: str | None = Field(default=None, pattern="^(M|F)$")
    source: str | None = Field(
        default=None,
        pattern="^(cv_upload|linkedin_csv|candidate_portal)$",
    )
    status: str | None = Field(
        default=None,
        pattern=CandidateStatusPattern,
    )
    is_talent_pool: bool | None = None
    consent_given: bool | None = None
    owner_user_id: UUID | None = None


class CandidateRead(CandidateBase):
    id: UUID
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class CandidateHistoryCVFile(BaseModel):
    id: UUID
    original_filename: str
    mime_type: str | None = None
    file_size_bytes: int | None = None
    parsing_status: str
    parser_model: str | None = None
    uploaded_at: datetime


class CandidateHistoryMatchingResult(BaseModel):
    id: UUID
    application_id: UUID | None = None
    job_offer_id: UUID
    job_title: str | None = None
    score: Decimal
    semantic_score: int | None = None
    used_semantic_embedding: bool
    recommendation: str | None = None
    explanation: str | None = None
    matched_skills: Any = None
    missing_skills: Any = None
    detailed_scores: dict[str, Any] | None = None
    created_at: datetime


class CandidateHistoryInterview(BaseModel):
    id: UUID
    application_id: UUID
    interview_type: str
    status: str
    scheduled_start_at: datetime
    scheduled_end_at: datetime | None = None
    location: str | None = None
    meeting_url: str | None = None
    notes: str | None = None


class CandidateHistoryEvaluation(BaseModel):
    id: UUID
    application_id: UUID
    interview_id: UUID | None = None
    evaluator_name: str | None = None
    rating: int | None = None
    technical_score: int | None = None
    soft_skills_score: int | None = None
    motivation_score: int | None = None
    communication_score: int | None = None
    culture_fit_score: int | None = None
    global_score: Decimal | None = None
    recommendation: str
    strengths: str | None = None
    weaknesses: str | None = None
    comments: str | None = None
    notes: str | None = None
    submitted_at: datetime | None = None


class CandidateHistoryApplication(BaseModel):
    id: UUID
    job_offer_id: UUID
    job_title: str
    company_name: str | None = None
    source: str
    status: str
    current_stage: str | None = None
    applied_at: datetime
    cv_file_id: UUID | None = None
    matching_results: list[CandidateHistoryMatchingResult] = []
    interviews: list[CandidateHistoryInterview] = []
    evaluations: list[CandidateHistoryEvaluation] = []


class CandidateHistoryTimelineEvent(BaseModel):
    id: UUID
    event_type: str
    title: str
    description: str | None = None
    metadata: dict[str, Any] | None = None
    created_at: datetime


class CandidateHistoryRead(BaseModel):
    candidate: CandidateRead
    cv_files: list[CandidateHistoryCVFile] = []
    applications: list[CandidateHistoryApplication] = []
    matching_results: list[CandidateHistoryMatchingResult] = []
    interviews: list[CandidateHistoryInterview] = []
    evaluations: list[CandidateHistoryEvaluation] = []
    timeline_events: list[CandidateHistoryTimelineEvent] = []

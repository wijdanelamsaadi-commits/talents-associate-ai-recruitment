from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator


class CandidateRegister(BaseModel):
    first_name: str = Field(min_length=1, max_length=100)
    last_name: str = Field(min_length=1, max_length=100)
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    phone: str | None = Field(default=None, max_length=50)
    location: str | None = Field(default=None, max_length=255)
    current_title: str | None = Field(default=None, max_length=150)


class CandidateLogin(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1, max_length=128)


class CandidateProfileUpdate(BaseModel):
    first_name: str | None = Field(default=None, min_length=1, max_length=100)
    last_name: str | None = Field(default=None, min_length=1, max_length=100)
    phone: str | None = Field(default=None, max_length=50)
    location: str | None = Field(default=None, max_length=255)
    linkedin_url: str | None = None
    portfolio_url: str | None = None
    current_title: str | None = Field(default=None, max_length=150)


class CandidateProfileRead(BaseModel):
    id: UUID
    first_name: str
    last_name: str
    email: EmailStr | None
    phone: str | None
    location: str | None
    linkedin_url: str | None
    portfolio_url: str | None
    current_title: str | None
    source: str
    status: str
    account_status: str
    latest_cv_file_id: UUID | None = None
    latest_cv_filename: str | None = None
    latest_cv_uploaded_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True)


class CandidateTokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    candidate: CandidateProfileRead


class PortalApplicationResponse(BaseModel):
    candidate_id: UUID
    application_id: UUID
    cv_file_id: UUID
    parsing_status: str
    confidence_score: float | None
    matching_result_ids: list[UUID]
    message: str


class PortalApplicationStatusItem(BaseModel):
    application_id: UUID
    job_offer_id: UUID
    job_title: str
    company_name: str | None
    application_status: str
    current_stage: str | None
    applied_at: datetime
    cv_file_id: UUID | None
    best_matching_score: float | None
    recommendation: str | None


class PortalApplicationStatusResponse(BaseModel):
    email: EmailStr
    candidate_id: UUID | None
    applications: list[PortalApplicationStatusItem]


class CandidateApplicationRead(PortalApplicationStatusItem):
    matching_result_ids: list[UUID] = []


class PortalCandidateData(BaseModel):
    first_name: str = Field(min_length=1, max_length=100)
    last_name: str = Field(min_length=1, max_length=100)
    email: EmailStr
    phone: str | None = Field(default=None, max_length=50)
    location: str | None = Field(default=None, max_length=255)


class PublicJobRead(BaseModel):
    id: UUID
    title: str
    company_name: str | None
    location: str | None
    contract_type: str | None
    required_skills: list[str]
    preferred_skills: list[str]
    required_experience_years: int | None
    education_level: str | None
    description: str
    status: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

    @field_validator("required_skills", "preferred_skills", mode="before")
    @classmethod
    def default_empty_skill_lists(cls, value: list[str] | None) -> list[str]:
        return value or []

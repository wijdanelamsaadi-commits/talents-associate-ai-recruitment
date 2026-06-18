from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator


class PortalApplicationResponse(BaseModel):
    candidate_id: UUID
    application_id: UUID
    cv_file_id: UUID
    parsing_status: str
    confidence_score: float | None
    matching_result_ids: list[UUID]
    message: str


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

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator


class JobOfferBase(BaseModel):
    title: str = Field(min_length=1, max_length=180)
    company_name: str | None = Field(default=None, max_length=180)
    location: str | None = Field(default=None, max_length=180)
    contract_type: str | None = Field(default=None, max_length=60)
    required_skills: list[str] = Field(default_factory=list)
    preferred_skills: list[str] = Field(default_factory=list)
    required_experience_years: int | None = Field(default=None, ge=0)
    education_level: str | None = Field(default=None, max_length=120)
    description: str = Field(min_length=1)
    status: str = Field(default="draft", pattern="^(draft|open|paused|closed|archived)$")

    @field_validator("required_skills", "preferred_skills", mode="before")
    @classmethod
    def default_empty_skill_lists(cls, value: list[str] | None) -> list[str]:
        return value or []


class JobOfferCreate(JobOfferBase):
    pass


class JobOfferUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=180)
    company_name: str | None = Field(default=None, max_length=180)
    location: str | None = Field(default=None, max_length=180)
    contract_type: str | None = Field(default=None, max_length=60)
    required_skills: list[str] | None = None
    preferred_skills: list[str] | None = None
    required_experience_years: int | None = Field(default=None, ge=0)
    education_level: str | None = Field(default=None, max_length=120)
    description: str | None = Field(default=None, min_length=1)
    status: str | None = Field(default=None, pattern="^(draft|open|paused|closed|archived)$")


class JobOfferRead(JobOfferBase):
    id: UUID
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

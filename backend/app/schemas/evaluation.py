from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class EvaluationBase(BaseModel):
    interview_id: UUID
    candidate_id: UUID | None = None
    evaluator_name: str = Field(min_length=1, max_length=150)
    technical_score: int = Field(ge=0, le=100)
    soft_skills_score: int = Field(ge=0, le=100)
    motivation_score: int = Field(ge=0, le=100)
    communication_score: int = Field(ge=0, le=100)
    culture_fit_score: int = Field(ge=0, le=100)
    recommendation: str = Field(pattern="^(strong_yes|yes|hold|no|strong_no)$")
    strengths: str | None = None
    weaknesses: str | None = None
    comments: str | None = None


class EvaluationCreate(EvaluationBase):
    pass


class EvaluationUpdate(BaseModel):
    interview_id: UUID | None = None
    candidate_id: UUID | None = None
    evaluator_name: str | None = Field(default=None, min_length=1, max_length=150)
    technical_score: int | None = Field(default=None, ge=0, le=100)
    soft_skills_score: int | None = Field(default=None, ge=0, le=100)
    motivation_score: int | None = Field(default=None, ge=0, le=100)
    communication_score: int | None = Field(default=None, ge=0, le=100)
    culture_fit_score: int | None = Field(default=None, ge=0, le=100)
    recommendation: str | None = Field(default=None, pattern="^(strong_yes|yes|hold|no|strong_no)$")
    strengths: str | None = None
    weaknesses: str | None = None
    comments: str | None = None


class EvaluationRead(BaseModel):
    id: UUID
    interview_id: UUID
    application_id: UUID
    candidate_id: UUID
    evaluator_name: str
    technical_score: int
    soft_skills_score: int
    motivation_score: int
    communication_score: int
    culture_fit_score: int
    global_score: float
    recommendation: str
    strengths: str | None
    weaknesses: str | None
    comments: str | None
    submitted_at: datetime | None
    created_at: datetime
    updated_at: datetime

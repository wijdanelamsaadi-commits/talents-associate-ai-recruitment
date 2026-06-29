from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


EVALUATION_DECISION_PATTERN = "^(preselectionne|non_selectionne|profil_valide|refus_candidat)$"


class EvaluationBase(BaseModel):
    interview_id: UUID
    candidate_id: UUID | None = None
    evaluator_name: str = Field(default="Recruteur", min_length=1, max_length=150)
    rating: int = Field(ge=1, le=5)
    technical_score: int = Field(ge=1, le=5)
    soft_skills_score: int = Field(ge=1, le=5)
    motivation_score: int = Field(ge=1, le=5)
    recommendation: str = Field(pattern=EVALUATION_DECISION_PATTERN)
    comments: str | None = None


class EvaluationCreate(EvaluationBase):
    pass


class EvaluationUpdate(BaseModel):
    interview_id: UUID | None = None
    candidate_id: UUID | None = None
    evaluator_name: str | None = Field(default=None, min_length=1, max_length=150)
    rating: int | None = Field(default=None, ge=1, le=5)
    technical_score: int | None = Field(default=None, ge=1, le=5)
    soft_skills_score: int | None = Field(default=None, ge=1, le=5)
    motivation_score: int | None = Field(default=None, ge=1, le=5)
    recommendation: str | None = Field(default=None, pattern=EVALUATION_DECISION_PATTERN)
    comments: str | None = None


class EvaluationRead(BaseModel):
    id: UUID
    interview_id: UUID
    application_id: UUID
    candidate_id: UUID
    evaluator_name: str
    rating: int
    technical_score: int
    soft_skills_score: int
    motivation_score: int
    global_score: float
    recommendation: str
    comments: str | None
    submitted_at: datetime | None
    created_at: datetime
    updated_at: datetime
